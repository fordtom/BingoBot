"""Bingo module commands."""
# Import migrated commands
from bingo.commands.list_events import execute as list_events_execute
from bingo.commands.list_games import execute as list_games_execute
from bingo.commands.vote import execute as vote_execute
from bingo.commands.view_board import execute as view_board_execute
from bingo.commands.help import execute as help_execute
from bingo.commands.delete_game import execute as delete_game_execute
from bingo.commands.set_active_game import execute as set_active_game_execute
from bingo.commands.new_game import execute as new_game_execute

# Create command modules that match the legacy pattern
class list_events:
    execute = list_events_execute

class list_games:
    execute = list_games_execute

class vote:
    execute = vote_execute

class view_board:
    execute = view_board_execute

class help:
    execute = help_execute

class delete_game:
    execute = delete_game_execute

class set_active_game:
    execute = set_active_game_execute

class new_game:
    execute = new_game_execute
