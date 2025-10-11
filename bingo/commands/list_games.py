"""Command to list all bingo games with their details."""

import discord
import sqlite3
from typing import List, Tuple

from db import get_db_handler
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

    # Get the database handler
    db = await get_db_handler()

    try:
        # Get the active game for highlighting
        active_game = await get_active_game(db)
        active_game_id = active_game["game_id"] if active_game else None

        # Fetch game stats with aggregates in a single query
        games_with_stats: List[Tuple[int, str, int, int, int, int]] = await db.fetchall(
            """
            SELECT
                g.game_id AS id,
                g.title,
                g.grid_size,
                COUNT(DISTINCT e.event_id) AS event_count,
                SUM(CASE WHEN e.status = ? THEN 1 ELSE 0 END) AS closed_count,
                COUNT(DISTINCT b.user_id) AS player_count
            FROM games g
            LEFT JOIN events e ON g.game_id = e.game_id
            LEFT JOIN boards b ON g.game_id = b.game_id
            GROUP BY g.game_id
            ORDER BY g.game_id DESC
            """,
            (EventStatus.CLOSED.name,),
        )

        # Create an embed with the games
        if games_with_stats:
            embed = discord.Embed(
                title="Bingo Games",
                description="List of all bingo games",
                color=discord.Color.blue(),
            )

            for game in games_with_stats:
                (
                    game_id,
                    title,
                    grid_size,
                    event_count,
                    closed_count,
                    player_count,
                ) = game

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
                    name=f"Game #{game_id}: {game_name}", value=value, inline=False
                )

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("No games found.")

    except sqlite3.Error as e:
        await interaction.followup.send(f"Error retrieving games: {e}")
