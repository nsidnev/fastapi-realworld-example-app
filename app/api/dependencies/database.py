from typing import AsyncGenerator, Callable, Type

from fastapi import Depends
from starlette.requests import Request

from app.db.database import Database
from app.db.repositories.base import BaseRepository


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_repository(repo_type: Type[BaseRepository]) -> Callable:
    async def _get_repo(
        db: Database = Depends(get_db)
    ) -> AsyncGenerator[BaseRepository, None]:
        async with db.pool.acquire() as conn:
            yield repo_type(conn)

    return _get_repo
