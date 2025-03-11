import discord
from db import get_db
from models.event import EventStatus
from utils import check_channel


async def execute(interaction: discord.Interaction, game_id: int = None):
    """
    List all events for a specified game or the active game.
    
    Args:
        interaction: The Discord interaction that triggered the command
        game_id: ID of the game to list events for (optional, uses active game if not provided)
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
    
    # Get events for the game
    async with db.db.execute("SELECT * FROM events WHERE game_id = ? ORDER BY event_id", (game_id,)) as cursor:
        events = await cursor.fetchall()
    
    if not events:
        await interaction.response.send_message(f"No events found for game '{game['title']}' (ID: {game_id}).")
        return
    
    # Format the events list
    event_list = []
    for e in events:
        status = "✓ CLOSED" if e['status'] == EventStatus.CLOSED.name else "○ OPEN"
        event_list.append(f"**Event {e['event_id']}** — {e['description']} — Status: {status}")
    
    # Create an embed
    embed = discord.Embed(
        title=f"Events for Game: {game['title']}",
        description="\n".join(event_list),
        color=discord.Color.blue()
    )
    
    embed.set_footer(text=f"Game ID: {game_id}")
    
    await interaction.response.send_message(embed=embed)