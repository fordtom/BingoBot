"""Command to list uploaded files."""
import os
import logging
import discord

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/data/uploads"


async def execute(interaction: discord.Interaction):
    """List all files stored in the uploads directory."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    files = sorted(os.listdir(UPLOAD_DIR))

    if not files:
        await interaction.response.send_message("No uploaded files found.")
        return

    embed = discord.Embed(
        title="Uploaded Files",
        description="\n".join(f"- {name}" for name in files),
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(embed=embed)
