import io
from PIL import Image, ImageDraw, ImageFont

async def generate_bingo_board_image(grid, grid_size, square_size=170):
    """Generate a bingo board image from grid data."""
    img_width = grid_size * square_size
    img_height = grid_size * square_size
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    font_size = 20
    square_font = ImageFont.load_default()
    potential_fonts = [
        "Arial", "arial",
        "Helvetica", "helvetica",
        "DejaVuSans", "DejaVuSans-Bold",
        "Verdana", "verdana",
        "FreeSans", "FreeSansBold",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Verdana.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for font_name in potential_fonts:
        try:
            temp_font = ImageFont.truetype(font_name, font_size)
            square_font = temp_font
            break
        except Exception:
            continue

    for row in range(grid_size):
        for col in range(grid_size):
            square = grid[row][col]
            x1 = col * square_size
            y1 = row * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size

            if square:
                color = "green" if square["status"] == "CLOSED" else "lightblue"
            else:
                color = "white"
            draw.rectangle([x1, y1, x2, y2], fill=color, outline="black", width=3)

            if square:
                description = square["description"]
                text_x = x1 + square_size // 2
                text_y = y1 + square_size // 2
                text_color = "white" if square["status"] == "CLOSED" else "black"

                words = description.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = " ".join(current_line + [word])
                    if len(test_line) <= 14:
                        current_line.append(word)
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(" ".join(current_line))
                if len(lines) > 6:
                    lines = lines[:5] + ["..."]

                line_height = 24
                start_y = text_y - ((len(lines) - 1) * line_height // 2)
                for i, line in enumerate(lines):
                    line_y = start_y + i * line_height
                    draw.text((text_x, line_y), line, fill=text_color, font=square_font, anchor="mm")

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

