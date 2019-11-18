import time
from functools import wraps
from inspect import Traceback
from typing import Any, Callable, Optional, Type

import docker.errors
import psycopg2
from asyncpg import Connection
from asyncpg.pool import Pool
from docker import APIClient


class FakePoolAcquireContext:
    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool

    async def __aenter__(self) -> Connection:
        return self.pool.connection

    async def __aexit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: Traceback
    ) -> None:
        pass


class FakePool:
    def __init__(self, pool: Pool) -> None:
        self.pool: Pool = pool
        self.connection: Optional[Connection] = None

    @classmethod
    async def create_pool(cls, pool: Pool) -> "FakePool":
        fake = cls(pool)
        fake.connection = await pool.acquire()
        return fake

    def acquire(self) -> FakePoolAcquireContext:
        return FakePoolAcquireContext(self)

    async def close(self) -> None:
        if self.connection:  # pragma: no cover
            await self.pool.release(self.connection)
        await self.pool.close()


def do_with_retry(
    catching_exc: Type[Exception], reraised_exc: Type[Exception], error_msg: str
) -> Callable:  # pragma: no cover
    def outer_wrapper(call: Callable) -> Callable:
        @wraps(call)
        def inner_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = 0.001
            for i in range(100):
                try:
                    return call(*args, **kwargs)
                except catching_exc:
                    time.sleep(delay)
                    delay *= 2
            else:  # pragma: no cover
                raise reraised_exc(error_msg)

        return inner_wrapper

    return outer_wrapper


@do_with_retry(docker.errors.APIError, RuntimeError, "cannot pull postgres image")
def pull_image(client: APIClient, image: str) -> None:  # pragma: no cover
    client.pull(image)


@do_with_retry(psycopg2.Error, RuntimeError, "cannot start postgres server")
def ping_postgres(dsn: str) -> None:  # pragma: no cover
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION hstore;")
    cur.close()
    conn.close()
