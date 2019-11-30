from typing import AsyncGenerator, Callable, Type

from asyncpg.pool import Pool
from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository


def _get_db_pool(request: Request) -> Pool:
    return request.app.state.pool


def get_repository(repo_type: Type[BaseRepository]) -> Callable:  # type: ignore
    async def _get_repo(
        pool: Pool = Depends(_get_db_pool),
    ) -> AsyncGenerator[BaseRepository, None]:
        async with pool.acquire() as conn:
            yield repo_type(conn)

    return _get_repo
