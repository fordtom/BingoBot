"""Command to initialize a new empty bingo game."""
import discord
from db import get_db
from bingo.utils.channel_check import require_allowed_channel

from bingo.models.event import EventStatus


@require_allowed_channel
async def execute(interaction: discord.Interaction):
    """
    Initialize a new empty bingo game.
    
    Args:
        interaction: The Discord interaction that triggered the command
    """
        
    # Defer response to give us time to process
    await interaction.response.defer(ephemeral=False)
    
    db = await get_db()
    
    try:
        # Create a new game with default values
        async with db.db.execute(
            "INSERT INTO games (title, grid_size) VALUES (?, ?)",
            (f"Game created by {interaction.user.display_name}", 4)  # Default grid size of 4
        ) as cursor:
            new_game_id = cursor.lastrowid
        
        # Commit the changes
        await db.db.commit()
        
        # Create a response embed
        embed = discord.Embed(
            title="New Empty Bingo Game Created",
            description=(
                f"Game ID: {new_game_id}\n"
                f"Created by: {interaction.user.display_name}\n\n"
                "This game has no events or players yet. To populate it:\n"
                "• Add players with Discord mentions\n"
                "• Upload a CSV of events or create them manually"
            ),
            color=discord.Color.blue()
        )
        
        # Set this as the active game if no active game exists
        cursor = await db.db.execute("SELECT game_id FROM games WHERE is_active = 1")
        active_game = await cursor.fetchone()
        
        if not active_game:
            await db.db.execute("UPDATE games SET is_active = 1 WHERE game_id = ?", (new_game_id,))
            await db.db.commit()
            embed.add_field(name="Status", value="✅ Set as active game", inline=False)
        else:
            embed.add_field(
                name="Note", 
                value=f"Game ID {active_game['game_id']} is currently active. Use `/bingo set_active_game {new_game_id}` to switch.", 
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        # Rollback transaction on error
        await db.db.rollback()
        
        # Send error message
        if interaction.response.is_done():
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"Error creating game: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"Error creating game: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        return
