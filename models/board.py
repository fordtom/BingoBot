from dataclasses import dataclass
from typing import Optional


@dataclass
class Board:
    """
    Represents a player's Bingo board.
    
    Attributes:
        board_id: Unique identifier for the board
        game_id: ID of the game this board belongs to
        user_id: Discord user ID of the player who owns this board
        grid_size: Size of the grid (e.g., 4 for a 4x4 board)
    """
    board_id: int
    game_id: int
    user_id: int
    grid_size: int = 4