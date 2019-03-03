from asyncpg import Connection
from pydantic import EmailStr

from app.models.user import UserInCreate, UserInDB, UserInUpdate


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
        RETURNING id, created_at, updated_at
        """,
        dbuser.username,
        dbuser.email,
        dbuser.salt,
        dbuser.hashed_password,
        dbuser.bio,
        dbuser.image,
    )

    dbuser.id = row["id"]
    dbuser.created_at = row["created_at"]
    dbuser.updated_at = row["updated_at"]

    return dbuser


async def update_user(conn: Connection, username: str, user: UserInUpdate) -> UserInDB:
    dbuser = await get_user(conn, username)

    dbuser.username = user.username or dbuser.username
    dbuser.email = user.email or dbuser.email
    dbuser.bio = user.bio or dbuser.bio
    dbuser.image = user.image or dbuser.image
    if user.password:
        dbuser.change_password(user.password)

    updated_at = await conn.fetchval(
        """
        UPDATE users
        SET username = $1, email = $2, salt = $3, hashed_password = $4, bio = $5, image = $6
        WHERE username = $7
        RETURNING updated_at
        """,
        dbuser.username,
        dbuser.email,
        dbuser.salt,
        dbuser.hashed_password,
        dbuser.bio,
        dbuser.image,
        username,
    )

    dbuser.updated_at = updated_at
    return dbuser
