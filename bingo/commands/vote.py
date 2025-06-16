"""Command to vote that an event has occurred."""
import discord
import math
import logging
from db import get_db_handler
from bingo.utils.channel_check import require_allowed_channel

from bingo.models.event import EventStatus
from bingo.utils.db_utils import (
    get_or_validate_game,
    check_user_in_game,
    send_error_message,
)
from bingo.utils.config import VOTE_CONSENSUS_THRESHOLD
from bingo.utils.win_checker import check_for_winners, announce_winners

logger = logging.getLogger(__name__)


@require_allowed_channel
async def execute(interaction: discord.Interaction, event_id: int, game_id: int = None):
    """
    Vote that an event has occurred.
    
    Args:
        interaction: The Discord interaction that triggered the command
        event_id: ID of the event to vote for (this is the event number within the game, not a global ID)
        game_id: ID of the game (optional, uses active game if not provided)
    """
    
    try:
        db = await get_db_handler()
        
        # Get the game (active game if game_id is None)
        game = await get_or_validate_game(interaction, game_id, db)
        if not game:
            return  # Error message already sent by get_or_validate_game
        
        game_id = game["game_id"]
        
        # Check if the user is a player in this game
        if not await check_user_in_game(game_id, interaction.user.id, db):
            await send_error_message(interaction, "You are not a player in this game.")
            return
        
        # Get the event
        event = await db.fetchone(
            "SELECT * FROM events WHERE game_id = ? AND event_id = ?", 
            (game_id, event_id)
        )
        
        if not event:
            await send_error_message(
                interaction, f"Event {event_id} not found in game {game_id}."
            )
            return
        
        # Check if the event is already closed
        if event["status"] == EventStatus.CLOSED.name:
            await send_error_message(
                interaction,
                f"Event {event_id} ({event['description']}) is already closed.",
            )
            return
        
        # Check if the user has already voted for this event
        existing_vote = await db.fetchone(
            "SELECT * FROM votes WHERE event_id = ? AND game_id = ? AND user_id = ?", 
            (event_id, game_id, interaction.user.id)
        )
        
        if existing_vote:
            await send_error_message(interaction, "You have already voted for this event.")
            return
        
        # Add the vote
        await db.execute_and_commit(
            "INSERT INTO votes (event_id, game_id, user_id) VALUES (?, ?, ?)",
            (event_id, game_id, interaction.user.id)
        )
        
        # Count the total number of players in the game
        player_count_row = await db.fetchone(
            "SELECT COUNT(*) as player_count FROM boards WHERE game_id = ?", 
            (game_id,)
        )
        player_count = player_count_row["player_count"]
        
        # Count votes for this event
        vote_count_row = await db.fetchone(
            "SELECT COUNT(*) as vote_count FROM votes WHERE event_id = ? AND game_id = ?", 
            (event_id, game_id)
        )
        vote_count = vote_count_row["vote_count"]
        
        # Calculate consensus threshold - for small games, require all players
        # For larger games, use the percentage from config
        if player_count <= 3:
            consensus_threshold = player_count  # Everyone must agree for small games
        else:
            consensus_threshold = max(2, math.ceil(player_count * VOTE_CONSENSUS_THRESHOLD))
        
        # Check if consensus is reached
        if vote_count >= consensus_threshold:
            # Mark the event as closed
            await db.execute_and_commit(
                "UPDATE events SET status = ? WHERE game_id = ? AND event_id = ?",
                (EventStatus.CLOSED.name, game_id, event_id)
            )
            
            await interaction.response.send_message(
                f"You voted for event {event_id} ({event['description']}). "
                f"Consensus reached ({vote_count}/{player_count} votes)! Event is now closed."
            )
            
            # Check for winners now that the event is closed
            winners = await check_for_winners(db, game_id, game["grid_size"])
            if winners:
                await announce_winners(interaction.channel, winners, game["title"], interaction.client)
        else:
            await interaction.response.send_message(
                f"You voted for event {event_id} ({event['description']}). "
                f"Current votes: {vote_count}/{consensus_threshold} needed for consensus."
            )
        
    except Exception as e:
        logger.error(f"Vote command error: {type(e).__name__}: {str(e)}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your vote.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred while processing your vote.", ephemeral=True)
        except Exception as response_error:
            logger.error(f"Failed to send error message: {type(response_error).__name__}: {str(response_error)}")
        raise

