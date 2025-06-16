"""Database connection and schema for the Discord bot."""
import aiosqlite
import logging

logger = logging.getLogger(__name__)

# Database path - use local mounted directory instead of network storage
DATABASE_PATH = "/db/bingobot.db"

class DatabaseHandler:
    """Single database handler that maintains one connection and ensures sequential access."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize the database handler.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the database connection and schema."""
        if self._initialized:
            return
            
        logger.info("DATABASE: Initializing database connection")
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        
        # Keep minimal pragmas - remove potentially problematic ones
        await self.db.execute("PRAGMA busy_timeout=5000")  # Reduced timeout
        
        logger.info("DATABASE: SQLite pragmas set")
        
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
        self._initialized = True
        logger.info("DATABASE: Database initialized successfully")
        
    async def execute(self, query, params=None):
        """Execute a query and return the cursor.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            Cursor with results
        """
        if not self._initialized:
            await self.initialize()
            
        logger.debug(f"DATABASE: Executing query: {query[:50]}...")
        if params:
            cursor = await self.db.execute(query, params)
        else:
            cursor = await self.db.execute(query)
        return cursor
    
    async def fetchone(self, query, params=None):
        """Execute a query and fetch one result.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            Single row result or None
        """
        if not self._initialized:
            await self.initialize()
            
        if params:
            cursor = await self.db.execute(query, params)
        else:
            cursor = await self.db.execute(query)
        result = await cursor.fetchone()
        await cursor.close()
        return result
    
    async def fetchall(self, query, params=None):
        """Execute a query and fetch all results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            List of row results
        """
        if not self._initialized:
            await self.initialize()
            
        if params:
            cursor = await self.db.execute(query, params)
        else:
            cursor = await self.db.execute(query)
        results = await cursor.fetchall()
        await cursor.close()
        return results
    
    async def execute_and_commit(self, query, params=None):
        """Execute a query and commit the transaction.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            Cursor with results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            if params:
                cursor = await self.db.execute(query, params)
            else:
                cursor = await self.db.execute(query)
            await self.db.commit()
            return cursor
        except Exception as e:
            logger.error(f"Database error in execute_and_commit: {type(e).__name__}: {str(e)}")
            try:
                await self.db.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {type(rollback_error).__name__}: {str(rollback_error)}")
            raise
    
    async def commit(self):
        """Commit the current transaction."""
        if not self._initialized:
            await self.initialize()
            
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Database error in commit: {type(e).__name__}: {str(e)}")
            raise
    
    async def close(self):
        """Close the database connection."""
        if self.db:
            logger.info("DATABASE: Closing database connection")
            await self.db.close()
            self.db = None
            self._initialized = False


# Singleton database handler
_db_handler = None

# Legacy database instance
_db = None


async def get_db_handler() -> DatabaseHandler:
    """Get the singleton database handler."""
    global _db_handler
    if _db_handler is None:
        logger.info("DATABASE: Creating new database handler")
        _db_handler = DatabaseHandler()
        await _db_handler.initialize()
    return _db_handler


# Legacy Database class for backwards compatibility (deprecated)
class Database:
    """Legacy database connection manager (deprecated - use get_db_handler instead)."""
    
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

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
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


async def get_db() -> DatabaseHandler:
    """Get the database instance (now returns DatabaseHandler for consistency)."""
    # Route all database access through the single handler
    return await get_db_handler()
