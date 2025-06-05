"""Cog for all filesystem-related commands."""

import discord
import logging
from discord.ext import commands
from discord import app_commands

from filesystem.commands import upload, list_files

logger = logging.getLogger(__name__)

class FilesystemCog(commands.Cog, name="Filesystem"):
    """A cog for all filesystem-related commands."""

    file_group = app_commands.Group(name="file", description="File management commands")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @file_group.command(name="upload")
    @app_commands.describe(file="File to upload")
    async def cmd_upload(self, interaction: discord.Interaction, file: discord.Attachment):
        logger.info(f"Received /file upload from {interaction.user}")
        await upload.execute(interaction, file)

    @file_group.command(name="list")
    async def cmd_list(self, interaction: discord.Interaction):
        logger.info(f"Received /file list from {interaction.user}")
        await list_files.execute(interaction)

async def setup(bot: commands.Bot):
    """Set up the Filesystem cog."""
    cog = FilesystemCog(bot)
    await bot.add_cog(cog) 