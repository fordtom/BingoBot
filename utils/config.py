"""
Configuration settings for the BingoBot application.
"""

# Database settings
DATABASE_PATH = "bingobot.db"

# Game settings
DEFAULT_GRID_SIZE = 4
MAX_GRID_SIZE = 5
MIN_GRID_SIZE = 3

# Voting settings
VOTE_CONSENSUS_THRESHOLD = 0.6  # Percentage of players needed to mark an event as happened

# Discord UI settings
EMBED_COLOR_PRIMARY = 0x3498db  # Discord blue
EMBED_COLOR_SUCCESS = 0x2ecc71  # Green
EMBED_COLOR_WARNING = 0xf39c12  # Orange
EMBED_COLOR_ERROR = 0xe74c3c    # Red

# Board display settings
BOARD_SQUARE_EMPTY = "⬜"
BOARD_SQUARE_FILLED = "🟩"
BOARD_SQUARE_SEPARATOR = "│"
BOARD_ROW_SEPARATOR = "─"
BOARD_CORNER = "┼"