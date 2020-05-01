import pathlib

import aiosql

queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "asyncpg")
