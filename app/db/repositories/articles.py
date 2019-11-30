from typing import List, Optional, Sequence

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.db.repositories.tags import TagsRepository
from app.models.domain.articles import Article
from app.models.domain.users import User

ADD_ARTICLE_INTO_FAVORITES_QUERY = """
INSERT INTO favorites (user_id, article_id)
VALUES ((SELECT id FROM users WHERE username = $1),
        (SELECT id FROM articles WHERE slug = $2))
ON CONFLICT DO NOTHING
"""
REMOVE_ARTICLE_FROM_FAVORITES_QUERY = """
DELETE
FROM favorites
WHERE user_id = (SELECT id FROM users WHERE username = $1)
  AND article_id = (SELECT id FROM articles WHERE slug = $2)
"""
IS_ARTICLE_FAVORITED_BY_USER_QUERY = """
SELECT CASE WHEN count(user_id) > 0 THEN TRUE ELSE FALSE END AS favorited
FROM favorites
WHERE
    user_id = (SELECT id FROM users WHERE username = $1)
    AND
    article_id = (SELECT id FROM articles WHERE slug = $2)
"""
GET_FAVORITES_COUNT_FOR_ARTICLE_QUERY = """
SELECT count(*) as favorites_count
FROM favorites
WHERE article_id = (SELECT id FROM articles WHERE slug = $1)
"""
GET_TAGS_FOR_ARTICLE_QUERY = """
SELECT t.tag
FROM tags t
INNER JOIN articles_to_tags att ON
t.tag = att.tag
AND
att.article_id = (SELECT id FROM articles WHERE slug = $1)
"""
GET_ARTICLE_BY_SLUG_QUERY = """
SELECT id,
       slug,
       title,
       description,
       body,
       created_at,
       updated_at,
       (SELECT username FROM users WHERE id = author_id) AS author_username
FROM articles
WHERE slug = $1
"""
CREATE_ARTICLE_QUERY = """
WITH author_subquery AS (
    SELECT id, username
    FROM users
    WHERE username = $5
)
INSERT
INTO articles (slug, title, description, body, author_id)
VALUES ($1, $2, $3, $4, (SELECT id FROM author_subquery))
RETURNING
    id,
    slug,
    title,
    description,
    body,
        (SELECT username FROM author_subquery) as author_username,
    created_at,
    updated_at
"""
LINK_ARTICLE_WITH_TAGS = """
INSERT INTO articles_to_tags (article_id, tag)
VALUES ((SELECT id FROM articles WHERE slug = $1),
        (SELECT tag FROM tags WHERE tag = $2))
ON CONFLICT DO NOTHING
"""
UPDATE_ARTICLE_QUERY = """
UPDATE articles
SET slug        = $1,
    title       = $2,
    body        = $3,
    description = $4
WHERE slug = $5
  AND author_id = (SELECT id FROM users WHERE username = $6)
RETURNING updated_at
"""
DELETE_ARTICLE_QUERY = """
DELETE
FROM articles
WHERE slug = $1
  AND author_id = (SELECT id FROM users WHERE username = $2)
"""
GET_ARTICLES_FOR_USER_FEED_QUERY = """
SELECT a.id,
       a.slug,
       a.title,
       a.description,
       a.body,
       a.created_at,
       a.updated_at,
       (
           SELECT username
           FROM users
           WHERE id = a.author_id
       ) AS author_username
FROM articles a
         INNER JOIN followers_to_followings f ON
        f.following_id = a.author_id AND
        f.follower_id = (SELECT id FROM users WHERE username = $1)
ORDER BY a.created_at
LIMIT $2
OFFSET
$3
"""
GET_ARTICLES_QUERY = """
SELECT a.id,
       a.slug,
       a.title,
       a.description,
       a.body,
       a.created_at,
       a.updated_at,
       (
           SELECT username
           FROM users
           WHERE id = a.author_id
       ) AS author_username
FROM articles a
"""
_FILTER_BY_TAG_QUERY = """
INNER JOIN articles_to_tags at ON
a.id = at.article_id
AND
at.tag = (
    SELECT tag
    FROM tags
    WHERE tag = ${tag_param_index}
)
"""
_FILTER_BY_FAVORITED_QUERY = """
INNER JOIN favorites fav ON
a.id = fav.article_id
AND
fav.user_id = (
    SELECT id
    FROM users
    WHERE username = ${favorited_param_index}
)
"""
_FILTER_BY_AUTHOR_QUERY = """
INNER JOIN users u ON
a.author_id = u.id
AND
u.id = (
    SELECT id
    FROM users
    WHERE username = ${author_param_index}
)
"""
_LIMIT_QUERY = """
LIMIT ${limit_param_index}
"""
_OFFSET_QUERY = """
OFFSET ${offset_param_index}
"""
_ORDER_QUERY = """
ORDER BY a.created_at
"""

EMPTY_STRING = ""
AUTHOR_USERNAME_ALIAS = "author_username"


class ArticlesRepository(BaseRepository):  # noqa: WPS214
    def __init__(self, conn: Connection) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)
        self._tags_repo = TagsRepository(conn)

    async def create_article(  # noqa: WPS211
        self,
        *,
        slug: str,
        title: str,
        description: str,
        body: str,
        author: User,
        tags: Optional[Sequence[str]] = None,
    ) -> Article:
        async with self.connection.transaction():
            article_row = await self._log_and_fetch_row(
                CREATE_ARTICLE_QUERY, slug, title, description, body, author.username
            )

            if tags:
                await self._tags_repo.create_tags_that_dont_exist(tags=tags)
                await self._link_article_with_tags(slug=slug, tags=tags)

        return await self._get_article_from_db_record(
            article_row=article_row,
            slug=slug,
            author_username=article_row[AUTHOR_USERNAME_ALIAS],
            requested_user=author,
        )

    async def update_article(  # noqa: WPS211
        self,
        *,
        article: Article,
        slug: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Article:
        updated_article = article.copy(deep=True)
        updated_article.slug = slug or updated_article.slug
        updated_article.title = title or article.title
        updated_article.body = body or article.body
        updated_article.description = description or article.description

        async with self.connection.transaction():
            updated_article.updated_at = await self._log_and_fetch_value(
                UPDATE_ARTICLE_QUERY,
                updated_article.slug,
                updated_article.title,
                updated_article.body,
                updated_article.description,
                article.slug,
                article.author.username,
            )

        return updated_article

    async def delete_article(self, *, article: Article) -> None:
        async with self.connection.transaction():
            await self._log_and_execute(
                DELETE_ARTICLE_QUERY, article.slug, article.author.username
            )

    async def filter_articles(  # noqa: WPS211
        self,
        *,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        requested_user: Optional[User] = None,
    ) -> List[Article]:
        query_params_count = 0
        query = GET_ARTICLES_QUERY

        if tag:
            query_params_count += 1
            query = EMPTY_STRING.join((query, _FILTER_BY_TAG_QUERY)).format(
                tag_param_index=query_params_count
            )

        if author:
            query_params_count += 1
            query = EMPTY_STRING.join((query, _FILTER_BY_AUTHOR_QUERY)).format(
                author_param_index=query_params_count
            )

        if favorited:
            query_params_count += 1
            query = EMPTY_STRING.join((query, _FILTER_BY_FAVORITED_QUERY)).format(
                favorited_param_index=query_params_count
            )

        query = EMPTY_STRING.join(
            (query, _ORDER_QUERY, _LIMIT_QUERY, _OFFSET_QUERY)
        ).format(
            limit_param_index=query_params_count + 1,
            offset_param_index=query_params_count + 2,
        )

        articles_rows = await self._log_and_fetch(
            query,
            *[
                query_param
                for query_param in (tag, author, favorited, limit, offset)
                if query_param is not None
            ],
        )

        return [
            await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row["slug"],
                author_username=article_row[AUTHOR_USERNAME_ALIAS],
                requested_user=requested_user,
            )
            for article_row in articles_rows
        ]

    async def get_articles_for_user_feed(
        self, *, user: User, limit: int = 20, offset: int = 0
    ) -> List[Article]:
        articles_rows = await self._log_and_fetch(
            GET_ARTICLES_FOR_USER_FEED_QUERY, user.username, limit, offset
        )
        return [
            await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row["slug"],
                author_username=article_row[AUTHOR_USERNAME_ALIAS],
                requested_user=user,
            )
            for article_row in articles_rows
        ]

    async def get_article_by_slug(
        self, *, slug: str, requested_user: Optional[User] = None
    ) -> Article:
        article_row = await self._log_and_fetch_row(GET_ARTICLE_BY_SLUG_QUERY, slug)
        if article_row:
            return await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row["slug"],
                author_username=article_row[AUTHOR_USERNAME_ALIAS],
                requested_user=requested_user,
            )

        raise EntityDoesNotExist("article with slug {0} does not exist".format(slug))

    async def get_tags_for_article_by_slug(self, *, slug: str) -> List[str]:
        tag_rows = await self._log_and_fetch(GET_TAGS_FOR_ARTICLE_QUERY, slug)
        return [row["tag"] for row in tag_rows]

    async def get_favorites_count_for_article_by_slug(self, *, slug: str) -> int:
        return await self._log_and_fetch_value(
            GET_FAVORITES_COUNT_FOR_ARTICLE_QUERY, slug
        )

    async def is_article_favorited_by_user(self, *, slug: str, user: User) -> bool:
        return await self._log_and_fetch_value(
            IS_ARTICLE_FAVORITED_BY_USER_QUERY, user.username, slug
        )

    async def add_article_into_favorites(self, *, article: Article, user: User) -> None:
        await self._log_and_execute(
            ADD_ARTICLE_INTO_FAVORITES_QUERY, user.username, article.slug
        )

    async def remove_article_from_favorites(
        self, *, article: Article, user: User
    ) -> None:
        await self._log_and_execute(
            REMOVE_ARTICLE_FROM_FAVORITES_QUERY, user.username, article.slug
        )

    async def _get_article_from_db_record(
        self,
        *,
        article_row: Record,
        slug: str,
        author_username: str,
        requested_user: Optional[User],
    ) -> Article:
        return Article(
            id=article_row["id"],
            slug=slug,
            title=article_row["title"],
            description=article_row["description"],
            body=article_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username, requested_user=requested_user
            ),
            tags=await self.get_tags_for_article_by_slug(slug=slug),
            favorites_count=await self.get_favorites_count_for_article_by_slug(
                slug=slug
            ),
            favorited=await self.is_article_favorited_by_user(
                slug=slug, user=requested_user
            )
            if requested_user
            else False,
            created_at=article_row["created_at"],
            updated_at=article_row["updated_at"],
        )

    async def _link_article_with_tags(self, *, slug: str, tags: Sequence[str]) -> None:
        await self._log_and_execute_many(
            LINK_ARTICLE_WITH_TAGS, [(slug, tag) for tag in tags]
        )
