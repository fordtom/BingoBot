"""
Utility for checking if commands are run in the correct channel.
"""

import os
import discord
from dotenv import load_dotenv

# Load environment variables if not already loaded
load_dotenv()

# Get the allowed channel ID
ALLOWED_CHANNEL_ID = os.getenv('CHANNEL')
if ALLOWED_CHANNEL_ID:
    try:
        ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID)
    except ValueError:
        ALLOWED_CHANNEL_ID = None

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