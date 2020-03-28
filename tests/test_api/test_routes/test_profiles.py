import pytest
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.db.repositories.profiles import ProfilesRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.users import UserInDB
from app.models.schemas.profiles import ProfileInResponse

pytestmark = pytest.mark.asyncio


async def test_unregistered_user_will_receive_profile_without_following(
    app: FastAPI, client: AsyncClient, test_user: UserInDB
) -> None:
    response = await client.get(
        app.url_path_for("profiles:get-profile", username=test_user.username)
    )
    profile = ProfileInResponse(**response.json())
    assert profile.profile.username == test_user.username
    assert not profile.profile.following


async def test_user_that_does_not_follows_another_will_receive_profile_without_follow(
    app: FastAPI, authorized_client: AsyncClient, pool: Pool
) -> None:
    async with pool.acquire() as conn:
        users_repo = UsersRepository(conn)
        user = await users_repo.create_user(
            username="user_for_following",
            email="test-for-following@email.com",
            password="password",
        )

    response = await authorized_client.get(
        app.url_path_for("profiles:get-profile", username=user.username)
    )
    profile = ProfileInResponse(**response.json())
    assert profile.profile.username == user.username
    assert not profile.profile.following


async def test_user_that_follows_another_will_receive_profile_with_follow(
    app: FastAPI, authorized_client: AsyncClient, pool: Pool, test_user: UserInDB
) -> None:
    async with pool.acquire() as conn:
        users_repo = UsersRepository(conn)
        user = await users_repo.create_user(
            username="user_for_following",
            email="test-for-following@email.com",
            password="password",
        )

        profiles_repo = ProfilesRepository(conn)
        await profiles_repo.add_user_into_followers(
            target_user=user, requested_user=test_user
        )

    response = await authorized_client.get(
        app.url_path_for("profiles:get-profile", username=user.username)
    )
    profile = ProfileInResponse(**response.json())
    assert profile.profile.username == user.username
    assert profile.profile.following


@pytest.mark.parametrize(
    "api_method, route_name",
    (
        ("GET", "profiles:get-profile"),
        ("POST", "profiles:follow-user"),
        ("DELETE", "profiles:unsubscribe-from-user"),
    ),
)
async def test_user_can_not_retrieve_not_existing_profile(
    app: FastAPI, authorized_client: AsyncClient, api_method: str, route_name: str
) -> None:
    response = await authorized_client.request(
        api_method, app.url_path_for(route_name, username="not_existing_user")
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "api_method, route_name, following",
    (
        ("POST", "profiles:follow-user", True),
        ("DELETE", "profiles:unsubscribe-from-user", False),
    ),
)
async def test_user_can_change_following_for_another_user(
    app: FastAPI,
    authorized_client: AsyncClient,
    pool: Pool,
    test_user: UserInDB,
    api_method: str,
    route_name: str,
    following: bool,
) -> None:
    async with pool.acquire() as conn:
        users_repo = UsersRepository(conn)
        user = await users_repo.create_user(
            username="user_for_following",
            email="test-for-following@email.com",
            password="password",
        )

        if not following:
            profiles_repo = ProfilesRepository(conn)
            await profiles_repo.add_user_into_followers(
                target_user=user, requested_user=test_user
            )

    change_following_response = await authorized_client.request(
        api_method, app.url_path_for(route_name, username=user.username)
    )
    assert change_following_response.status_code == status.HTTP_200_OK

    response = await authorized_client.get(
        app.url_path_for("profiles:get-profile", username=user.username)
    )
    profile = ProfileInResponse(**response.json())
    assert profile.profile.username == user.username
    assert profile.profile.following == following


@pytest.mark.parametrize(
    "api_method, route_name, following",
    (
        ("POST", "profiles:follow-user", True),
        ("DELETE", "profiles:unsubscribe-from-user", False),
    ),
)
async def test_user_can_not_change_following_state_to_the_same_twice(
    app: FastAPI,
    authorized_client: AsyncClient,
    pool: Pool,
    test_user: UserInDB,
    api_method: str,
    route_name: str,
    following: bool,
) -> None:
    async with pool.acquire() as conn:
        users_repo = UsersRepository(conn)
        user = await users_repo.create_user(
            username="user_for_following",
            email="test-for-following@email.com",
            password="password",
        )

        if following:
            profiles_repo = ProfilesRepository(conn)
            await profiles_repo.add_user_into_followers(
                target_user=user, requested_user=test_user
            )

    response = await authorized_client.request(
        api_method, app.url_path_for(route_name, username=user.username)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "api_method, route_name",
    (("POST", "profiles:follow-user"), ("DELETE", "profiles:unsubscribe-from-user")),
)
async def test_user_can_not_change_following_state_for_him_self(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_user: UserInDB,
    api_method: str,
    route_name: str,
) -> None:
    response = await authorized_client.request(
        api_method, app.url_path_for(route_name, username=test_user.username)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
