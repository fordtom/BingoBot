"""Cog for all AI-related commands."""

import discord
import logging
from discord.ext import commands
from discord import app_commands

from ai.commands import query

logger = logging.getLogger(__name__)

class AICog(commands.Cog, name="AI"):
    """A cog for all AI-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask a question to the AI")
    @app_commands.describe(
        question="The question you want to ask",
        files="String to search for in the filesystem before answering",
    )
    async def cmd_ask(
        self, interaction: discord.Interaction, question: str, files: str | None = None
    ):
        logger.info(f"Received /ask command from {interaction.user}")
        await query.execute(interaction, question, files)

async def setup(bot: commands.Bot):
    """Set up the AI cog."""
    await bot.add_cog(AICog(bot)) 