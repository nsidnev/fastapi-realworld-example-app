import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from app.models.domain.users import UserInDB

pytestmark = pytest.mark.asyncio


async def test_user_successful_login(
    app: FastAPI, client: AsyncClient, test_user: UserInDB
) -> None:
    login_json = {"user": {"email": "test@test.com", "password": "password"}}

    response = await client.post(app.url_path_for("auth:login"), json=login_json)
    assert response.status_code == HTTP_200_OK


@pytest.mark.parametrize(
    "credentials_part, credentials_value",
    (("email", "wrong@test.com"), ("password", "wrong")),
)
async def test_user_login_when_credential_part_does_not_match(
    app: FastAPI,
    client: AsyncClient,
    test_user: UserInDB,
    credentials_part: str,
    credentials_value: str,
) -> None:
    login_json = {"user": {"email": "test@test.com", "password": "password"}}
    login_json["user"][credentials_part] = credentials_value
    response = await client.post(app.url_path_for("auth:login"), json=login_json)
    assert response.status_code == HTTP_400_BAD_REQUEST
