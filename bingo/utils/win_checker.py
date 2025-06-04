"""Utility functions for checking bingo win conditions."""
import discord
from typing import List, Dict, Any

from db import get_db
from bingo.models.event import EventStatus


async def check_for_winners(db, game_id: int, grid_size: int) -> List[int]:
    """
    Check if any player has all events on their board marked as closed.
    
    Args:
        db: Database connection
        game_id: ID of the game to check
        grid_size: Size of the game grid
        
    Returns:
        A list of winners (user IDs), or an empty list if no winners yet
    """
    # Get all boards for this game
    async with db.db.execute(
        "SELECT board_id, user_id FROM boards WHERE game_id = ?", 
        (game_id,)
    ) as cursor:
        boards = await cursor.fetchall()
    
    winners = []
    
    # For each board, check if all squares are closed
    for board in boards:
        board_id = board["board_id"]
        user_id = board["user_id"]
        
        # Count total squares on the board
        total_squares = grid_size * grid_size
        
        # Count closed squares
        async with db.db.execute(
            """
            SELECT COUNT(*) as closed_count
            FROM board_squares bs
            JOIN events e ON bs.event_id = e.event_id AND e.game_id = ?
            WHERE bs.board_id = ? AND e.status = ?
            """, 
            (game_id, board_id, EventStatus.CLOSED.name)
        ) as cursor:
            count_row = await cursor.fetchone()
            closed_count = count_row["closed_count"]
        
        # If all squares are closed, add user to winners
        if closed_count == total_squares:
            winners.append(user_id)
    
    return winners


async def announce_winners(channel, winners: List[int], game_title: str, bot: discord.Client):
    """
    Announce the winners of a bingo game.
    
    Args:
        channel: Discord channel to send the announcement to
        winners: List of user IDs who have won
        game_title: Title of the game
        bot: The Discord bot client used to fetch user information
    """
    if not winners:
        return
    
    # Fetch user objects for all winners
    winner_users = []
    for user_id in winners:
        user = None
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            # Fallback if user can't be fetched
            user = f"User ID: {user_id}"
        
        if user:
            winner_users.append(user)
    
    # Create an embed to announce the winners
    embed = discord.Embed(
        title="🎉 BINGO! 🎉",
        description=f"We have {'a winner' if len(winners) == 1 else 'winners'} for game **{game_title}**!",
        color=discord.Color.gold()
    )
    
    if len(winner_users) == 1:
        user = winner_users[0]
        mention = user.mention if isinstance(user, discord.User) else user
        embed.add_field(
            name="Winner",
            value=f"Congratulations to {mention}!",
            inline=False
        )
    else:
        mentions = []
        for user in winner_users:
            mention = user.mention if isinstance(user, discord.User) else user
            mentions.append(mention)
            
        embed.add_field(
            name="Winners",
            value="Congratulations to:\n" + "\n".join(mentions),
            inline=False
        )
    
    # Send the announcement
    await channel.send(embed=embed)