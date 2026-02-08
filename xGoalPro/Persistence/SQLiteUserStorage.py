import aiosqlite
from typing import Optional, Dict, Any
from Persistence.StorageInterface import IUserStorage
from ResourcePath import resource_path


class SQLiteUserStorage(IUserStorage):
    """SQLite-based user storage"""

    def __init__(self, db_path: str = "local.db"):
        """Initializes the storage with the given database path."""
        self.__db_path: str = db_path
        self.__conn: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize_connection(self) -> None:
        """Loads database"""
        if self._initialized:
            return
        self.__conn = await aiosqlite.connect(resource_path(self.__db_path))
        await self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.__conn.commit()
        self._initialized = True

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Returns user data given the user's name as a parameter"""
        async with self.__conn.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(zip([column[0] for column in cursor.description], row))
            return None

    async def user_exists(self, username: str) -> bool:
        """Returns whether the given username exists"""
        async with self.__conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

    async def create_user(self, username: str, email: str, password_salt: str, password_hash: str) -> None:
        """Creates new user from given paramteters"""
        await self.__conn.execute(
            "INSERT INTO users (username, email, password_salt, password_hash) VALUES (?, ?, ?, ?)",
            (username, email, password_salt, password_hash)
        )
        await self.__conn.commit()

    async def close_connection(self) -> None:
        """Closes database file"""
        if self.__conn:
            await self.__conn.close()
            self.__conn = None
            self._initialized = False
