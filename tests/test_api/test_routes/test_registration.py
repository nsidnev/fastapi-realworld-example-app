import pytest
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.db.repositories.users import UsersRepository
from app.models.domain.users import UserInDB

pytestmark = pytest.mark.asyncio


async def test_user_success_registration(
    app: FastAPI, client: AsyncClient, pool: Pool
) -> None:
    email, username, password = "test@test.com", "username", "password"
    registration_json = {
        "user": {"email": email, "username": username, "password": password}
    }
    response = await client.post(
        app.url_path_for("auth:register"), json=registration_json
    )
    assert response.status_code == HTTP_201_CREATED

    async with pool.acquire() as conn:
        repo = UsersRepository(conn)
        user = await repo.get_user_by_email(email=email)
        assert user.email == email
        assert user.username == username
        assert user.check_password(password)


@pytest.mark.parametrize(
    "credentials_part, credentials_value",
    (("username", "free_username"), ("email", "free-email@tset.com")),
)
async def test_failed_user_registration_when_some_credentials_are_taken(
    app: FastAPI,
    client: AsyncClient,
    test_user: UserInDB,
    credentials_part: str,
    credentials_value: str,
) -> None:
    registration_json = {
        "user": {
            "email": "test@test.com",
            "username": "username",
            "password": "password",
        }
    }
    registration_json["user"][credentials_part] = credentials_value

    response = await client.post(
        app.url_path_for("auth:register"), json=registration_json
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
