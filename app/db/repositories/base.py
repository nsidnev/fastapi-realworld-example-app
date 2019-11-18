from typing import Any, List, Sequence, Tuple

from asyncpg import Record
from asyncpg.connection import Connection
from loguru import logger


def _log_query(query: str, query_params: Tuple[Any, ...]) -> None:
    logger.debug("query: {0}, values: {1}", query, query_params)


class BaseRepository:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    @property
    def connection(self) -> Connection:
        return self._conn

    async def _log_and_fetch(self, query: str, *query_params: Any) -> List[Record]:
        _log_query(query, query_params)
        return await self._conn.fetch(query, *query_params)

    async def _log_and_fetch_row(self, query: str, *query_params: Any) -> Record:
        _log_query(query, query_params)
        return await self._conn.fetchrow(query, *query_params)

    async def _log_and_fetch_value(self, query: str, *query_params: Any) -> Any:
        _log_query(query, query_params)
        return await self._conn.fetchval(query, *query_params)

    async def _log_and_execute(self, query: str, *query_params: Any) -> None:
        _log_query(query, query_params)
        await self._conn.execute(query, *query_params)

    async def _log_and_execute_many(
        self, query: str, *query_params: Sequence[Tuple[Any, ...]]
    ) -> None:
        _log_query(query, query_params)
        await self._conn.executemany(query, *query_params)
