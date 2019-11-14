from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB

GET_USER_BY_EMAIL_QUERY = """
SELECT id,
       username,
       email,
       salt,
       hashed_password,
       bio,
       image,
       created_at,
       updated_at
FROM users
WHERE email = $1
"""
GET_USER_BY_USERNAME_QUERY = """
SELECT id,
       username,
       email,
       salt,
       hashed_password,
       bio,
       image,
       created_at,
       updated_at
FROM users
WHERE username = $1
"""
CREATE_USER_QUERY = """
INSERT INTO users (username, email, salt, hashed_password)
VALUES ($1, $2, $3, $4)
RETURNING id, created_at, updated_at
"""
UPDATE_USER_QUERY = """
UPDATE users
SET username        = $1,
    email           = $2,
    salt            = $3,
    hashed_password = $4,
    bio             = $5,
    image           = $6
WHERE username = $7
RETURNING updated_at
"""


class UsersRepository(BaseRepository):
    async def get_user_by_email(self, *, email: str) -> UserInDB:
        user_row = await self._log_and_fetch_row(GET_USER_BY_EMAIL_QUERY, email)
        if user_row:
            return UserInDB(**user_row)

        raise EntityDoesNotExist("user with email {0} does not exist".format(email))

    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_row = await self._log_and_fetch_row(GET_USER_BY_USERNAME_QUERY, username)
        if user_row:
            return UserInDB(**user_row)

        raise EntityDoesNotExist(
            "user with username {0} does not exist".format(username)
        )

    async def create_user(
        self, *, username: str, email: str, password: str
    ) -> UserInDB:
        user = UserInDB(username=username, email=email)
        user.change_password(password)

        async with self.connection.transaction():
            user_row = await self._log_and_fetch_row(
                CREATE_USER_QUERY,
                user.username,
                user.email,
                user.salt,
                user.hashed_password,
            )

        return user.copy(update=dict(user_row))

    async def update_user(  # noqa: WPS211
        self,
        *,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        bio: Optional[str] = None,
        image: Optional[str] = None,
    ) -> UserInDB:
        user_in_db = await self.get_user_by_username(username=user.username)

        user_in_db.username = username or user_in_db.username
        user_in_db.email = email or user_in_db.email
        user_in_db.bio = bio or user_in_db.bio
        user_in_db.image = image or user_in_db.image
        if password:
            user_in_db.change_password(password)

        async with self.connection.transaction():
            user_in_db.updated_at = await self._log_and_fetch_row(
                UPDATE_USER_QUERY,
                user_in_db.username,
                user_in_db.email,
                user_in_db.salt,
                user_in_db.hashed_password,
                user_in_db.bio,
                user_in_db.image,
                user.username,
            )

        return user_in_db
