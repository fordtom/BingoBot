"""Main Discord bot application entry point.

This module initializes the Discord bot and registers all command modules.
It handles bot startup, database initialization, and command synchronization.
"""
import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from db import get_db
# For now, directly import the bingo module, later we'll use the plugin system
import bingo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("DISCORD_TOKEN environment variable not set")
    raise ValueError("DISCORD_TOKEN environment variable not set")

# Get the allowed channel ID
ALLOWED_CHANNEL_ID = os.getenv('CHANNEL')
if not ALLOWED_CHANNEL_ID:
    logger.warning("CHANNEL environment variable not set. Commands will work in all channels.")
else:
    try:
        ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID)
        logger.info(f"Commands restricted to channel ID: {ALLOWED_CHANNEL_ID}")
    except ValueError:
        logger.warning("CHANNEL environment variable is not a valid integer. Commands will work in all channels.")
        ALLOWED_CHANNEL_ID = None

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    # Initialize the database
    await get_db()
    
    # Register bingo commands
    bingo.setup_bingo_commands(bot)
    logger.info("Bingo commands registered")
    
    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    
    logger.error(f"Command error: {error}")
    await ctx.send(f"An error occurred: {error}")


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        sys.exit(1)