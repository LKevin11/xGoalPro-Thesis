import asyncpg
from typing import Optional, Dict, Any, List
import asyncio
import logging
from functools import wraps
from Persistence.StorageInterface import IRiskGameStorage

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


class PostgresDribbleKingStorage(IRiskGameStorage):
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
                CREATE TABLE IF NOT EXISTS dribblescore (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    score INTEGER NOT NULL DEFAULT 0,
                    high_score INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_dribble_user_id ON dribblescore(user_id);
                CREATE INDEX IF NOT EXISTS idx_dribble_high_score ON dribblescore(high_score DESC);
            """)

    @retry_on_connection_error()
    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO dribblescore (user_id, score, high_score)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO NOTHING;
                """, user_id, score, high_score)

    @retry_on_connection_error()
    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE dribblescore
                    SET score = $1, high_score = $2
                    WHERE user_id = $3;
                """, score, high_score, user_id)

    @retry_on_connection_error()
    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow("""
                    SELECT score, high_score
                    FROM dribblescore
                    WHERE user_id = $1;
                """, user_id)
                return dict(row) if row else None

    @retry_on_connection_error()
    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch("""
                    SELECT u.id AS user_id, u.username, r.high_score
                    FROM users u
                    JOIN dribblescore r ON u.id = r.user_id
                    ORDER BY r.high_score DESC
                    LIMIT $1;
                """, limit)
                return [dict(row) for row in rows]

    @retry_on_connection_error()
    async def user_exists(self, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM dribblescore WHERE user_id = $1);",
                    user_id
                )

    async def close_connection(self) -> None:
        if self.pool:
            try:
                await self.pool.close()
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
