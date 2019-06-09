from typing import Optional

from fastapi import APIRouter, Depends, Path
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from ....core.jwt import get_current_user_authorizer
from ....crud.profile import follow_for_user, get_profile_for_user, unfollow_user
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.profile import ProfileInResponse
from ....models.user import User

router = APIRouter()


@router.get("/profiles/{username}", response_model=ProfileInResponse, tags=["profiles"])
async def retrieve_profile(
    username: str = Path(..., min_length=1),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    profile = await get_profile_for_user(
        db, username, user.username if user else None
    )
    profile = ProfileInResponse(profile=profile)
    return profile


@router.post(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def follow_user(
    username: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not follow them self",
        )

    profile = await get_profile_for_user(db, username, user.username)

    if profile.following:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You follow this user already",
        )

    await follow_for_user(db, user.username, profile.username)
    profile.following = True

    return ProfileInResponse(profile=profile)


@router.delete(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def describe_from_user(
    username: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not describe from them self",
        )

    profile = await get_profile_for_user(db, username, user.username)

    if not profile.following:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You did not follow this user",
        )

    await unfollow_user(db, user.username, profile.username)
    profile.following = False

    return ProfileInResponse(profile=profile)
