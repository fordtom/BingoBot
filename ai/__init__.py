"""AI module for BingoBot."""
import discord
import logging
from discord import app_commands

# Import all AI commands
from ai.commands import query

logger = logging.getLogger(__name__)


def setup_ai_commands(bot):
    """Register all AI commands with the bot and return them."""

    @bot.tree.command(name="ask", description="Ask a question to the AI")
    @app_commands.describe(
        question="The question you want to ask",
        files="String to search for in the filesystem before answering",
    )
    async def cmd_ask(
        interaction: discord.Interaction, question: str, files: str | None = None
    ):
        logger.info(f"Received /ask command from {interaction.user}")
        await query.execute(interaction, question, files)

    logger.info(f"Registered /ask command: {cmd_ask.name}")

    # Return command for reference, mirroring bingo.setup_bingo_commands
    return (cmd_ask,)
