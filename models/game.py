from dataclasses import dataclass
from typing import Optional


@dataclass
class Game:
    """
    Represents a Bingo game instance.
    
    Attributes:
        game_id: Unique identifier for the game
        title: Optional title or description for the game
        is_active: Boolean to indicate if this is the currently active game
        grid_size: Size of the grid (e.g., 4 for a 4x4 bingo board)
    """
    game_id: int
    title: Optional[str] = None
    is_active: bool = False
    grid_size: int = 4