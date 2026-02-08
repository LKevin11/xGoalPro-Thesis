import asyncpg
from typing import Optional, Dict, Any, List
import asyncio
import logging
from functools import wraps
from Persistence.StorageInterface import ICollectionStorage

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


class PostgresCollectionStorage(ICollectionStorage):
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
            timeout=30  # connection timeout in seconds
        )
        await self.initialize_database()
        self._initialized = True

    @retry_on_connection_error()
    async def initialize_database(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                    CREATE TABLE IF NOT EXISTS collections (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    card_id INT NOT NULL,
                    acquired_at TIMESTAMPTZ DEFAULT NOW(),
                    CONSTRAINT uq_user_card UNIQUE (user_id, card_id)
                    );
            """)

    @retry_on_connection_error()
    async def add_to_collection(self, user_id: int, card_id: int) -> None:
        """Adds a card to the user's collection"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO collections (user_id, card_id)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id, card_id) DO NOTHING
                    """,
                    user_id, card_id
                )

    @retry_on_connection_error()
    async def get_user_complete_collection(self, username: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the user's entire card collection"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    """
                    SELECT u.id AS user_id, u.username, c.card_id, COUNT(*) AS quantity
                    FROM users u
                    LEFT JOIN collections c ON u.id = c.user_id
                    WHERE u.username = $1
                    GROUP BY u.id, u.username, c.card_id
                    ORDER BY c.card_id
                    """,
                    username
                )

                return [dict(row) for row in rows]

    @retry_on_connection_error()
    async def get_user_collection_sample(self, username: str, page: int, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve a random sample of the user's card collection"""
        offset = (page - 1) * limit
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    """
                    SELECT u.id AS user_id, u.username, c.card_id
                    FROM users u
                    JOIN collections c ON u.id = c.user_id
                    WHERE u.username = $1
                    ORDER BY c.card_id
                    LIMIT $2 OFFSET $3
                    """,
                    username, limit, offset
                )

                return rows

    async def close_connection(self) -> None:
        if self.pool:
            try:
                await self.pool.close()
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
