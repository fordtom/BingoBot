"""Command to display a user's bingo board."""
import discord
from bingo.utils.board_image import generate_bingo_board_image

from db import get_db
from bingo.utils.channel_check import require_allowed_channel
from bingo.utils.db_utils import get_or_validate_game, check_user_in_game, send_error_message
from bingo.utils.config import EMBED_COLOR_PRIMARY

@require_allowed_channel
async def execute(interaction: discord.Interaction, user: discord.Member, game_id: int = None):
    """
    Display a user's bingo board for a specified game or the active game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        user: The Discord user whose board to display
        game_id: ID of the game (optional, uses active game if not provided)
    """
    
    # Defer response to give us time to process
    await interaction.response.defer(ephemeral=False)
    
    db = await get_db()
    
    # Get active game or validate provided game_id
    game = await get_or_validate_game(interaction, game_id, db)
    if not game:
        return  # Error already handled by get_or_validate_game
    
    game_id = game["game_id"]
    
    # Check if user has a board for this game
    if not await check_user_in_game(game_id, user.id, db):
        await send_error_message(
            interaction, 
            f"{user.display_name} does not have a board for this game."
        )
        return
    
    # Get board info
    async with db.db.execute(
        "SELECT * FROM boards WHERE game_id = ? AND user_id = ?", 
        (game_id, user.id)
    ) as cursor:
        board = await cursor.fetchone()
    
    # Get the board squares
    async with db.db.execute(
        """
        SELECT bs.row, bs.column, bs.event_id, e.description, e.status 
        FROM board_squares bs
        JOIN events e ON bs.event_id = e.event_id AND e.game_id = ?
        WHERE bs.board_id = ?
        ORDER BY bs.row, bs.column
        """, 
        (game_id, board["board_id"])
    ) as cursor:
        squares = await cursor.fetchall()
    
    if not squares:
        await send_error_message(
            interaction, 
            f"{user.display_name}'s board exists but has no squares. This may be an error."
        )
        return
    
    # Get the grid size (should be stored in the board record)
    grid_size = board["grid_size"]
    
    # Create a 2D grid to store events by position
    grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for square in squares:
        row = square["row"]
        col = square["column"]
        grid[row][col] = square
    
    # Create embed for board display
    embed = discord.Embed(
        title=f"Bingo Board for {user.display_name}",
        description=f"Game: **{game['title']}** (ID: {game_id})",
        color=EMBED_COLOR_PRIMARY
    )
    
    # Generate the board image
    board_image = await generate_bingo_board_image(grid, grid_size)
    
    # Add footer with basic info
    embed.set_footer(text=f"Board ID: {board['board_id']} • Grid Size: {grid_size}×{grid_size}")
    
    # Create file attachment from the generated image
    file = discord.File(fp=board_image, filename="bingo_board.png")
    
    # Send the embed and file in the same message, but not embedded
    await interaction.followup.send(embed=embed, file=file)
