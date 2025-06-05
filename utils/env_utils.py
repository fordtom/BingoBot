"""Environment variable helper utilities."""
import os
from dotenv import load_dotenv


def get_discord_token() -> str:
    """Load and return the Discord bot token."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable not set")
    return token


def get_allowed_channel_id() -> int | None:
    """Return the allowed channel ID if set and valid."""
    load_dotenv()
    channel = os.getenv("CHANNEL")
    if channel:
        try:
            return int(channel)
        except ValueError:
            return None
    return None 