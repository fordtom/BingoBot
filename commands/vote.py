import discord
from db import get_db
from models.event import EventStatus
from utils import check_channel


async def execute(interaction: discord.Interaction, event_id: int, game_id: int = None):
    """
    Vote that an event has occurred.
    
    Args:
        interaction: The Discord interaction that triggered the command
        event_id: ID of the event to vote for
        game_id: ID of the game (optional, uses active game if not provided)
    """
    # Check if command is used in the allowed channel
    if not await check_channel(interaction):
        return
        
    db = await get_db()
    
    # If game_id not provided, get the active game
    if game_id is None:
        async with db.db.execute("SELECT game_id FROM games WHERE is_active = 1") as cursor:
            active_game = await cursor.fetchone()
            
        if not active_game:
            await interaction.response.send_message("No active game found. Use `/bingo set_active_game` to set an active game.")
            return
            
        game_id = active_game["game_id"]
    
    # Get game info
    async with db.db.execute("SELECT * FROM games WHERE game_id = ?", (game_id,)) as cursor:
        game = await cursor.fetchone()
        
    if not game:
        await interaction.response.send_message(f"Game with ID {game_id} not found.")
        return
    
    # Check if the user is a player in this game
    async with db.db.execute(
        "SELECT * FROM boards WHERE game_id = ? AND user_id = ?", 
        (game_id, interaction.user.id)
    ) as cursor:
        player_board = await cursor.fetchone()
    
    if not player_board:
        await interaction.response.send_message("You are not a player in this game.")
        return
    
    # Get the event
    async with db.db.execute(
        "SELECT * FROM events WHERE game_id = ? AND event_id = ?", 
        (game_id, event_id)
    ) as cursor:
        event = await cursor.fetchone()
    
    if not event:
        await interaction.response.send_message(f"Event {event_id} not found in game {game_id}.")
        return
    
    # Check if the event is already closed
    if event["status"] == EventStatus.CLOSED.name:
        await interaction.response.send_message(f"Event {event_id} ({event['description']}) is already closed.")
        return
    
    # Check if the user has already voted for this event
    async with db.db.execute(
        "SELECT * FROM votes WHERE event_id = ? AND game_id = ? AND user_id = ?", 
        (event_id, game_id, interaction.user.id)
    ) as cursor:
        existing_vote = await cursor.fetchone()
    
    if existing_vote:
        await interaction.response.send_message("You have already voted for this event.")
        return
    
    # Add the vote
    await db.db.execute(
        "INSERT INTO votes (event_id, game_id, user_id) VALUES (?, ?, ?)",
        (event_id, game_id, interaction.user.id)
    )
    await db.db.commit()
    
    # Count the total number of players in the game
    async with db.db.execute(
        "SELECT COUNT(*) as player_count FROM boards WHERE game_id = ?", 
        (game_id,)
    ) as cursor:
        player_count_row = await cursor.fetchone()
        player_count = player_count_row["player_count"]
    
    # Count votes for this event
    async with db.db.execute(
        "SELECT COUNT(*) as vote_count FROM votes WHERE event_id = ? AND game_id = ?", 
        (event_id, game_id)
    ) as cursor:
        vote_count_row = await cursor.fetchone()
        vote_count = vote_count_row["vote_count"]
    
    # Calculate consensus - typically 4 out of 5 (80%), but we'll generalize
    consensus_threshold = max(4, int(player_count * 0.8))
    
    # Check if consensus is reached
    if vote_count >= consensus_threshold:
        # Mark the event as closed
        await db.db.execute(
            "UPDATE events SET status = ? WHERE game_id = ? AND event_id = ?",
            (EventStatus.CLOSED.name, game_id, event_id)
        )
        await db.db.commit()
        
        await interaction.response.send_message(
            f"You voted for event {event_id} ({event['description']}). "
            f"Consensus reached ({vote_count}/{player_count} votes)! Event is now closed."
        )
    else:
        await interaction.response.send_message(
            f"You voted for event {event_id} ({event['description']}). "
            f"Current votes: {vote_count}/{consensus_threshold} needed for consensus."
        )