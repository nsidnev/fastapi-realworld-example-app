from os import environ

import alembic.config
import pytest
from asgi_lifespan import LifespanManager
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient

from app.db.repositories.articles import ArticlesRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.articles import Article
from app.models.domain.users import UserInDB
from app.services import jwt


@pytest.fixture(autouse=True)
async def apply_migrations() -> None:
    alembic.config.main(argv=["upgrade", "head"])
    yield
    alembic.config.main(argv=["downgrade", "base"])


@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.main import get_application  # local import for testing purpose

    return get_application()


@pytest.fixture
async def initialized_app(app: FastAPI) -> FastAPI:
    async with LifespanManager(app):
        yield app


@pytest.fixture
def pool(initialized_app: FastAPI) -> Pool:
    return initialized_app.state.pool


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        app=initialized_app,
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture
def authorization_prefix() -> str:
    from app.core.config import JWT_TOKEN_PREFIX

    return JWT_TOKEN_PREFIX


@pytest.fixture
async def test_user(pool: Pool) -> UserInDB:
    async with pool.acquire() as conn:
        return await UsersRepository(conn).create_user(
            email="test@test.com", password="password", username="username"
        )


@pytest.fixture
async def test_article(test_user: UserInDB, pool: Pool) -> Article:
    async with pool.acquire() as connection:
        articles_repo = ArticlesRepository(connection)
        return await articles_repo.create_article(
            slug="test-slug",
            title="Test Slug",
            description="Slug for tests",
            body="Test " * 100,
            author=test_user,
            tags=["tests", "testing", "pytest"],
        )


@pytest.fixture
def token(test_user: UserInDB) -> str:
    return jwt.create_access_token_for_user(test_user, environ["SECRET_KEY"])


@pytest.fixture
def authorized_client(
    client: AsyncClient, token: str, authorization_prefix: str
) -> AsyncClient:
    client.headers = {
        "Authorization": f"{authorization_prefix} {token}",
        **client.headers,
    }
    return client
