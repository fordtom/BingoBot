"""Command to set a game as the active game."""
import discord
from db import get_db
from bingo.utils.channel_check import require_allowed_channel


@require_allowed_channel
async def execute(interaction: discord.Interaction, game_id: int):
    """
    Set a game as the active game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        game_id: ID of the game to set as active
    """
        
    db = await get_db()
    
    # Check if the game exists
    async with db.db.execute("SELECT * FROM games WHERE game_id = ?", (game_id,)) as cursor:
        game = await cursor.fetchone()
    
    if not game:
        await interaction.response.send_message(f"Game with ID {game_id} not found.")
        return
    
    try:
        # First, unset any currently active game
        await db.db.execute("UPDATE games SET is_active = 0 WHERE is_active = 1")
        
        # Set the specified game as active
        await db.db.execute("UPDATE games SET is_active = 1 WHERE game_id = ?", (game_id,))
        
        # Commit the changes
        await db.db.commit()
        
        await interaction.response.send_message(f"Game '{game['title']}' (ID: {game_id}) is now the active game.")
        
    except Exception as e:
        # Rollback transaction on error
        await db.db.rollback()
        await interaction.response.send_message(f"Error setting active game: {str(e)}")
        return
