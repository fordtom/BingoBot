"""Database connection and schema for the Discord bot."""
import os
import aiosqlite
from pathlib import Path

# Use a path in the data directory if it exists, otherwise use default location
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
if os.path.exists(DATA_DIR) and os.path.isdir(DATA_DIR):
    DATABASE_PATH = os.path.join(DATA_DIR, "bingobot.db")
else:
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bingobot.db")

class Database:
    """Database connection manager for the BingoBot."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db = None
        
    async def connect(self):
        """Connect to the database."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        
    async def close(self):
        """Close the database connection."""
        if self.db:
            await self.db.close()
            
    async def initialize(self):
        """Initialize the database schema."""
        await self.connect()
        
        # Create tables
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            is_active BOOLEAN DEFAULT 0,
            grid_size INTEGER DEFAULT 4
        )
        ''')
        
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER,
            game_id INTEGER,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            PRIMARY KEY (event_id, game_id),
            FOREIGN KEY (game_id) REFERENCES games (game_id)
        )
        ''')
        
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS boards (
            board_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            user_id INTEGER,
            grid_size INTEGER DEFAULT 4,
            FOREIGN KEY (game_id) REFERENCES games (game_id),
            UNIQUE (game_id, user_id)
        )
        ''')
        
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS board_squares (
            board_id INTEGER,
            row INTEGER,
            column INTEGER,
            event_id INTEGER,
            PRIMARY KEY (board_id, row, column),
            FOREIGN KEY (board_id) REFERENCES boards (board_id)
        )
        ''')
        
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            event_id INTEGER,
            game_id INTEGER,
            user_id INTEGER,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id, game_id, user_id),
            FOREIGN KEY (game_id) REFERENCES games (game_id)
        )
        ''')
        
        await self.db.commit()


# Singleton database instance
_db = None


async def get_db() -> Database:
    """Get the database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.initialize()
    return _db