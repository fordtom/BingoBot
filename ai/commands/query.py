"""Query command to interact with AI."""
import discord

async def execute(interaction: discord.Interaction, question: str):
    """Execute the query command.
    
    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
    """
    # For now, we just return a simple response
    await interaction.response.send_message(f"answer")