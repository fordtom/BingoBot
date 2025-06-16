"""Command to vote that an event has occurred."""
import discord
import math
import logging
from db import get_db
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
    
    logger.info(f"VOTE: Starting vote command - user_id={interaction.user.id}, event_id={event_id}, game_id={game_id}")
    
    try:
        logger.info("VOTE: Getting database connection")
        db = await get_db()
        logger.info("VOTE: Database connection obtained")
        
        # Get the game (active game if game_id is None)
        logger.info("VOTE: Getting/validating game")
        game = await get_or_validate_game(interaction, game_id, db)
        if not game:
            logger.info("VOTE: Game validation failed, returning")
            return  # Error message already sent by get_or_validate_game
        
        logger.info(f"VOTE: Game validated - game_id={game['game_id']}")
        game_id = game["game_id"]
        
        # Check if the user is a player in this game
        logger.info("VOTE: Checking if user is in game")
        if not await check_user_in_game(game_id, interaction.user.id, db):
            logger.info("VOTE: User not in game, sending error")
            await send_error_message(interaction, "You are not a player in this game.")
            return
        
        logger.info("VOTE: User is in game, proceeding")
        
        # Get the event
        logger.info(f"VOTE: Getting event - game_id={game_id}, event_id={event_id}")
        async with db.db.execute(
            "SELECT * FROM events WHERE game_id = ? AND event_id = ?", 
            (game_id, event_id)
        ) as cursor:
            event = await cursor.fetchone()
        
        if not event:
            logger.info("VOTE: Event not found, sending error")
            await send_error_message(
                interaction, f"Event {event_id} not found in game {game_id}."
            )
            return
        
        logger.info(f"VOTE: Event found - status={event['status']}, description={event['description']}")
        
        # Check if the event is already closed
        if event["status"] == EventStatus.CLOSED.name:
            logger.info("VOTE: Event already closed, sending error")
            await send_error_message(
                interaction,
                f"Event {event_id} ({event['description']}) is already closed.",
            )
            return
        
        # Check if the user has already voted for this event
        logger.info("VOTE: Checking for existing vote")
        async with db.db.execute(
            "SELECT * FROM votes WHERE event_id = ? AND game_id = ? AND user_id = ?", 
            (event_id, game_id, interaction.user.id)
        ) as cursor:
            existing_vote = await cursor.fetchone()
        
        if existing_vote:
            logger.info("VOTE: User already voted, sending error")
            await send_error_message(interaction, "You have already voted for this event.")
            return
        
        logger.info("VOTE: No existing vote found, proceeding to add vote")
        
        # Add the vote
        logger.info("VOTE: Inserting vote into database")
        await db.db.execute(
            "INSERT INTO votes (event_id, game_id, user_id) VALUES (?, ?, ?)",
            (event_id, game_id, interaction.user.id)
        )
        await db.db.commit()
        logger.info("VOTE: Vote inserted and committed")
        
        # Count the total number of players in the game
        logger.info("VOTE: Counting players in game")
        async with db.db.execute(
            "SELECT COUNT(*) as player_count FROM boards WHERE game_id = ?", 
            (game_id,)
        ) as cursor:
            player_count_row = await cursor.fetchone()
            player_count = player_count_row["player_count"]
        
        logger.info(f"VOTE: Player count = {player_count}")
        
        # Count votes for this event
        logger.info("VOTE: Counting votes for event")
        async with db.db.execute(
            "SELECT COUNT(*) as vote_count FROM votes WHERE event_id = ? AND game_id = ?", 
            (event_id, game_id)
        ) as cursor:
            vote_count_row = await cursor.fetchone()
            vote_count = vote_count_row["vote_count"]
        
        logger.info(f"VOTE: Vote count = {vote_count}")
        
        # Calculate consensus threshold - for small games, require all players
        # For larger games, use the percentage from config
        if player_count <= 3:
            consensus_threshold = player_count  # Everyone must agree for small games
        else:
            consensus_threshold = max(2, math.ceil(player_count * VOTE_CONSENSUS_THRESHOLD))
        
        logger.info(f"VOTE: Consensus threshold = {consensus_threshold}")
        
        # Check if consensus is reached
        if vote_count >= consensus_threshold:
            logger.info("VOTE: Consensus reached, closing event")
            # Mark the event as closed
            await db.db.execute(
                "UPDATE events SET status = ? WHERE game_id = ? AND event_id = ?",
                (EventStatus.CLOSED.name, game_id, event_id)
            )
            await db.db.commit()
            logger.info("VOTE: Event status updated to closed")
            
            logger.info("VOTE: Sending consensus reached message")
            await interaction.response.send_message(
                f"You voted for event {event_id} ({event['description']}). "
                f"Consensus reached ({vote_count}/{player_count} votes)! Event is now closed."
            )
            logger.info("VOTE: Consensus message sent")
            
            # Check for winners now that the event is closed
            logger.info("VOTE: Checking for winners")
            winners = await check_for_winners(db, game_id, game["grid_size"])
            logger.info(f"VOTE: Winners check complete - found {len(winners) if winners else 0} winners")
            
            if winners:
                logger.info("VOTE: Announcing winners")
                await announce_winners(interaction.channel, winners, game["title"], interaction.client)
                logger.info("VOTE: Winners announced")
        else:
            logger.info("VOTE: Consensus not reached, sending progress message")
            await interaction.response.send_message(
                f"You voted for event {event_id} ({event['description']}). "
                f"Current votes: {vote_count}/{consensus_threshold} needed for consensus."
            )
            logger.info("VOTE: Progress message sent")
        
        logger.info("VOTE: Command completed successfully")
        
    except Exception as e:
        logger.error(f"VOTE: Exception occurred - {type(e).__name__}: {str(e)}", exc_info=True)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your vote.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred while processing your vote.", ephemeral=True)
        except Exception as response_error:
            logger.error(f"VOTE: Failed to send error message - {type(response_error).__name__}: {str(response_error)}")
        raise

