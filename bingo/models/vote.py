"""Vote model for bingo game events."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Vote:
    """
    Represents a player's vote on an event.
    
    Attributes:
        event_id: ID of the event being voted on
        game_id: ID of the game the event belongs to
        user_id: Discord user ID of the player who cast the vote
        voted_at: Timestamp when the vote was cast
    """
    event_id: int
    game_id: int
    user_id: int
    voted_at: datetime = datetime.now()
