import logging

import asyncpg

from app.core.config import DATABASE_URL
from .database import db


async def connect_to_postgres():
    logging.info("Connecting to database")

    db.pool = await asyncpg.create_pool(str(DATABASE_URL))

    logging.info("Connected to database")


async def close_postgres_connection():
    logging.info("Closing connection")

    await db.pool.close()

    logging.info("Connection closed")
