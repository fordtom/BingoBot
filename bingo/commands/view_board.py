"""Command to display a user's bingo board."""
import discord
import io
from PIL import Image, ImageDraw, ImageFont

from db import get_db
from bingo.utils.channel_check import is_allowed_channel
from bingo.utils.db_utils import get_or_validate_game, check_user_in_game, send_error_message
from bingo.utils.config import (
    EMBED_COLOR_PRIMARY,
    BOARD_SQUARE_EMPTY,
    BOARD_SQUARE_FILLED
)


async def generate_bingo_board_image(grid, grid_size, square_size=170):
    """
    Generate a bingo board image from the grid data.
    
    Args:
        grid: 2D array containing board square data
        grid_size: Size of the grid (N for an NxN grid)
        square_size: Size of each square in pixels (default: 170)
        
    Returns:
        BytesIO object containing the PNG image
    """
    # Image dimensions (no padding/border)
    img_width = grid_size * square_size
    img_height = grid_size * square_size
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)
    
    # Font settings - try multiple fonts with proper size
    font_size = 20  # Further reduced font size for better fit
    
    # Start with default font in case none of the others work
    square_font = ImageFont.load_default()
    
    # List of fonts to try - common fonts across different operating systems
    potential_fonts = [
        # System fonts
        "Arial", "arial",
        "Helvetica", "helvetica",
        "DejaVuSans", "DejaVuSans-Bold",
        "Verdana", "verdana",
        "FreeSans", "FreeSansBold",
        
        # Full paths for common locations
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Verdana.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    
    # Try each font in the list
    for font_name in potential_fonts:
        try:
            # Try to load the font and break the loop if successful
            temp_font = ImageFont.truetype(font_name, font_size)
            square_font = temp_font
            print(f"Successfully loaded font: {font_name} at size {font_size}")
            break
        except Exception as e:
            # If this font fails, continue to the next one
            continue
    
    # Draw grid
    for row in range(grid_size):
        for col in range(grid_size):
            square = grid[row][col]
            x1 = col * square_size
            y1 = row * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size
            
            # Square background color
            if square:
                color = "green" if square["status"] == "CLOSED" else "lightblue"
            else:
                color = "white"
            
            # Draw rectangle with thicker border
            draw.rectangle([x1, y1, x2, y2], fill=color, outline="black", width=3)
            
            # Add event description if square exists
            if square:
                # Get description text
                description = square["description"]
                
                # Calculate center of square
                text_x = x1 + square_size // 2
                text_y = y1 + square_size // 2
                
                # Draw text with contrasting color
                text_color = "white" if square["status"] == "CLOSED" else "black"
                
                # Draw text with word wrapping for better fit
                words = description.split()
                lines = []
                current_line = []
                
                # Simple word wrapping algorithm - adjust for font size
                for word in words:
                    test_line = " ".join(current_line + [word])
                    if len(test_line) <= 14:  # Reduced to create more margin around text
                        current_line.append(word)
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(" ".join(current_line))
                
                # Limit to 6 lines max to fit the text
                if len(lines) > 6:
                    lines = lines[:5] + ["..."]
                
                # Draw each line with appropriate spacing
                line_height = 24  # Reduced line spacing
                start_y = text_y - ((len(lines) - 1) * line_height // 2)
                
                for i, line in enumerate(lines):
                    line_y = start_y + i * line_height
                    draw.text((text_x, line_y), line, fill=text_color, font=square_font, anchor="mm")
    
    # Convert image to bytes for Discord attachment
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return img_bytes


async def execute(interaction: discord.Interaction, user: discord.Member, game_id: int = None):
    """
    Display a user's bingo board for a specified game or the active game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        user: The Discord user whose board to display
        game_id: ID of the game (optional, uses active game if not provided)
    """
    # Check if command is used in the allowed channel
    if not await is_allowed_channel(interaction):
        return
    
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