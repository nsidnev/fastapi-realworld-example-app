from types import TracebackType
from typing import Optional, Type

from asyncpg import Connection
from asyncpg.pool import Pool


class FakeAsyncPGPool:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool
        self._conn = None
        self._tx = None

    @classmethod
    async def create_pool(cls, pool: Pool) -> "FakeAsyncPGPool":
        pool = cls(pool)
        conn = await pool._pool.acquire()
        tx = conn.transaction()
        await tx.start()
        pool._conn = conn
        pool._tx = tx
        return pool

    async def close(self) -> None:
        await self._tx.rollback()
        await self._pool.release(self._conn)
        await self._pool.close()

    def acquire(self, *, timeout: Optional[float] = None) -> "FakePoolAcquireContent":
        return FakePoolAcquireContent(self)


class FakePoolAcquireContent:
    def __init__(self, pool: FakeAsyncPGPool) -> None:
        self._pool = pool

    async def __aenter__(self) -> Connection:
        return self._pool._conn

    async def __aexit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> None:
        pass
