"""Filesystem module for uploading and listing files."""
import logging
import discord
from discord import app_commands

from filesystem.commands import upload, list_files

logger = logging.getLogger(__name__)

# Create command group
file_group = app_commands.Group(name="file", description="File management commands")


def setup_filesystem_commands(bot):
    """Register filesystem commands with the bot."""

    @file_group.command(name="upload")
    @app_commands.describe(file="File to upload")
    async def cmd_upload(interaction: discord.Interaction, file: discord.Attachment):
        logger.info(f"Received /file upload from {interaction.user}")
        await upload.execute(interaction, file)

    logger.info(f"Registered /file upload command: {cmd_upload.name}")

    @file_group.command(name="list")
    async def cmd_list(interaction: discord.Interaction):
        logger.info(f"Received /file list from {interaction.user}")
        await list_files.execute(interaction)

    logger.info(f"Registered /file list command: {cmd_list.name}")

    bot.tree.add_command(file_group)
    return cmd_upload, cmd_list
