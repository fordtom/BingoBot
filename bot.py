import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from db import get_db
from commands import (
    list_events,
    view_board,
    vote,
    new_game,
    set_active_game,
    delete_game,
    help
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

# Get the allowed channel ID
ALLOWED_CHANNEL_ID = os.getenv('CHANNEL')
if not ALLOWED_CHANNEL_ID:
    print("Warning: CHANNEL environment variable not set. Commands will work in all channels.")
else:
    try:
        ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID)
        print(f"Commands restricted to channel ID: {ALLOWED_CHANNEL_ID}")
    except ValueError:
        print("Warning: CHANNEL environment variable is not a valid integer. Commands will work in all channels.")
        ALLOWED_CHANNEL_ID = None

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    
    # Initialize the database
    await get_db()
    
    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Register bingo commands
bingo_group = app_commands.Group(name="bingo", description="Bingo game commands")


@bingo_group.command(name="list_events")
async def cmd_list_events(interaction: discord.Interaction, game_id: int = None):
    """List events for a game.
    
    Args:
        game_id: Optional ID of the game to list events for. 
                If not provided, the active game will be used.
    """
    await list_events.execute(interaction, game_id)


@bingo_group.command(name="view_board")
async def cmd_view_board(interaction: discord.Interaction, user: discord.Member, game_id: int = None):
    """Display a user's bingo board.
    
    Args:
        user: The user whose board to display
        game_id: Optional ID of the game. If not provided, the active game will be used.
    """
    await view_board.execute(interaction, user, game_id)


@bingo_group.command(name="vote")
async def cmd_vote(interaction: discord.Interaction, event_id: int, game_id: int = None):
    """Vote that an event has occurred.
    
    Args:
        event_id: ID of the event to vote for
        game_id: Optional ID of the game. If not provided, the active game will be used.
    """
    await vote.execute(interaction, event_id, game_id)


@bingo_group.command(name="new_game")
async def cmd_new_game(interaction: discord.Interaction, title: str, grid_size: int, 
                      players: str, events_csv: discord.Attachment = None):
    """Create a new bingo game.
    
    Args:
        title: Title or description of the game
        grid_size: Size of the grid (e.g., 4 for a 4x4 board)
        players: Space-separated list of player mentions (e.g., "@player1 @player2")
        events_csv: Optional CSV file containing event descriptions
    """
    # Parse player mentions - handling all formats of mentions: <@ID>, <@!ID>, etc.
    player_ids = []
    for p in players.split():
        if p.startswith('<@') and p.endswith('>'):
            # Extract just the numeric ID by removing all non-digit characters
            user_id_str = ''.join(c for c in p if c.isdigit())
            if user_id_str.isdigit():
                player_ids.append(int(user_id_str))
    
    await new_game.execute(interaction, title, grid_size, player_ids, events_csv)


@bingo_group.command(name="set_active_game")
async def cmd_set_active_game(interaction: discord.Interaction, game_id: int):
    """Set the active bingo game.
    
    Args:
        game_id: ID of the game to set as active
    """
    await set_active_game.execute(interaction, game_id)


@bingo_group.command(name="delete_game")
async def cmd_delete_game(interaction: discord.Interaction, game_id: int):
    """Delete a game and all associated data.
    
    Args:
        game_id: ID of the game to delete
    """
    await delete_game.execute(interaction, game_id)


@bingo_group.command(name="help")
async def cmd_help(interaction: discord.Interaction):
    """Display help information about how to use the bot."""
    await help.execute(interaction)


# Add the bingo command group to the bot
bot.tree.add_command(bingo_group)


if __name__ == "__main__":
    bot.run(TOKEN)