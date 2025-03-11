import discord
from db import get_db
from utils import (
    get_or_validate_game, 
    check_user_in_game, 
    send_error_message, 
    check_channel,
    EMBED_COLOR_PRIMARY,
    BOARD_SQUARE_EMPTY,
    BOARD_SQUARE_FILLED,
    BOARD_SQUARE_SEPARATOR,
    BOARD_ROW_SEPARATOR,
    BOARD_CORNER
)


async def execute(interaction: discord.Interaction, user: discord.Member, game_id: int = None):
    """
    Display a user's bingo board for a specified game or the active game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        user: The Discord user whose board to display
        game_id: ID of the game (optional, uses active game if not provided)
    """
    # Check if command is used in the allowed channel
    if not await check_channel(interaction):
        return
    
    # Defer response to give us time to process
    await interaction.response.defer(ephemeral=False)
    
    # Get active game or validate provided game_id
    game = await get_or_validate_game(interaction, game_id)
    if not game:
        return  # Error already handled by get_or_validate_game
    
    game_id = game["game_id"]
    db = await get_db()
    
    # Check if user has a board for this game
    if not await check_user_in_game(game_id, user.id):
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
    
    # Create embed for board display
    embed = discord.Embed(
        title=f"Bingo Board for {user.display_name}",
        description=f"Game: **{game['title']}** (ID: {game_id})",
        color=EMBED_COLOR_PRIMARY
    )
    
    # Create board visualization using emoji and markdown
    board_grid = []
    
    # Create a 2D grid to store events by position
    grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for square in squares:
        row = square["row"]
        col = square["column"]
        grid[row][col] = square
    
    # Generate the board display
    board_text = "```\n"
    
    # Add column headers
    board_text += "   "
    for col in range(grid_size):
        board_text += f" {col+1}  "
    board_text += "\n"
    
    # Add horizontal line
    board_text += "  +"
    for col in range(grid_size):
        board_text += "───+"
    board_text += "\n"
    
    # Add rows with data
    for row in range(grid_size):
        # Add row label
        board_text += f"{row+1} |"
        
        # Add cells
        for col in range(grid_size):
            square = grid[row][col]
            if square:
                # Determine marker based on status
                marker = "X" if square["status"] == "CLOSED" else " "
                board_text += f" {marker} |"
            else:
                board_text += "   |"
        
        board_text += "\n"
        
        # Add row separator unless it's the last row
        if row < grid_size - 1:
            board_text += "  +"
            for col in range(grid_size):
                board_text += "───+"
            board_text += "\n"
    
    # Add bottom border
    board_text += "  +"
    for col in range(grid_size):
        board_text += "───+"
    board_text += "\n```"
    
    embed.add_field(name="Board", value=board_text, inline=False)
    
    # Add events listing field
    events_text = ""
    for row in range(grid_size):
        for col in range(grid_size):
            square = grid[row][col]
            if square:
                status_marker = "✅" if square["status"] == "CLOSED" else "⬜"
                events_text += f"{status_marker} **({row+1},{col+1})** [Event {square['event_id']}]: {square['description']}\n"
    
    embed.add_field(name="Events", value=events_text, inline=False)
    
    # Add footer
    embed.set_footer(text=f"Board ID: {board['board_id']} • Grid Size: {grid_size}×{grid_size}")
    
    # Send the board display
    await interaction.followup.send(embed=embed)