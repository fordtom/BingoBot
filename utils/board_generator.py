import random
from typing import List, Dict, Any


async def generate_board(events: List[Dict[str, Any]], grid_size: int = 4) -> List[Dict[str, Any]]:
    """
    Randomly generate a bingo board layout from a list of events.
    
    Args:
        events: List of event dictionaries
        grid_size: Size of the grid (e.g., 4 for a 4x4 board)
        
    Returns:
        List of board square dictionaries with row, column, and event_id
        
    Raises:
        ValueError: If there aren't enough events to fill the board
    """
    num_squares = grid_size * grid_size
    
    if len(events) < num_squares:
        raise ValueError(f"Not enough events ({len(events)}) to fill a {grid_size}x{grid_size} board ({num_squares} needed)")
    
    # Randomly select events for the board
    selected_events = random.sample(events, num_squares)
    
    # Create board squares
    squares = []
    for i in range(grid_size):
        for j in range(grid_size):
            event_index = i * grid_size + j
            squares.append({
                'row': i,
                'column': j,
                'event_id': selected_events[event_index]['event_id']
            })
    
    return squares