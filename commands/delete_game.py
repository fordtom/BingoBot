import discord
from db import get_db
from utils import check_channel


async def execute(interaction: discord.Interaction, game_id: int):
    """
    Delete a game and all associated data from the database.
    
    Args:
        interaction: The Discord interaction that triggered the command
        game_id: ID of the game to delete
    """
    # Check if command is used in the allowed channel
    if not await check_channel(interaction):
        return
        
    db = await get_db()
    
    # Check if the game exists
    async with db.db.execute("SELECT * FROM games WHERE game_id = ?", (game_id,)) as cursor:
        game = await cursor.fetchone()
    
    if not game:
        await interaction.response.send_message(f"Game with ID {game_id} not found.")
        return
    
    try:
        # Get game title for confirmation message
        game_title = game["title"]
        
        # Start a transaction
        await db.db.execute("BEGIN TRANSACTION")
        
        # Delete votes associated with events in this game
        await db.db.execute(
            "DELETE FROM votes WHERE game_id = ?", 
            (game_id,)
        )
        
        # Delete board squares associated with boards in this game
        await db.db.execute(
            """DELETE FROM board_squares 
               WHERE board_id IN (SELECT board_id FROM boards WHERE game_id = ?)""", 
            (game_id,)
        )
        
        # Delete boards in this game
        await db.db.execute("DELETE FROM boards WHERE game_id = ?", (game_id,))
        
        # Delete events in this game
        await db.db.execute("DELETE FROM events WHERE game_id = ?", (game_id,))
        
        # Delete the game itself
        await db.db.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
        
        # Commit the transaction
        await db.db.commit()
        
        await interaction.response.send_message(
            f"Game '{game_title}' (ID: {game_id}) has been deleted along with all associated data."
        )
        
    except Exception as e:
        # Rollback transaction on error
        await db.db.rollback()
        await interaction.response.send_message(f"Error deleting game: {str(e)}")
        return