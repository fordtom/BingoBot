"""Command to display help information about the bingo bot."""
import discord
from discord import Embed
from bingo.utils.channel_check import require_allowed_channel


@require_allowed_channel
async def execute(interaction: discord.Interaction):
    """Generate a help message explaining how to use the bot and its commands."""
    
    
    # Defer the response since help content might take a moment to compile
    await interaction.response.defer(ephemeral=True)
    
    # Create embed for main help message
    help_embed = Embed(
        title="BingoBot Help Guide",
        description="BingoBot helps you run bingo games in your Discord server. Here's how to use it:",
        color=discord.Color.blue()
    )
    
    # Command help entries
    command_help = [
        ("📋 `/bingo help`", "Shows this help message"),
        (
            "🆕 `/bingo new_game <title> <grid_size> <@players...> [events_csv?]`",
            "Creates a complete bingo game with customized settings.\n"
            "• `title`: Name for your bingo game\n"
            "• `grid_size`: Size of the grid (3=3×3, 4=4×4, 5=5×5)\n"
            "• `@players`: Mention all players who will participate\n"
            "• `events_csv`: Optional CSV file with event descriptions",
        ),
        (
            "📊 `/bingo list_games`",
            "Lists all available bingo games with their details.\n",
        ),
        (
            "📊 `/bingo list_events [game_id?]`",
            "Lists all events for the active game or specified game.\n"
            "• `game_id`: Optional game ID (uses active game if not specified)",
        ),
        (
            "🎮 `/bingo view_board <user> [game_id?]`",
            "Shows a player's bingo board.\n"
            "• `user`: The user whose board you want to see\n"
            "• `game_id`: Optional game ID (uses active game if not specified)",
        ),
        (
            "✅ `/bingo vote <event_id> [game_id?]`",
            "Vote that an event has occurred.\n"
            "• `event_id`: ID of the event that happened\n"
            "• `game_id`: Optional game ID (uses active game if not specified)",
        ),
        (
            "⭐ `/bingo set_active_game <game_id>`",
            "Sets which game is currently active for commands that don't specify a game ID.\n"
            "• `game_id`: ID of the game to make active",
        ),
        (
            "🗑️ `/bingo delete_game <game_id>`",
            "Deletes a game and all associated data.\n"
            "• `game_id`: ID of the game to delete",
        ),
    ]

    for name, desc in command_help:
        help_embed.add_field(name=name, value=desc, inline=False)
    
    # Add CSV format information
    help_embed.add_field(
        name="📝 CSV File Format",
        value=(
            "When creating a game, you can optionally upload a CSV file with events. The format is simple:\n\n"
            "**Option 1: With Header (recommended)**\n"
            "```\n"
            "description\n"
            "First event description\n"
            "Second event description\n"
            "...\n"
            "```\n\n"
            "**Option 2: Without Header**\n"
            "```\n"
            "First event description\n"
            "Second event description\n"
            "...\n"
            "```\n\n"
            "The system will automatically assign event IDs when they're stored in the database. You only need to provide the descriptions."
        ),
        inline=False
    )
    
    # Add example
    help_embed.add_field(
        name="💡 Example",
        value=(
            "To create a meeting bingo game:\n"
            "1. Create a CSV with meeting event descriptions\n"
            "2. Run `/bingo new_game \"Team Meeting Bingo\" 5 @player1 @player2 @player3`\n"
            "3. Upload your CSV file when prompted\n"
            "4. Each player can view their board with `/bingo view_board @username`\n"
            "5. When events happen, vote with `/bingo vote <event_id>`\n"
            "6. Use `/bingo list_events` to see all available events and their status"
        ),
        inline=False
    )
    
    # Add footer with tips
    help_embed.set_footer(text="Tip: Use list_events to see event IDs for voting. Check view_board to see your progress!")
    
    # Send the help embed as a followup
    await interaction.followup.send(embed=help_embed, ephemeral=True)

