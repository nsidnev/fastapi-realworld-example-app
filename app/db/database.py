import asyncpg
from asyncpg.pool import Pool

from app.core.config import DATABASE_URL


class DataBase:
    pool: Pool = None


db = DataBase()


async def get_database():
    if not db.pool:
        db.pool = await asyncpg.create_pool(str(DATABASE_URL))
    return db
