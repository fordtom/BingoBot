"""Command to delete a bingo game and all its data."""

import discord
from db import get_db
from bingo.utils.channel_check import require_allowed_channel


@require_allowed_channel
async def execute(interaction: discord.Interaction, game_id: int):
    """
    Delete a game and all associated data from the database.

    Args:
        interaction: The Discord interaction that triggered the command
        game_id: ID of the game to delete
    """

    db = await get_db()

    # Check if the game exists
    game = await db.fetchone("SELECT * FROM games WHERE game_id = ?", (game_id,))

    if not game:
        await interaction.response.send_message(f"Game with ID {game_id} not found.")
        return

    try:
        # Get game title for confirmation message
        game_title = game["title"]
        is_active = bool(game["is_active"])

        # Start a transaction using the handler's context manager
        async with db.transaction() as executor:
            # Delete votes associated with events in this game
            await executor.execute(
                "DELETE FROM votes WHERE game_id = ?",
                (game_id,),
            )

            # Delete board squares associated with boards in this game
            await executor.execute(
                """DELETE FROM board_squares 
               WHERE board_id IN (SELECT board_id FROM boards WHERE game_id = ?)""",
                (game_id,),
            )

            # Delete boards in this game
            await executor.execute(
                "DELETE FROM boards WHERE game_id = ?",
                (game_id,),
            )

            # Delete events in this game
            await executor.execute(
                "DELETE FROM events WHERE game_id = ?",
                (game_id,),
            )

            # Delete the game itself
            await executor.execute(
                "DELETE FROM games WHERE game_id = ?",
                (game_id,),
            )

            # If we deleted the active game, find the game with the lowest ID and set it as active
            new_active_game_info = ""
            if is_active:
                # Find game with lowest ID
                next_game = await executor.fetchone(
                    "SELECT * FROM games ORDER BY game_id ASC LIMIT 1"
                )

                if next_game:
                    # Set this game as active
                    await executor.execute(
                        "UPDATE games SET is_active = 1 WHERE game_id = ?",
                        (next_game["game_id"],),
                    )
                    new_active_game_info = (
                        f"\nGame '{next_game['title']}' (ID: {next_game['game_id']}) "
                        "has been set as the new active game."
                    )
                else:
                    new_active_game_info = (
                        "\nNo games remain. You'll need to create a new game."
                    )

        await interaction.response.send_message(
            f"Game '{game_title}' (ID: {game_id}) has been deleted along with all associated data.{new_active_game_info}"
        )

    except Exception as e:
        await interaction.response.send_message(f"Error deleting game: {str(e)}")
        return
