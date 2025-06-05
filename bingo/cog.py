"""Cog for all bingo-related commands."""

import discord
from discord.ext import commands
from discord import app_commands

from bingo.commands import (
    list_events, list_games, vote, view_board, 
    help as help_cmd, delete_game, set_active_game, new_game, init_game
)
from utils.discord_utils import parse_player_ids

class BingoCog(commands.Cog, name="Bingo"):
    """A cog for all bingo-related commands."""

    bingo_group = app_commands.Group(name="bingo", description="Bingo game commands")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @bingo_group.command(name="list_events")
    async def cmd_list_events(self, interaction: discord.Interaction, game_id: int = None):
        """List events for a game."""
        await list_events.execute(interaction, game_id)
    
    @bingo_group.command(name="view_board")
    async def cmd_view_board(self, interaction: discord.Interaction, user: discord.Member, game_id: int = None):
        """Display a user's bingo board."""
        await view_board.execute(interaction, user, game_id)
    
    @bingo_group.command(name="vote")
    async def cmd_vote(self, interaction: discord.Interaction, event_id: int, game_id: int = None):
        """Vote that an event has occurred."""
        await vote.execute(interaction, event_id, game_id)
    
    @bingo_group.command(name="new_game")
    async def cmd_new_game(self, interaction: discord.Interaction, title: str, grid_size: int, 
                        players: str, events_csv: discord.Attachment = None):
        """Create a new bingo game."""
        player_ids = parse_player_ids(players)
        await new_game.execute(interaction, title, grid_size, player_ids, events_csv)
    
    @bingo_group.command(name="set_active_game")
    async def cmd_set_active_game(self, interaction: discord.Interaction, game_id: int):
        """Set the active bingo game."""
        await set_active_game.execute(interaction, game_id)
    
    @bingo_group.command(name="delete_game")
    async def cmd_delete_game(self, interaction: discord.Interaction, game_id: int):
        """Delete a game and all associated data."""
        await delete_game.execute(interaction, game_id)
    
    @bingo_group.command(name="list_games")
    async def cmd_list_games(self, interaction: discord.Interaction):
        """List all available bingo games with their details."""
        await list_games.execute(interaction)
        
    @bingo_group.command(name="help")
    async def cmd_help(self, interaction: discord.Interaction):
        """Display help information about how to use the bot."""
        await help_cmd.execute(interaction)
        
    @bingo_group.command(name="init_game")
    async def cmd_init_game(self, interaction: discord.Interaction):
        """Initialize a new empty bingo game."""
        await init_game.execute(interaction)


async def setup(bot: commands.Bot):
    """Set up the Bingo cog."""
    cog = BingoCog(bot)
    bot.tree.add_command(cog.bingo_group)
    await bot.add_cog(cog) 