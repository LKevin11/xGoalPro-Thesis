import asyncpg
from typing import Optional, Dict, Any, List
import asyncio
import logging
from functools import wraps
from Persistence.StorageInterface import IPredictionStorage

# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function when a connection error occurs.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (asyncpg.PostgresConnectionError, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * attempt
                        logger.warning(
                            f"Connection attempt {attempt} failed. Retrying in {wait_time} seconds... Error: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
            logger.error(f"Failed after {max_retries} attempts. Last error: {str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator


class PostgresPredictionStorage(IPredictionStorage):
    def __init__(self, url: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._initialized = False

    @retry_on_connection_error(max_retries=3, delay=1.0)
    async def initialize_connection(self) -> None:
        if self._initialized:
            return

        self.pool = await asyncpg.create_pool(
            self.url,
            min_size=1,
            max_size=10,
            timeout=30
        )
        await self.initialize_database()
        self._initialized = True

    @retry_on_connection_error()
    async def initialize_database(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    match_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    home_id INTEGER NOT NULL,
                    home_name TEXT NOT NULL,
                    home_xg DOUBLE PRECISION NOT NULL,
                    away_id INTEGER NOT NULL,
                    away_name TEXT NOT NULL,
                    away_xg DOUBLE PRECISION NOT NULL,
                    home_p DOUBLE PRECISION NOT NULL,
                    draw_p DOUBLE PRECISION NOT NULL,
                    away_p DOUBLE PRECISION NOT NULL,
                    real_home_score INTEGER DEFAULT -1,
                    real_away_score INTEGER DEFAULT -1,
                    UNIQUE(match_id, model)
                );

                CREATE INDEX IF NOT EXISTS idx_predictions_match_model
                ON predictions(match_id, model);
            """)

    @retry_on_connection_error()
    async def get_elo(self, team: str) -> float:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                value = await conn.fetchval(
                    "SELECT elo FROM eloscores WHERE name = $1",
                    team
                )
                return float(value) if value is not None else 1500.0

    @retry_on_connection_error()
    async def get_all_predictions(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch("SELECT * FROM predictions;")
                return [dict(row) for row in rows]

    @retry_on_connection_error()
    async def insert_prediction(
        self,
        match_id: int,
        model: str,
        home_id: int,
        home_xg: float,
        away_id: int,
        away_xg: float,
        home_p: float,
        draw_p: float,
        away_p: float,
        home_name: str,
        away_name: str
    ) -> bool:
        """Insert a new prediction. Returns True if inserted, False if already exists."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.execute("""
                        INSERT INTO predictions (
                            match_id, model, home_id, home_name, home_xg,
                            away_id, away_name, away_xg,
                            home_p, draw_p, away_p
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (match_id, model) DO NOTHING;
                    """, match_id, model, home_id, home_name, home_xg,
                         away_id, away_name, away_xg,
                         home_p, draw_p, away_p)
                    return True
                except asyncpg.UniqueViolationError:
                    return False

    @retry_on_connection_error()
    async def update_prediction_with_score(self, match_id: int, home_score: int, away_score: int) -> bool:
        """Updates a prediction with the real score. Returns True if updated, False if not found."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.execute("""
                    UPDATE predictions
                    SET real_home_score = $1, real_away_score = $2
                    WHERE match_id = $3;
                """, home_score, away_score, match_id)
                # result looks like 'UPDATE <n>', extract number of affected rows
                return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def close_connection(self) -> None:
        if self.pool:
            try:
                await self.pool.close()
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
