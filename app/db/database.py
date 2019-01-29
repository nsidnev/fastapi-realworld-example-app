from contextlib import asynccontextmanager

from asyncpg import Connection
from asyncpg.pool import Pool


class DataBase:
    pool: Pool


db = DataBase()
