import logging

import asyncpg

from app.core.config import DATABASE_URL

from .database import db


async def connect_to_postgres():
    logging.info("Connecting to database")

    pool = await asyncpg.create_pool(str(DATABASE_URL))
    db.pool = pool

    logging.info("Connected to database")


async def close_postgres_connection():
    logging.info("Closing connection")

    await db.pool.close()

    logging.info("Connection closed")


async def get_database():
    return db
