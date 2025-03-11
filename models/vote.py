from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Vote:
    """
    Represents a player's vote on an event.
    
    Attributes:
        event_id: ID of the event being voted on
        user_id: Discord user ID of the player who cast the vote
        voted_at: Timestamp when the vote was cast
    """
    event_id: int
    user_id: int
    voted_at: datetime = datetime.now()