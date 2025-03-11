"""Bingo game module for Discord bot."""
import discord
from discord import app_commands

# Import all bingo commands
from bingo.commands import (
    list_events, list_games, vote, view_board, 
    help, delete_game, set_active_game, new_game, init_game
)

# Create bingo command group
bingo_group = app_commands.Group(name="bingo", description="Bingo game commands")

def setup_bingo_commands(bot):
    """Register all bingo commands with the bot.
    
    Args:
        bot: The Discord bot to register commands with
    """
    
    @bingo_group.command(name="list_events")
    async def cmd_list_events(interaction: discord.Interaction, game_id: int = None):
        """List events for a game."""
        await list_events.execute(interaction, game_id)
    
    @bingo_group.command(name="view_board")
    async def cmd_view_board(interaction: discord.Interaction, user: discord.Member, game_id: int = None):
        """Display a user's bingo board."""
        await view_board.execute(interaction, user, game_id)
    
    @bingo_group.command(name="vote")
    async def cmd_vote(interaction: discord.Interaction, event_id: int, game_id: int = None):
        """Vote that an event has occurred."""
        await vote.execute(interaction, event_id, game_id)
    
    @bingo_group.command(name="new_game")
    async def cmd_new_game(interaction: discord.Interaction, title: str, grid_size: int, 
                        players: str, events_csv: discord.Attachment = None):
        """Create a new bingo game."""
        # Parse player mentions
        player_ids = []
        for p in players.split():
            if p.startswith('<@') and p.endswith('>'):
                # Extract just the numeric ID
                user_id_str = ''.join(c for c in p if c.isdigit())
                if user_id_str.isdigit():
                    player_ids.append(int(user_id_str))
        
        await new_game.execute(interaction, title, grid_size, player_ids, events_csv)
    
    @bingo_group.command(name="set_active_game")
    async def cmd_set_active_game(interaction: discord.Interaction, game_id: int):
        """Set the active bingo game."""
        await set_active_game.execute(interaction, game_id)
    
    @bingo_group.command(name="delete_game")
    async def cmd_delete_game(interaction: discord.Interaction, game_id: int):
        """Delete a game and all associated data."""
        await delete_game.execute(interaction, game_id)
    
    @bingo_group.command(name="list_games")
    async def cmd_list_games(interaction: discord.Interaction):
        """List all available bingo games with their details."""
        await list_games.execute(interaction)
        
    @bingo_group.command(name="help")
    async def cmd_help(interaction: discord.Interaction):
        """Display help information about how to use the bot."""
        await help.execute(interaction)
        
    @bingo_group.command(name="init_game")
    async def cmd_init_game(interaction: discord.Interaction):
        """Initialize a new empty bingo game."""
        await init_game.execute(interaction)
    
    # Add the bingo command group to the bot
    bot.tree.add_command(bingo_group)
    
    # Return the command group for reference
    return bingo_group