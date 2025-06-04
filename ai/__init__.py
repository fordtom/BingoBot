"""AI module for BingoBot."""
import discord
import logging
from discord import app_commands

# Import all AI commands
from ai.commands import query, files

logger = logging.getLogger(__name__)


def setup_ai_commands(bot):
    """Register all AI commands with the bot and return them."""

    @bot.tree.command(name="ask", description="Ask a question to the AI")
    @app_commands.describe(question="The question you want to ask")
    async def cmd_ask(interaction: discord.Interaction, question: str):
        logger.info(f"Received /ask command from {interaction.user}")
        await query.execute(interaction, question)

    logger.info(f"Registered /ask command: {cmd_ask.name}")

    @bot.tree.command(name="files", description="Ask a question after reading matching files")
    @app_commands.describe(question="The question you want to ask", find="String to search for in the filesystem")
    async def cmd_files(interaction: discord.Interaction, question: str, find: str):
        logger.info(f"Received /files command from {interaction.user}")
        await files.execute(interaction, question, find)

    logger.info(f"Registered /files command: {cmd_files.name}")

    # Return both commands for reference, mirroring bingo.setup_bingo_commands
    return cmd_ask, cmd_files
