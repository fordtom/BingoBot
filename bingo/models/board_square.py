"""BoardSquare model for bingo games."""
from dataclasses import dataclass


@dataclass
class BoardSquare:
    """
    Represents a square on a player's Bingo board.
    
    Attributes:
        board_id: ID of the board this square belongs to
        row: Row index (0-based)
        column: Column index (0-based)
        event_id: ID of the event assigned to this square
    """
    board_id: int
    row: int
    column: int
    event_id: int
