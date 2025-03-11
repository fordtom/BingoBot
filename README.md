# BingoBot

A Discord bot for playing Bingo games in your server.

## Architecture

The bot uses a modular architecture centered around the bingo game module.

```
BingoBot/                # Root directory
├── bingo/               # Bingo game module
│   ├── commands/        # Bingo-specific commands
│   ├── models/          # Bingo-specific models
│   ├── utils/           # Bingo-specific utilities
│   └── __init__.py      # Module initialization
├── db/                  # Database connection
├── bot.py               # Main bot entry point
└── requirements.txt     # Dependencies
```

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Discord token and optional allowed channel ID:
   ```
   # .env
   DISCORD_TOKEN=your_discord_bot_token_here
   CHANNEL=your_allowed_channel_id  # Optional
   ```
4. Run the bot:
   ```
   python bot.py
   ```

## Bingo Module

The Bingo module allows you to create and manage Bingo games with customizable events.

### Commands

- `/bingo init_game` - Initialize a new empty bingo game
- `/bingo new_game <title> <grid_size> <@players...> [events_csv_attachment?]` - Create a new game
- `/bingo set_active_game <game_id>` - Set the active game
- `/bingo delete_game <game_id>` - Delete a game and all associated data
- `/bingo list_games` - List all available games with details
- `/bingo list_events [game_id?]` - List events for a game
- `/bingo view_board <user> [game_id?]` - View a user's board
- `/bingo vote <event_id> [game_id?]` - Vote that an event has occurred
- `/bingo help` - Display help information

#### CSV Format

The expected format for the Bingo events CSV file is:

```
description
Event 1 description
Event 2 description
...
```

## License

MIT