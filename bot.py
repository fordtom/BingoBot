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
from utils.env_utils import get_discord_token, get_allowed_channel_id

from db import get_db

# Configure logging
log_file = "/data/bot.log" if os.path.exists("/data") else "bot.log"
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")

# Load environment variables
load_dotenv()
TOKEN = get_discord_token()

# Get the allowed channel ID
ALLOWED_CHANNEL_ID = get_allowed_channel_id()
if ALLOWED_CHANNEL_ID:
    logger.info(f"Commands restricted to channel ID: {ALLOWED_CHANNEL_ID}")
else:
    logger.warning(
        "CHANNEL environment variable not set or invalid. Commands will work in all channels."
    )

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable members intent for mention resolution
bot = commands.Bot(command_prefix='!', intents=intents)


async def load_cogs():
    """Load all cogs."""
    await bot.load_extension('bingo.cog')
    logger.info("Bingo cog loaded")
    await bot.load_extension('ai.cog')
    logger.info("AI cog loaded")
    await bot.load_extension('filesystem.cog')
    logger.info("Filesystem cog loaded")
    await bot.load_extension('monitoring.cog')
    logger.info("Monitoring cog loaded")


@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    # Initialize the database
    await get_db()
    
    # Initialize MCP servers once for the agent interface
    try:
        from ai.interface import get_mcp_servers
        await get_mcp_servers()
        logger.info("MCP servers initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MCP servers: {e}")
    
    # Load cogs
    await load_cogs()

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


async def cleanup():
    """Cleanup function to disconnect from services."""
    # MCP servers are handled by docker-entrypoint.sh cleanup
    logger.info("Bot cleanup completed")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        sys.exit(1)
    finally:
        # Run cleanup
        import asyncio
        asyncio.run(cleanup())
