"""
Utility for checking if commands are run in the correct channel.
"""

import discord
from dotenv import load_dotenv
from utils.env_utils import get_allowed_channel_id

# Load environment variables if not already loaded
load_dotenv()

# Get the allowed channel ID
ALLOWED_CHANNEL_ID = get_allowed_channel_id()

async def is_allowed_channel(interaction: discord.Interaction) -> bool:
    """
    Check if the interaction is in the allowed channel.
    
    Args:
        interaction: The Discord interaction to check
        
    Returns:
        bool: True if the interaction is in the allowed channel or if no channel restriction is set,
              False otherwise
    
    Side effects:
        May respond to the interaction with an error message if the channel check fails
    """
    # If no channel restriction is set, allow all channels
    if not ALLOWED_CHANNEL_ID:
        return True
    
    # Check if the interaction is in the allowed channel
    if interaction.channel_id == ALLOWED_CHANNEL_ID:
        return True
    
    # Send error message if not in the correct channel
    channel = interaction.client.get_channel(ALLOWED_CHANNEL_ID)
    channel_mention = f"<#{ALLOWED_CHANNEL_ID}>" if channel else f"the designated channel (ID: {ALLOWED_CHANNEL_ID})"
    
    await interaction.response.send_message(
        f"This command can only be used in {channel_mention}.",
        ephemeral=True
    )
    return False


def require_allowed_channel(func):
    """Decorator to restrict commands to the configured channel."""

    async def wrapper(*args, **kwargs):
        if not args:
            raise ValueError("Interaction argument missing")
        interaction = args[0]
        if not await is_allowed_channel(interaction):
            return
        return await func(*args, **kwargs)

    return wrapper

