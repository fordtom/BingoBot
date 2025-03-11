import discord
from db import get_db
from models.event import EventStatus
from utils import parse_events_csv, generate_board, check_channel


async def execute(interaction: discord.Interaction, title: str, grid_size: int, 
                 player_ids: list[int], events_csv: discord.Attachment = None):
    """
    Create a new bingo game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        title: Title or description of the game
        grid_size: Size of the grid
        player_ids: List of player Discord IDs
        events_csv: Optional CSV file containing event descriptions
    """
    # Check if command is used in the allowed channel
    if not await check_channel(interaction):
        return
        
    if grid_size < 2 or grid_size > 10:
        await interaction.response.send_message("Grid size must be between 2 and 10.")
        return
    
    if not player_ids:
        await interaction.response.send_message("No players specified. Use mentions to tag players (e.g., @player1 @player2).")
        return
    
    # We need events from CSV or somewhere else
    events_data = []
    
    # Respond immediately due to Discord interaction timeout
    await interaction.response.defer(thinking=True)
    
    # Parse events from CSV if provided
    if events_csv:
        try:
            # Download and read the CSV file
            csv_content = await events_csv.read()
            csv_text = csv_content.decode('utf-8')
            
            # Parse events
            events_data = await parse_events_csv(csv_text)
            
            if not events_data:
                await interaction.followup.send("No valid events found in the CSV file.")
                return
            
            # Make sure we have enough events for all boards
            required_events = grid_size * grid_size
            if len(events_data) < required_events:
                await interaction.followup.send(
                    f"Not enough events in the CSV. Need at least {required_events} "
                    f"for a {grid_size}x{grid_size} board, but only found {len(events_data)}."
                )
                return
            
        except Exception as e:
            await interaction.followup.send(f"Error parsing CSV: {str(e)}")
            return
    else:
        await interaction.followup.send("No events CSV provided. Please provide a CSV file with event descriptions.")
        return
    
    db = await get_db()
    
    try:
        # Create a new game
        async with db.db.execute(
            "INSERT INTO games (title, grid_size) VALUES (?, ?)",
            (title, grid_size)
        ) as cursor:
            # Get the new game ID
            new_game_id = cursor.lastrowid
        
        # Insert events
        for i, event_data in enumerate(events_data):
            await db.db.execute(
                "INSERT INTO events (event_id, game_id, description, status) VALUES (?, ?, ?, ?)",
                (i + 1, new_game_id, event_data['description'], EventStatus.OPEN.name)
            )
        
        # Create boards for each player
        for player_id in player_ids:
            # Insert board
            async with db.db.execute(
                "INSERT INTO boards (game_id, user_id, grid_size) VALUES (?, ?, ?)",
                (new_game_id, player_id, grid_size)
            ) as cursor:
                board_id = cursor.lastrowid
            
            # Get all events for this game
            async with db.db.execute(
                "SELECT event_id FROM events WHERE game_id = ?", 
                (new_game_id,)
            ) as cursor:
                all_events = await cursor.fetchall()
            
            # Convert to list of dicts for the generator
            events_list = [{"event_id": e["event_id"]} for e in all_events]
            
            # Generate board layout
            try:
                board_squares = await generate_board(events_list, grid_size)
                
                # Insert board squares
                for square in board_squares:
                    await db.db.execute(
                        "INSERT INTO board_squares (board_id, row, column, event_id) VALUES (?, ?, ?, ?)",
                        (board_id, square["row"], square["column"], square["event_id"])
                    )
            except Exception as e:
                await interaction.followup.send(f"Error generating board: {str(e)}")
                return
        
        # Commit all changes
        await db.db.commit()
        
        # Get player usernames
        player_names = []
        for player_id in player_ids:
            # Try to fetch the member directly
            player = interaction.guild.get_member(player_id)
            
            # If direct fetch failed, try fetching from the guild members
            if not player and interaction.guild:
                try:
                    # Use the bot's view of the guild to find the member
                    player = await interaction.guild.fetch_member(player_id)
                except discord.errors.NotFound:
                    player = None
            
            # Add the player name or a placeholder
            if player:
                player_names.append(f"{player.display_name} ({player.mention})")
            else:
                player_names.append(f"Unknown User ({player_id})")
        
        # Create a response embed
        embed = discord.Embed(
            title=f"New Bingo Game Created: {title}",
            description=f"Game ID: {new_game_id}\nGrid Size: {grid_size}x{grid_size}\nEvents: {len(events_data)}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Players", value="\n".join([f"• {name}" for name in player_names]), inline=False)
        
        # Set this as the active game if no active game exists
        async with db.db.execute("SELECT game_id FROM games WHERE is_active = 1") as cursor:
            active_game = await cursor.fetchone()
        
        if not active_game:
            await db.db.execute("UPDATE games SET is_active = 1 WHERE game_id = ?", (new_game_id,))
            await db.db.commit()
            embed.add_field(name="Status", value="Set as active game", inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        # Rollback transaction on error
        await db.db.rollback()
        await interaction.followup.send(f"Error creating game: {str(e)}")
        return