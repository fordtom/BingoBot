"""Query command to interact with AI."""
import discord
import logging

logger = logging.getLogger(__name__)

async def execute(interaction: discord.Interaction, question: str):
    """Execute the query command.
    
    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
    """
    # Log the query for debugging
    logger.info(f"AI query from {interaction.user}: {question}")
    
    # For now, we just return a simple response
    await interaction.response.send_message(f"answer")