from typing import Optional, Union

from asyncpg import Connection

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

IS_USER_FOLLOWING_FOR_ANOTHER_QUERY = """
SELECT CASE WHEN following_id IS NULL THEN FALSE ELSE TRUE END AS is_following
FROM users u
         LEFT OUTER JOIN followers_to_followings f ON
        u.id = f.follower_id
        AND
        f.following_id = (SELECT id FROM users WHERE username = $1)
WHERE u.username = $2
"""
ADD_USER_INTO_FOLLOWERS_QUERY = """
INSERT INTO followers_to_followings(follower_id, following_id)
VALUES ((SELECT id FROM users WHERE username = $1),
        (SELECT id FROM users WHERE username = $2))
"""
REMOVE_USER_FROM_FOLLOWERS_QUERY = """
DELETE
FROM followers_to_followings
WHERE follower_id = (SELECT id FROM users WHERE username = $1)
  AND following_id = (SELECT id FROM users WHERE username = $2)
"""

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn)
        self._users_repo = UsersRepository(conn)

    async def get_profile_by_username(
        self, *, username: str, requested_user: Optional[UserLike]
    ) -> Profile:
        user = await self._users_repo.get_user_by_username(username=username)

        profile = Profile(username=user.username, bio=user.bio, image=user.image)
        if requested_user:
            profile.following = await self.is_user_following_for_another_user(
                target_user=user, requested_user=requested_user
            )

        return profile

    async def is_user_following_for_another_user(
        self, *, target_user: UserLike, requested_user: UserLike
    ) -> bool:
        return await self._log_and_fetch_value(
            IS_USER_FOLLOWING_FOR_ANOTHER_QUERY,
            target_user.username,
            requested_user.username,
        )

    async def add_user_into_followers(
        self, *, target_user: UserLike, requested_user: UserLike
    ) -> None:
        async with self.connection.transaction():
            await self._log_and_execute(
                ADD_USER_INTO_FOLLOWERS_QUERY,
                requested_user.username,
                target_user.username,
            )

    async def remove_user_from_followers(
        self, *, target_user: UserLike, requested_user: UserLike
    ) -> None:
        async with self.connection.transaction():
            await self._log_and_execute(
                REMOVE_USER_FROM_FOLLOWERS_QUERY,
                requested_user.username,
                target_user.username,
            )
