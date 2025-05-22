"""AI module for BingoBot."""
import discord
import logging
from discord import app_commands

# Import all AI commands
from ai.commands import query

logger = logging.getLogger(__name__)

def setup_ai_commands(bot):
    """Register all AI commands with the bot.
    
    Args:
        bot: The Discord bot to register commands with
    """
    
    # Create a direct /ask command (not in a group)
    @bot.tree.command(name="ask", description="Ask a question to the AI")
    @app_commands.describe(question="The question you want to ask")
    async def cmd_ask(interaction: discord.Interaction, question: str):
        """Ask a question to the AI."""
        logger.info(f"Received /ask command from {interaction.user}")
        await query.execute(interaction, question)
    
    # Create a web search command
    @bot.tree.command(name="search", description="Ask a question and search the web for an answer")
    @app_commands.describe(question="The question you want to search for")
    async def cmd_search(interaction: discord.Interaction, question: str):
        """Ask a question and search the web for an answer."""
        logger.info(f"Received /search command from {interaction.user}")
        await query.execute(interaction, question, use_web_search=True)
    
    # Log the command registration
    logger.info(f"Registered /ask command: {cmd_ask.name}")
    logger.info(f"Registered /search command: {cmd_search.name}")
    
    # Return the commands for reference
    return [cmd_ask, cmd_search]