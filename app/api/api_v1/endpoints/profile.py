from typing import Optional

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from app.core.jwt import get_current_user_authorizer
from app.db.database import DataBase
from app.db.db_utils import get_database
from app.crud.user import get_user
from app.crud.profile import (
    is_following_for_user,
    follow_for_user,
    unfollow_user,
    get_profile_for_user,
)
from app.models.user import User
from app.models.profile import ProfileInResponse, Profile

router = APIRouter()


@router.get("/profiles/{username}", response_model=ProfileInResponse, tags=["profiles"])
async def retrieve_profile(
    username: str,
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        profile = await get_profile_for_user(
            conn, username, user.username if user else None
        )
        profile = ProfileInResponse(profile=profile)
        return profile


@router.post(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def follow_user(
    username: str,
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not follow them self",
        )

    async with db.pool.acquire() as conn:
        profile = await get_profile_for_user(conn, username, user.username)

        if profile.following:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"You follow this user already",
            )

        await follow_for_user(conn, user.username, profile.username)
        profile.following = True

        return ProfileInResponse(profile=profile)


@router.delete(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def describe_from_user(
    username: str,
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not describe from them self",
        )

    async with db.pool.acquire() as conn:
        profile = await get_profile_for_user(conn, username, user.username)

        if not profile.following:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"You did not follow this user",
            )

        await unfollow_user(conn, user.username, profile.username)
        profile.following = False

        return ProfileInResponse(profile=profile)
