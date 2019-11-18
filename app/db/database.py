from asyncpg.pool import Pool


class Database:
    pool: Pool


_db = Database()


def get_database() -> Database:
    return _db
