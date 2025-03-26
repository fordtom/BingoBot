"""AI module for BingoBot."""
import discord
from discord import app_commands

# Import all AI commands
from ai.commands import query

def setup_ai_commands(bot):
    """Register all AI commands with the bot.
    
    Args:
        bot: The Discord bot to register commands with
    """
    
    # Create a direct /ask command (not in a group)
    @bot.tree.command(name="ask")
    async def cmd_ask(interaction: discord.Interaction, question: str):
        """Ask a question to the AI."""
        await query.execute(interaction, question)
    
    # Return the command for reference
    return cmd_ask