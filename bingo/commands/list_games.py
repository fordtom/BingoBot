"""Command to list all bingo games with their details."""
import discord
import sqlite3
from typing import List, Tuple

from db import get_db
from bingo.utils.channel_check import require_allowed_channel
from bingo.utils.db_utils import get_active_game
from bingo.models.event import EventStatus


@require_allowed_channel
async def execute(interaction: discord.Interaction):
    """Execute the list_games command.
    
    Lists all games with their ID, title, and event statistics.
    
    Args:
        interaction: The Discord interaction object
    """
    # Defer the response since this might take a moment
    await interaction.response.defer(ephemeral=False)
    
    # Get the database connection
    db = await get_db()
    
    try:
        # Get the active game for highlighting
        active_game = await get_active_game(db)
        active_game_id = active_game['game_id'] if active_game else None
        
        # Fetch all games
        cursor = await db.db.execute(
            """
            SELECT g.game_id as id, g.title, g.grid_size, COUNT(DISTINCT e.event_id) as event_count
            FROM games g
            LEFT JOIN events e ON g.game_id = e.game_id
            GROUP BY g.game_id
            ORDER BY g.game_id DESC
            """
        )
        games = await cursor.fetchall()
        
        # For each game, get the count of closed events
        games_with_stats: List[Tuple[int, str, int, int, int]] = []
        for game in games:
            game_id, title, grid_size, event_count = game

            # Get count of closed events
            cursor = await db.db.execute(
                """
                SELECT COUNT(DISTINCT e.event_id) as closed_count
                FROM events e
                WHERE e.game_id = ? AND e.status = ?
                """,
                (game_id, EventStatus.CLOSED.name)
            )
            closed_result = await cursor.fetchone()
            closed_count = closed_result[0] if closed_result else 0
            
            # Get player count
            cursor = await db.db.execute(
                """
                SELECT COUNT(DISTINCT user_id) as player_count
                FROM boards
                WHERE game_id = ?
                """,
                (game_id,)
            )
            player_result = await cursor.fetchone()
            player_count = player_result[0] if player_result else 0
            
            games_with_stats.append((game_id, title, grid_size, closed_count, event_count, player_count))
        
        # Create an embed with the games
        if games_with_stats:
            embed = discord.Embed(
                title="Bingo Games",
                description="List of all bingo games",
                color=discord.Color.blue()
            )
            
            for game in games_with_stats:
                game_id, title, grid_size, closed_count, event_count, player_count = game
                
                # Mark the active game with a 🟢 emoji
                game_name = f"🟢 {title}" if game_id == active_game_id else title
                
                # Format: Game ID: Title (grid_size x grid_size)
                # Events: closed/total | Players: count
                value = (
                    f"**Grid Size:** {grid_size}×{grid_size}\n"
                    f"**Events:** {closed_count}/{event_count} closed\n"
                    f"**Players:** {player_count}"
                )
                
                embed.add_field(
                    name=f"Game #{game_id}: {game_name}",
                    value=value,
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("No games found.")
            
    except sqlite3.Error as e:
        await interaction.followup.send(f"Error retrieving games: {e}")

