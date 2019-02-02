from typing import Optional

from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_404_NOT_FOUND
from asyncpg import Connection

from app.crud.user import get_user
from app.models.profile import Profile


async def is_following_for_user(
    conn: Connection, current_username: str, target_username: str
) -> bool:
    return await conn.fetchval(
        """
        SELECT CASE WHEN following_id IS NULL THEN FALSE ELSE TRUE END AS following
        FROM users u
        LEFT OUTER JOIN followers f ON 
            u.id = f.follower_id 
            AND
            f.following_id = (SELECT id FROM users WHERE username = $1)
        WHERE u.username = $2
        """,
        target_username,
        current_username,
    )


async def follow_for_user(
    conn: Connection, current_username: str, target_username: str
):
    await conn.execute(
        """
        INSERT INTO followers(follower_id, following_id) 
        VALUES (
            (SELECT id FROM users WHERE username = $1),
            (SELECT id FROM users WHERE username = $2)
        )
        """,
        current_username,
        target_username,
    )


async def unfollow_user(conn: Connection, current_username: str, target_username: str):
    await conn.execute(
        """
        DELETE FROM followers
        WHERE 
            follower_id = (SELECT id FROM users WHERE username = $1)
            AND 
            following_id = (SELECT id FROM users WHERE username = $2)
        """,
        current_username,
        target_username,
    )


async def get_profile_for_user(
    conn: Connection, target_username: str, current_username: Optional[str] = None
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
