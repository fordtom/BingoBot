"""Event model for bingo games."""
from dataclasses import dataclass
from enum import Enum, auto


class EventStatus(Enum):
    """Status of a bingo event."""
    OPEN = auto()
    CLOSED = auto()


@dataclass
class Event:
    """
    Represents an event in a Bingo game.
    
    Attributes:
        event_id: Unique identifier for the event within a game
        game_id: ID of the game this event belongs to
        description: Description of the event
        status: Current status of the event (open or closed)
    """
    event_id: int
    game_id: int
    description: str
    status: EventStatus = EventStatus.OPEN
