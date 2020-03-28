import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_403_FORBIDDEN

from app.models.domain.users import User
from app.services.jwt import create_access_token_for_user

pytestmark = pytest.mark.asyncio


async def test_unable_to_login_with_wrong_jwt_prefix(
    app: FastAPI, client: AsyncClient, token: str
) -> None:
    response = await client.get(
        app.url_path_for("users:get-current-user"),
        headers={"Authorization": f"WrongPrefix {token}"},
    )
    assert response.status_code == HTTP_403_FORBIDDEN


async def test_unable_to_login_when_user_does_not_exist_any_more(
    app: FastAPI, client: AsyncClient, authorization_prefix: str
) -> None:
    token = create_access_token_for_user(
        User(username="user", email="email@email.com"), "secret"
    )
    response = await client.get(
        app.url_path_for("users:get-current-user"),
        headers={"Authorization": f"{authorization_prefix} {token}"},
    )
    assert response.status_code == HTTP_403_FORBIDDEN
