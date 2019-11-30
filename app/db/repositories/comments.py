from typing import List, Optional

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User

GET_COMMENTS_FOR_ARTICLE = """
SELECT c.id,
       c.body,
       c.created_at,
       c.updated_at,
       (SELECT username FROM users WHERE id = c.author_id) as author_username
FROM commentaries c
         INNER JOIN articles a ON c.article_id = a.id AND (a.slug = $1)
"""
GET_COMMENT_FOR_ARTICLE_BY_ID = """
SELECT
            c.id,
            c.body,
            c.created_at,
            c.updated_at,
            (SELECT username FROM users WHERE id = c.author_id) as author_username
        FROM commentaries c
        INNER JOIN articles a ON c.article_id = a.id AND (a.slug = $2)
        WHERE c.id = $1
"""
CREATE_COMMENT_QUERY = """
WITH users_subquery AS (
        (SELECT id, username FROM users WHERE username = $2)
)
INSERT
INTO commentaries (body, author_id, article_id)
VALUES ($1,
        (SELECT id FROM users_subquery),
        (SELECT id FROM articles WHERE slug = $3))
RETURNING
    id,
    body,
        (SELECT username FROM users_subquery) AS author_username,
    created_at,
    updated_at
"""
DELETE_ARTICLE_QUERY = """
DELETE
FROM commentaries
WHERE id = $1
  AND author_id = (SELECT id FROM users WHERE username = $2)
"""


class CommentsRepository(BaseRepository):
    def __init__(self, conn: Connection) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)

    async def get_comment_by_id(
        self, *, comment_id: int, article: Article, user: Optional[User] = None
    ) -> Comment:
        comment_row = await self._log_and_fetch_row(
            GET_COMMENT_FOR_ARTICLE_BY_ID, comment_id, article.slug
        )
        if comment_row:
            return await self._get_comment_from_db_record(
                comment_row=comment_row,
                author_username=comment_row["author_username"],
                requested_user=user,
            )

        raise EntityDoesNotExist(
            "comment with id {0} does not exist".format(comment_id)
        )

    async def get_comments_for_article(
        self, *, article: Article, user: Optional[User] = None
    ) -> List[Comment]:
        comments_rows = await self._log_and_fetch(
            GET_COMMENTS_FOR_ARTICLE, article.slug
        )
        return [
            await self._get_comment_from_db_record(
                comment_row=comment_row,
                author_username=comment_row["author_username"],
                requested_user=user,
            )
            for comment_row in comments_rows
        ]

    async def create_comment_for_article(
        self, *, body: str, article: Article, user: User
    ) -> Comment:
        comment_row = await self._log_and_fetch_row(
            CREATE_COMMENT_QUERY, body, user.username, article.slug
        )
        return await self._get_comment_from_db_record(
            comment_row=comment_row,
            author_username=comment_row["author_username"],
            requested_user=user,
        )

    async def delete_comment(self, *, comment: Comment) -> None:
        await self._log_and_execute(
            DELETE_ARTICLE_QUERY, comment.id, comment.author.username
        )

    async def _get_comment_from_db_record(
        self,
        *,
        comment_row: Record,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        return Comment(
            id=comment_row["id"],
            body=comment_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username, requested_user=requested_user
            ),
            created_at=comment_row["created_at"],
            updated_at=comment_row["updated_at"],
        )
