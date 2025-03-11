import discord
from db import get_db
from models.event import EventStatus
from utils import check_channel, get_or_validate_game
from utils.config import VOTE_CONSENSUS_THRESHOLD


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
    
    # Get the game (active game if game_id is None)
    game = await get_or_validate_game(interaction, game_id)
    if not game:
        return  # Error message already sent by get_or_validate_game
        
    game_id = game["game_id"]
    
    # Get events for the game
    async with db.db.execute("SELECT * FROM events WHERE game_id = ? ORDER BY event_id", (game_id,)) as cursor:
        events = await cursor.fetchall()
    
    if not events:
        await interaction.response.send_message(f"No events found for game '{game['title']}' (ID: {game_id}).")
        return
    
    # Count total players in the game
    async with db.db.execute(
        "SELECT COUNT(*) as player_count FROM boards WHERE game_id = ?", 
        (game_id,)
    ) as cursor:
        player_count_row = await cursor.fetchone()
        player_count = player_count_row["player_count"]
    
    # Calculate consensus threshold - for small games, require all players
    # For larger games, use the percentage from config
    if player_count <= 3:
        consensus_threshold = player_count  # Everyone must agree for small games
    else:
        consensus_threshold = max(2, int(player_count * VOTE_CONSENSUS_THRESHOLD))
    
    # Format the events list - simple but effective for Discord
    event_list = []
    
    for e in events:
        # Get vote count for this event
        async with db.db.execute(
            "SELECT COUNT(*) as vote_count FROM votes WHERE event_id = ? AND game_id = ?", 
            (e['event_id'], game_id)
        ) as cursor:
            vote_count_row = await cursor.fetchone()
            vote_count = vote_count_row["vote_count"]
        
        # Clean status indicator
        if e['status'] == EventStatus.CLOSED.name:
            status = "✅"
        else:
            status = f"{vote_count}/{consensus_threshold}"
        
        # Format each event entry with emojis and spacing that works in Discord
        event_list.append(f"**Event {e['event_id']}:** {e['description']} `{status}`")
    
    # Create an embed
    embed = discord.Embed(
        title=f"Events for Game: {game['title']}",
        description="\n".join(event_list),
        color=discord.Color.blue()
    )
    
    embed.set_footer(text=f"Game ID: {game_id} | Total Players: {player_count}")
    
    await interaction.response.send_message(embed=embed)