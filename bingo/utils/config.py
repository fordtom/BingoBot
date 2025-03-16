"""
Configuration constants for the Bingo bot.
"""

import os
from pathlib import Path

# Database path - use absolute path for more reliable operation
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "bingobot.db")

# Grid size settings
MIN_GRID_SIZE = 2
DEFAULT_GRID_SIZE = 4
MAX_GRID_SIZE = 10

# Voting settings
VOTE_CONSENSUS_THRESHOLD = 0.75  # 75% of players need to vote for an event

# Discord embed colors
EMBED_COLOR_PRIMARY = 0x3498db   # Blue
EMBED_COLOR_SUCCESS = 0x2ecc71   # Green  
EMBED_COLOR_ERROR = 0xe74c3c     # Red
EMBED_COLOR_WARNING = 0xf39c12   # Orange

# Board display characters
BOARD_SQUARE_EMPTY = "⬜"
BOARD_SQUARE_FILLED = "🟩"
BOARD_SQUARE_SEPARATOR = "│"
BOARD_ROW_SEPARATOR = "─"
BOARD_CORNER = "+"