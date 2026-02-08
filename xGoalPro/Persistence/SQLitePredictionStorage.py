import aiosqlite
from typing import Optional, Dict, Any, List
from Persistence.StorageInterface import IPredictionStorage
from ResourcePath import resource_path


class SQLitePredictionStorage(IPredictionStorage):
    """SQLite-based storage for match predictions."""

    def __init__(self, db_path: str = "local.db"):
        """Initializes the storage with the given database path."""
        self.__db_path: str = db_path
        self.__conn: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize_connection(self) -> None:
        """Initializes the database connection and creates the predictions table if it does not exist."""
        if self._initialized:
            return
        self.__conn = await aiosqlite.connect(resource_path(self.__db_path))
        await self.__conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                home_id INTEGER NOT NULL,
                home_name TEXT NOT NULL,
                home_xg REAL NOT NULL,
                away_id INTEGER NOT NULL,
                away_name TEXT NOT NULL,
                away_xg REAL NOT NULL,
                home_p REAL NOT NULL,
                draw_p REAL NOT NULL,
                away_p REAL NOT NULL,
                real_home_score INTEGER DEFAULT -1,
                real_away_score INTEGER DEFAULT -1,
                UNIQUE(match_id, model)
            )
        """)
        await self.__conn.commit()
        self._initialized = True

    async def get_elo(self, team: str) -> float:
        """Returns the ELO score for the given team, or 1500.0 if the team is not found."""
        async with self.__conn.execute("SELECT elo FROM eloScores WHERE name = ?", (team,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1500.0  # default value if team not found

    async def get_all_predictions(self) -> List[Dict[str, Any]]:
        """Returns a list of all stored predictions as dictionaries."""
        async with self.__conn.execute("SELECT * FROM predictions") as cursor:
            rows = await cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    async def insert_prediction(self, match_id: int, model: str, home_id: int, home_xg: float,
                                away_id: int, away_xg: float, home_p: float, draw_p: float,
                                away_p: float, home_name: str, away_name: str) -> bool:
        """
        Inserts a new prediction into the database.

        Returns True if the prediction was inserted, or False if a prediction
        for the same match_id and model already exists.
        """
        try:
            await self.__conn.execute("""
                INSERT INTO predictions (
                    match_id, model, home_id, home_name, home_xg, away_id, away_name, away_xg,
                    home_p, draw_p, away_p
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, model, home_id, home_name, home_xg, away_id, away_name, away_xg,
                home_p, draw_p, away_p
            ))
            await self.__conn.commit()
            return True
        except aiosqlite.IntegrityError:
            # match_id + model already exists
            return False

    async def update_prediction_with_score(self, match_id: int, home_score: int, away_score: int) -> bool:
        """
        Updates an existing prediction with the actual match scores.

        Returns True if the prediction was updated, or False if no prediction
        for the given match_id exists.
        """
        cursor = await self.__conn.execute("""
            UPDATE predictions
            SET real_home_score = ?, real_away_score = ?
            WHERE match_id = ?
        """, (home_score, away_score, match_id))
        await self.__conn.commit()
        return cursor.rowcount > 0

    async def close_connection(self) -> None:
        """Closes the database connection."""
        if self.__conn:
            await self.__conn.close()
            self.__conn = None
            self._initialized = False
