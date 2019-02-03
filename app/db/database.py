from asyncpg.pool import Pool


class DataBase:
    pool: Pool = None


db = DataBase()


async def get_database():
    return db
