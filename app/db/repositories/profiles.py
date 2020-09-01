from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):
    def __init__(self, conn: Connection):
        super().__init__(conn)
        self._users_repo = UsersRepository(conn)

    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
    ) -> Profile:
        user = await self._users_repo.get_user_by_username(username=username)

        profile = Profile(username=user.username, bio=user.bio, image=user.image)
        if requested_user:
            profile.following = await self.is_user_following_for_another_user(
                target_user=user,
                requested_user=requested_user,
            )

        return profile

    async def is_user_following_for_another_user(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> bool:
        return (
            await queries.is_user_following_for_another(
                self.connection,
                follower_username=requested_user.username,
                following_username=target_user.username,
            )
        )["is_following"]

    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        async with self.connection.transaction():
            await queries.subscribe_user_to_another(
                self.connection,
                follower_username=requested_user.username,
                following_username=target_user.username,
            )

    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        async with self.connection.transaction():
            await queries.unsubscribe_user_from_another(
                self.connection,
                follower_username=requested_user.username,
                following_username=target_user.username,
            )
