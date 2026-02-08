import aiosqlite
from typing import Optional, Dict, Any, List
from Persistence.StorageInterface import ISnakeGameStorage
from ResourcePath import resource_path


class SQLiteSnakeGameStorage(ISnakeGameStorage):
    """SQLite-based storage for the snake game."""

    def __init__(self, db_path: str = "local.db"):
        """Initializes the storage with the given database path."""
        self.__db_path: str = db_path
        self.__conn: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize_connection(self) -> None:
        """Initializes the database connection and creates required tables."""
        if self._initialized:
            return
        self.__conn = await aiosqlite.connect(resource_path(self.__db_path))
        await self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS snakeScores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                score INTEGER NOT NULL DEFAULT 0,
                high_score INTEGER NOT NULL DEFAULT 0
            )
        """)
        await self.__conn.commit()
        self._initialized = True

    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Inserts a new score for a user into the database."""
        await self.__conn.execute(
            "INSERT OR IGNORE INTO snakeScores (user_id, score, high_score) VALUES (?, ?, ?)",
            (user_id, score, high_score)
        )
        await self.__conn.commit()

    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Updates the existing score for a user in the database."""
        await self.__conn.execute(
            "UPDATE snakeScores SET score = ?, high_score = ? WHERE user_id = ?",
            (score, high_score, user_id)
        )
        await self.__conn.commit()

    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the score and high score for the specified user."""
        async with self.__conn.execute(
                "SELECT score, high_score FROM snakeScores WHERE user_id = ?",
                (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            cols = [column[0] for column in cursor.description]
            return dict(zip(cols, row))

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieves a list of top scores, limited by the given number."""
        async with self.__conn.execute("""
            SELECT u.id AS user_id, u.username, r.high_score
            FROM users u
            JOIN snakeScores r ON u.id = r.user_id
            ORDER BY r.high_score DESC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    async def user_exists(self, user_id: int) -> bool:
        """Checks whether a user exists in the database."""
        async with self.__conn.execute("SELECT id FROM snakeScores WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

    async def close_connection(self) -> None:
        """Closes the database connection."""
        if self.__conn:
            await self.__conn.close()
            self.__conn = None
            self._initialized = False
