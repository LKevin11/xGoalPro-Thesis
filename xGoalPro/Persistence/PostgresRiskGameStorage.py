import asyncpg
from typing import Optional, Dict, Any, List
import asyncio
import logging
from functools import wraps
from Persistence.StorageInterface import IRiskGameStorage

# Logging setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry functions when a connection error occurs.
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
                            f"Connection attempt {attempt} failed. Retrying in {wait_time}s... Error: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
            logger.error(f"Failed after {max_retries} attempts. Last error: {str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator


class PostgresRiskGameStorage(IRiskGameStorage):
    def __init__(self, url: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._initialized = False

    @retry_on_connection_error()
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
                CREATE TABLE IF NOT EXISTS riskscore (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    bank INTEGER NOT NULL DEFAULT 0,
                    high_score INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_risk_user_id ON riskscore(user_id);
                CREATE INDEX IF NOT EXISTS idx_risk_high_score ON riskscore(high_score DESC);
            """)

    @retry_on_connection_error()
    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Insert a new user record if not exists."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO riskscore (user_id, bank, high_score)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO NOTHING;
                """, user_id, score, high_score)

    @retry_on_connection_error()
    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Update user score and high score."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE riskscore
                    SET bank = $1, high_score = $2
                    WHERE user_id = $3;
                """, score, high_score, user_id)

    @retry_on_connection_error()
    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user's current and high score."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow("""
                    SELECT bank, high_score
                    FROM riskscore
                    WHERE user_id = $1;
                """, user_id)
                return dict(row) if row else None

    @retry_on_connection_error()
    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get leaderboard of top players by high score."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch("""
                    SELECT u.id AS user_id, u.username, r.high_score
                    FROM users u
                    JOIN riskscore r ON u.id = r.user_id
                    ORDER BY r.high_score DESC
                    LIMIT $1;
                """, limit)
                return [dict(row) for row in rows]

    @retry_on_connection_error()
    async def user_exists(self, user_id: int) -> bool:
        """Check if a user already has a score record."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM riskscore WHERE user_id = $1);",
                    user_id
                )

    async def close_connection(self) -> None:
        """Close connection pool."""
        if self.pool:
            try:
                await self.pool.close()
            except Exception as e:
                logger.error(f"Error closing Postgres pool: {e}")
