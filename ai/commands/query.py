"""Query command to interact with the AI interface."""
import discord
import logging
from ai import interface

logger = logging.getLogger(__name__)

async def execute(interaction: discord.Interaction, question: str, files: str | None = None):
    """Handle the /ask command."""
    logger.info(f"AI query from {interaction.user}: {question} files='{files}'")
    await interaction.response.defer()
    try:
        if files:
            instruction = (
                f"CRITICAL INSTRUCTION: First search the filesystem for '{files}' and read all files you find before answering."
            )
            ai_response = await interface.ask_question(
                interaction, question, prepend_instruction=instruction
            )
        else:
            ai_response = await interface.ask_question(interaction, question)
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")
    except Exception as e:
        logger.error(f"Error in AI query execution: {e}")
        await interaction.followup.send(
            "Sorry, I encountered an error while processing your request."
        )
