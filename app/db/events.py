import asyncpg
from loguru import logger

from app.core.config import DATABASE_URL, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT
from app.db.database import get_database


async def connect_to_db() -> None:
    logger.info("Connecting to {0}", repr(DATABASE_URL))

    db = get_database()
    db.pool = await asyncpg.create_pool(
        str(DATABASE_URL),
        min_size=MIN_CONNECTIONS_COUNT,
        max_size=MAX_CONNECTIONS_COUNT,
    )

    logger.info("Connection established")


async def close_db_connection() -> None:
    logger.info("Closing connection to database")

    await get_database().pool.close()

    logger.info("Connection closed")
