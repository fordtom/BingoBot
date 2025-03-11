# BingoBot

A Discord bot that manages multiple Bingo games. Each game has a list of events, an associated set of players, and generated (or manually assigned) boards.

## Setup

1. Clone this repository
2. Install dependencies with uv:
   ```
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
3. Create a `.env` file with your Discord token and allowed channel ID:
   ```
   # .env
   DISCORD_TOKEN=your_discord_bot_token_here
   CHANNEL=your_allowed_channel_id
   ```
4. Run the bot:
   ```
   python bot.py
   ```

## Commands

### Game Management

- `/bingo new_game <title> <grid_size> <@players...> [events_csv_attachment?]` - Create a new game
- `/bingo set_active_game <game_id>` - Set the active game
- `/bingo init_game` - Initialize a new empty game
- `/bingo delete_game <game_id>` - Delete a game and all associated data

### Game Play

- `/bingo list_events [game_id?]` - List events for a game
- `/bingo view_board <user> [game_id?]` - View a user's board
- `/bingo vote <event_id> [game_id?]` - Vote that an event has occurred
- `/bingo help` - Display help information

## CSV Format

The expected format for the events CSV file is:

```
description
Event 1 description
Event 2 description
...
```

## License

MIT