import discord
from db import get_db
from models.event import EventStatus
from utils import get_active_game, send_error_message, DEFAULT_GRID_SIZE, EMBED_COLOR_PRIMARY


async def execute(interaction: discord.Interaction):
    """
    Initialize a new empty bingo game.
    
    Args:
        interaction: The Discord interaction that triggered the command
    """
    # Defer response to give us time to process
    await interaction.response.defer(ephemeral=False)
    
    db = await get_db()
    
    try:
        # Create a new game with default values
        async with db.db.execute(
            "INSERT INTO games (title, grid_size) VALUES (?, ?)",
            (f"Game created by {interaction.user.display_name}", DEFAULT_GRID_SIZE)
        ) as cursor:
            new_game_id = cursor.lastrowid
        
        # Commit the changes
        await db.db.commit()
        
        # Create a response embed
        embed = discord.Embed(
            title="New Empty Bingo Game Created",
            description=(
                f"Game ID: {new_game_id}\n"
                f"Created by: {interaction.user.display_name}\n\n"
                "This game has no events or players yet. To populate it:\n"
                "• Add players with Discord mentions\n"
                "• Upload a CSV of events or create them manually"
            ),
            color=EMBED_COLOR_PRIMARY
        )
        
        # Set this as the active game if no active game exists
        active_game = await get_active_game()
        
        if not active_game:
            await db.db.execute("UPDATE games SET is_active = 1 WHERE game_id = ?", (new_game_id,))
            await db.db.commit()
            embed.add_field(name="Status", value="✅ Set as active game", inline=False)
        else:
            embed.add_field(
                name="Note", 
                value=f"Game ID {active_game['game_id']} is currently active. Use `/bingo set_active_game {new_game_id}` to switch.", 
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        # Rollback transaction on error
        await db.db.rollback()
        await send_error_message(interaction, f"Error creating game: {str(e)}")
        return