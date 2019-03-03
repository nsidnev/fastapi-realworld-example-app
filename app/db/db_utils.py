import logging

import asyncpg

from app.core.config import DATABASE_URL, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT

from .database import db


async def connect_to_postgres():
    logging.info("Connecting to database")

    db.pool = await asyncpg.create_pool(
        str(DATABASE_URL),
        min_size=MIN_CONNECTIONS_COUNT,
        max_size=MAX_CONNECTIONS_COUNT,
    )

    logging.info("Connected to database")


async def close_postgres_connection():
    logging.info("Closing connection")

    await db.pool.close()

    logging.info("Connection closed")
