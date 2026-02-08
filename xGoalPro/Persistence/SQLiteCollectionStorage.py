import aiosqlite
from typing import Optional, Dict, Any, List
from Persistence.StorageInterface import ICollectionStorage
from ResourcePath import resource_path


class SQLiteCollectionStorage(ICollectionStorage):
    """SQLite-based storage for user card collections."""

    def __init__(self, db_path: str = "local.db"):
        """Initializes the storage with the given database path."""
        self.__db_path: str = db_path
        self.__conn: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize_connection(self) -> None:
        """Initializes the database connection and creates the collections table if it does not exist."""
        if self._initialized:
            return
        self.__conn = await aiosqlite.connect(resource_path(self.__db_path))
        await self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, card_id)
            )
        """)
        await self.__conn.commit()
        self._initialized = True

    async def add_to_collection(self, user_id: int, card_id: int) -> None:
        """Adds a card to the user's collection. Ignores if the card already exists."""
        await self.__conn.execute(
            "INSERT OR IGNORE INTO collections (user_id, card_id) VALUES (?, ?)",
            (user_id, card_id)
        )
        await self.__conn.commit()

    async def get_user_complete_collection(self, username: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the complete collection for a user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries containing user_id, username, card_id, and quantity for each card.
        """
        async with self.__conn.execute("""
            SELECT u.id AS user_id, u.username, c.card_id, COUNT(*) AS quantity
            FROM users u
            LEFT JOIN collections c ON u.id = c.user_id
            WHERE u.username = ?
            GROUP BY u.id, u.username, c.card_id
            ORDER BY c.card_id
        """, (username,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    async def get_user_collection_sample(self, username: str, page: int, limit: int) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves a paginated sample of the user's collection.

        Args:
            username: The username of the user.
            page: The page number (1-indexed).
            limit: The maximum number of items per page.

        Returns:
            A list of dictionaries containing user_id, username, and card_id for the selected page.
        """
        offset = (page - 1) * limit
        async with self.__conn.execute("""
            SELECT u.id AS user_id, u.username, c.card_id
            FROM users u
            JOIN collections c ON u.id = c.user_id
            WHERE u.username = ?
            ORDER BY c.card_id
            LIMIT ? OFFSET ?
        """, (username, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    async def close_connection(self) -> None:
        """Closes the database connection."""
        if self.__conn:
            await self.__conn.close()
            self.__conn = None
            self._initialized = False
