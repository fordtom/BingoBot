"""
Utility functions for bingo database operations.
These functions help reduce duplicate code across command implementations.
"""

import discord
# Import get_db_handler inside each function to avoid circular imports

from bingo.utils.config import DEFAULT_GRID_SIZE


async def get_active_game(db=None):
    """Get the currently active game from the database.
    
    Args:
        db: Optional database handler. If not provided, a new handler will be obtained.
    
    Returns:
        dict: The active game record or None if no active game exists
    """
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()
        
    active_game = await db.fetchone("SELECT * FROM games WHERE is_active = 1")
    return active_game


async def get_game_by_id(game_id, db=None):
    """Get a game by its ID.
    
    Args:
        game_id: The ID of the game to retrieve
        db: Optional database handler. If not provided, a new handler will be obtained.
        
    Returns:
        dict: The game record or None if the game doesn't exist
    """
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()
        
    game = await db.fetchone("SELECT * FROM games WHERE game_id = ?", (game_id,))
    return game


async def get_or_validate_game(interaction, game_id=None, db=None):
    """Get the active game or validate a specific game ID.
    
    This function handles the common pattern of using either a specified game ID
    or falling back to the active game, with appropriate error messages.
    
    Args:
        interaction: Discord interaction object
        game_id: Optional ID of the game
        db: Optional database handler. If not provided, a new handler will be obtained.
        
    Returns:
        dict: The game record or None if no valid game exists
        
    Side effects:
        May send an error response to the interaction if no valid game exists
    """
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()
        
    # Check if game_id is provided
    if game_id is not None:
        # Validate the specified game exists
        game = await get_game_by_id(game_id, db)
        if not game:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Error: Game with ID {game_id} not found.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"Error: Game with ID {game_id} not found.",
                    ephemeral=True
                )
            return None
        return game
    
    # Use active game if no game_id provided
    active_game = await get_active_game(db)
    if not active_game:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Error: No active game found. Please specify a game ID or set an active game.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Error: No active game found. Please specify a game ID or set an active game.",
                ephemeral=True
            )
        return None
    
    return active_game


async def check_user_in_game(game_id, user_id, db=None):
    """Check if a user has a board in the specified game.
    
    Args:
        game_id: ID of the game
        user_id: Discord user ID
        db: Optional database handler. If not provided, a new handler will be obtained.
        
    Returns:
        bool: True if the user has a board in the game, False otherwise
    """
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()
        
    result = await db.fetchone(
        "SELECT 1 FROM boards WHERE game_id = ? AND user_id = ?",
        (game_id, user_id)
    )
    return result is not None


async def get_event_by_id(event_id, game_id, db=None):
    """Get an event by its ID and game ID.
    
    Args:
        event_id: The ID of the event
        game_id: The ID of the game the event belongs to
        db: Optional database handler. If not provided, a new handler will be obtained.
        
    Returns:
        dict: The event record or None if the event doesn't exist
    """
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()
        
    event = await db.fetchone(
        "SELECT * FROM events WHERE event_id = ? AND game_id = ?",
        (event_id, game_id)
    )
    return event


async def fetch_events_for_game(game_id, db=None):
    """Retrieve all events for a given game."""
    if db is None:
        from db import get_db_handler
        db = await get_db_handler()

    events = await db.fetchall(
        "SELECT * FROM events WHERE game_id = ? ORDER BY event_id",
        (game_id,),
    )
    return events


async def send_error_message(interaction, message):
    """Send a standardized error message.
    
    Args:
        interaction: Discord interaction object
        message: The error message to send
    """
    # Check if we need to use followup or direct response
    if interaction.response.is_done():
        await interaction.followup.send(
            embed=discord.Embed(
                title="Error",
                description=message,
                color=discord.Color.red()
            ),
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Error",
                description=message,
                color=discord.Color.red()
            ),
            ephemeral=True
        )


