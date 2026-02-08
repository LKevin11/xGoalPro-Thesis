import asyncpg
from typing import Optional, Dict, Any
import asyncio
import logging
from functools import wraps
from Persistence.StorageInterface import IUserStorage

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


class PostgresUserStorage(IUserStorage):
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
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(128) NOT NULL,
                    password_salt VARCHAR(64) NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """)

    @retry_on_connection_error()
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1",
                    username
                )

    @retry_on_connection_error()
    async def user_exists(self, username: str) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                    username
                )

    @retry_on_connection_error()
    async def create_user(self, username: str, email: str, salt: str, password_hash: str) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """INSERT INTO users (username, email, password_salt, password_hash)
                    VALUES ($1, $2, $3, $4)""",
                    username, email, salt, password_hash
                )

    async def close_connection(self) -> None:
        if self.pool:
            try:
                await self.pool.close()
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
