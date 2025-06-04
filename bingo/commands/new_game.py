"""Command to create a new bingo game."""
import discord
from db import get_db
from bingo.utils.channel_check import require_allowed_channel

from bingo.models.event import EventStatus
from bingo.utils.csv_parser import parse_events_csv
from bingo.utils.board_generator import generate_board
from bingo.utils.db_utils import fetch_events_for_game, send_error_message


async def insert_game(db, title: str, grid_size: int) -> int:
    """Insert a new game and return its ID."""
    async with db.db.execute(
        "INSERT INTO games (title, grid_size) VALUES (?, ?)",
        (title, grid_size),
    ) as cursor:
        return cursor.lastrowid


async def insert_events(db, game_id: int, events: list[dict]):
    """Insert parsed events for a game."""
    for i, event in enumerate(events):
        await db.db.execute(
            "INSERT INTO events (event_id, game_id, description, status) VALUES (?, ?, ?, ?)",
            (i + 1, game_id, event["description"], EventStatus.OPEN.name),
        )


async def create_player_boards(db, game_id: int, player_ids: list[int], grid_size: int):
    """Create boards for each player and populate squares."""
    for player_id in player_ids:
        async with db.db.execute(
            "INSERT INTO boards (game_id, user_id, grid_size) VALUES (?, ?, ?)",
            (game_id, player_id, grid_size),
        ) as cursor:
            board_id = cursor.lastrowid

        all_events = await fetch_events_for_game(game_id, db)
        events_list = [{"event_id": e["event_id"]} for e in all_events]
        board_squares = await generate_board(events_list, grid_size)

        for square in board_squares:
            await db.db.execute(
                "INSERT INTO board_squares (board_id, row, column, event_id) VALUES (?, ?, ?, ?)",
                (board_id, square["row"], square["column"], square["event_id"]),
            )


async def build_response_embed(interaction, new_game_id: int, title: str, grid_size: int, events_count: int, player_ids: list[int], db) -> discord.Embed:
    """Create a response embed summarizing the new game."""
    player_names = []
    for pid in player_ids:
        player = interaction.guild.get_member(pid)
        if not player and interaction.guild:
            try:
                player = await interaction.guild.fetch_member(pid)
            except discord.errors.NotFound:
                player = None

        player_names.append(f"{player.display_name} ({player.mention})" if player else f"Unknown User ({pid})")

    embed = discord.Embed(
        title=f"New Bingo Game Created: {title}",
        description=f"Game ID: {new_game_id}\nGrid Size: {grid_size}x{grid_size}\nEvents: {events_count}",
        color=discord.Color.green(),
    )
    embed.add_field(name="Players", value="\n".join(f"• {n}" for n in player_names), inline=False)
    return embed


@require_allowed_channel
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
        
    if grid_size < 2 or grid_size > 10:
        await send_error_message(interaction, "Grid size must be between 2 and 10.")
        return
    
    if not player_ids:
        await send_error_message(
            interaction,
            "No players specified. Use mentions to tag players (e.g., @player1 @player2).",
        )
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
                await send_error_message(interaction, "No valid events found in the CSV file.")
                return
            
            # Make sure we have enough events for all boards
            required_events = grid_size * grid_size
            if len(events_data) < required_events:
                await send_error_message(
                    interaction,
                    f"Not enough events in the CSV. Need at least {required_events} "
                    f"for a {grid_size}x{grid_size} board, but only found {len(events_data)}.",
                )
                return
            
        except Exception as e:
            await send_error_message(interaction, f"Error parsing CSV: {str(e)}")
            return
    else:
        await send_error_message(
            interaction,
            "No events CSV provided. Please provide a CSV file with event descriptions.",
        )
        return
    
    db = await get_db()

    try:
        new_game_id = await insert_game(db, title, grid_size)
        await insert_events(db, new_game_id, events_data)
        await create_player_boards(db, new_game_id, player_ids, grid_size)

        await db.db.commit()

        embed = await build_response_embed(
            interaction,
            new_game_id,
            title,
            grid_size,
            len(events_data),
            player_ids,
            db,
        )

        async with db.db.execute("SELECT game_id FROM games WHERE is_active = 1") as cursor:
            active_game = await cursor.fetchone()

        if not active_game:
            await db.db.execute("UPDATE games SET is_active = 1 WHERE game_id = ?", (new_game_id,))
            await db.db.commit()
            embed.add_field(name="Status", value="Set as active game", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await db.db.rollback()
        await send_error_message(interaction, f"Error creating game: {str(e)}")
        return


