import pytest
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient

from app.db.repositories.tags import TagsRepository

pytestmark = pytest.mark.asyncio


async def test_empty_list_when_no_tags_exist(app: FastAPI, client: AsyncClient) -> None:
    response = await client.get(app.url_path_for("tags:get-all"))
    assert response.json() == {"tags": []}


async def test_list_of_tags_when_tags_exist(
    app: FastAPI, client: AsyncClient, pool: Pool
) -> None:
    tags = ["tag1", "tag2", "tag3", "tag4", "tag1"]

    async with pool.acquire() as conn:
        tags_repo = TagsRepository(conn)
        await tags_repo.create_tags_that_dont_exist(tags=tags)

    response = await client.get(app.url_path_for("tags:get-all"))
    tags_from_response = response.json()["tags"]
    assert len(tags_from_response) == len(set(tags))
    assert all((tag in tags for tag in tags_from_response))
