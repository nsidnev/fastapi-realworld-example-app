from typing import Optional

from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from ..crud.user import get_user
from ..db.mongodb import AsyncIOMotorClient
from ..core.config import database_name, followers_collection_name
from ..models.profile import Profile


async def is_following_for_user(
    conn: AsyncIOMotorClient, current_username: str, target_username: str
) -> bool:
    count = await conn[database_name][followers_collection_name].count_documents({"follower": current_username,
                                                                                  "following": target_username})
    return count > 0


async def follow_for_user(
    conn: AsyncIOMotorClient, current_username: str, target_username: str
):
    await conn[database_name][followers_collection_name].insert_one({"follower": current_username,
                                                                     "following": target_username})


async def unfollow_user(conn: AsyncIOMotorClient, current_username: str, target_username: str):
    await conn[database_name][followers_collection_name].delete_many({"follower": current_username,
                                                                     "following": target_username})


async def get_profile_for_user(
    conn: AsyncIOMotorClient, target_username: str, current_username: Optional[str] = None
) -> Profile:
    user = await get_user(conn, target_username)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"User {target_username} not found"
        )

    profile = Profile(**user.dict())
    profile.following = await is_following_for_user(
        conn, current_username, target_username
    )

    return profile
