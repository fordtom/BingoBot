# BingoBot

A Discord bot for playing Bingo games in your server.

## Architecture

The bot uses a modular architecture centered around the bingo game module.

```
BingoBot/                # Root directory
├── ai/                  # AI integration module
├── bingo/               # Bingo game module
│   ├── commands/        # Bingo-specific commands
│   ├── models/          # Bingo-specific models
│   ├── utils/           # Bingo-specific utilities
│   └── __init__.py      # Module initialization
├── db/                  # Database connection
├── data/                # Storage for database files
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

## Database Structure

The bot uses SQLite for data storage. **Important**: Currently, the database does not track server IDs, so all games exist globally across all servers where the bot is added. This means that:

- Game IDs are unique across all servers
- Only one game can be active at a time (globally)
- Players can participate in games regardless of which server they are on

Key tables:
- `games`: Stores game information (title, active status, grid size)
- `events`: Stores events for each game
- `boards`: Stores board information for each player
- `board_squares`: Maps events to positions on players' boards
- `votes`: Tracks player votes on events

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

### CSV Format

The expected format for the Bingo events CSV file is:

```
description
Event 1 description
Event 2 description
...
```

### AI Integration

BingoBot includes AI integration:

- `/ask <question>` - Ask the AI assistant a question

## Docker Support

BingoBot can be deployed using Docker:

```bash
# Build and run with docker-compose
docker-compose up -d
```

This will create a persistent volume for the database in the `data` directory.

## License

MIT