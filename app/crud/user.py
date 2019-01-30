from typing import Optional

from asyncpg import Connection
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.models.user import UserInCreate, UserInUpdate
from models.user import UserInDB


async def get_user(conn: Connection, username: str) -> UserInDB:
    row = await conn.fetchrow(
        """
        SELECT id, username, email, salt, hashed_password, bio, image, created_at, updated_at
        FROM users
        WHERE username = $1
        """,
        username,
    )
    if row:
        return UserInDB(**row)


async def get_user_by_email(conn: Connection, email: EmailStr) -> UserInDB:
    row = await conn.fetchrow(
        """
        SELECT id, username, email, salt, hashed_password, bio, image, created_at, updated_at
        FROM users
        WHERE email = $1
        """,
        email,
    )
    if row:
        return UserInDB(**row)


async def create_user(conn: Connection, user: UserInCreate) -> UserInDB:
    dbuser = UserInDB(**user.dict())
    dbuser.change_password(user.password)

    row = await conn.fetchrow(
        """
        INSERT INTO users (username, email, salt, hashed_password, bio, image) 
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, username, email, salt, hashed_password, bio, image, created_at, updated_at
        """,
        dbuser.username,
        dbuser.email,
        dbuser.salt,
        dbuser.hashed_password,
        dbuser.bio,
        dbuser.image,
    )

    dbuser = UserInDB(**row)
    return dbuser


async def update_user(
    conn: Connection, username: str, user_data: UserInUpdate
) -> UserInDB:
    dbuser = await get_user(conn, username)

    dbuser.username = user_data.username or dbuser.username
    dbuser.email = user_data.email or dbuser.email
    dbuser.bio = user_data.bio or dbuser.bio
    dbuser.image = user_data.image or dbuser.image
    if user_data.password:
        dbuser.change_password(user_data.password)

    row = await conn.fetchrow(
        """
        UPDATE users
        SET username = $1, email = $2, salt = $3, hashed_password = $4, bio = $5, image = $6
        WHERE username = $7
        RETURNING id, username, email, salt, hashed_password, bio, image, created_at, updated_at
        """,
        dbuser.username,
        dbuser.email,
        dbuser.salt,
        dbuser.hashed_password,
        dbuser.bio,
        dbuser.image,
        username,
    )

    dbuser = UserInDB(**row)
    return dbuser


async def check_free_username_and_email(
    conn: Connection, username: Optional[str], email: Optional[EmailStr]
):
    if username:
        user_by_username = await get_user(conn, username)
        if user_by_username:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this username already exists",
            )
    if email:
        user_by_email = await get_user_by_email(conn, email)
        if user_by_email:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this email already exists",
            )
