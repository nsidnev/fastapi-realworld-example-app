from typing import List, Optional

from asyncpg import Connection
from slugify import slugify

from app.models.article import (
    ArticleInDB,
    ArticleFilterParams,
    ArticleInCreate,
    ArticleInUpdate,
)
from .profile import get_profile_for_user
from .tag import (
    get_tags_for_article,
    create_tags_that_not_exist,
    link_tags_with_article,
)


async def is_article_favorited_by_user(
    conn: Connection, slug: str, username: str
) -> bool:
    return await conn.fetchval(
        """
        SELECT CASE WHEN user_id IS NULL THEN FALSE ELSE TRUE END AS favorited
        FROM favorites
        WHERE 
            user_id = (SELECT id FROM users WHERE username = $1) 
            AND
            article_id = (SELECT id FROM articles WHERE slug = $2)
        """,
        username,
        slug,
    )


async def add_article_to_favorites(conn: Connection, slug: str, username: str):
    await conn.execute(
        """
        INSERT INTO favorites (user_id, article_id) 
        VALUES (
            (SELECT id FROM users WHERE username = $2),
            (SELECT id FROM articles WHERE slug = $1) 
        )
        """,
        slug,
        username,
    )


async def remove_article_from_favorites(conn: Connection, slug: str, username: str):
    await conn.execute(
        """
        DELETE FROM favorites
        WHERE 
            article_id = (SELECT id FROM articles WHERE slug = $1) 
            AND 
            user_id = (SELECT id FROM users WHERE username = $2)
        """,
        slug,
        username,
    )


async def get_favorites_count_for_article(conn: Connection, slug: str):
    return await conn.fetchval(
        """
        SELECT count(*) as favorites_count
        FROM favorites
        WHERE article_id = (SELECT id FROM articles WHERE slug = $1)
        """,
        slug,
    )


async def get_article_by_slug(
    conn: Connection, slug: str, username: Optional[str] = None
) -> ArticleInDB:
    article_info_row = await conn.fetchrow(
        """
        SELECT id, slug, title, description, body, created_at, updated_at,
            (SELECT username FROM users WHERE id = author_id) AS author_username
        FROM articles
        WHERE slug = $1
        """,
        slug,
    )
    if article_info_row:
        author = await get_profile_for_user(
            conn, article_info_row["author_username"], username
        )
        tags = await get_tags_for_article(conn, slug)
        favorites_count = await get_favorites_count_for_article(conn, slug)
        favorited_by_user = await is_article_favorited_by_user(conn, slug, username)

        return ArticleInDB(
            **article_info_row,
            author=author,
            tagList=[tag.tag for tag in tags],
            favorited=favorited_by_user,
            favoritesCount=favorites_count,
        )


async def create_article_by_slug(
    conn: Connection, article: ArticleInCreate, username: str
) -> ArticleInDB:
    slug = slugify(article.title)

    row = await conn.fetchrow(
        """
        INSERT INTO articles (slug, title, description, body, author_id) 
        VALUES ($1, $2, $3, $4, (SELECT id FROM users WHERE username = $5))
        RETURNING 
            id, 
            slug, 
            title, 
            description, 
            body, 
            (SELECT username FROM users WHERE id = author_id) as author_username, 
            created_at, 
            updated_at
        """,
        slug,
        article.title,
        article.description,
        article.body,
        username,
    )

    author = await get_profile_for_user(conn, row["author_username"], "")

    if article.tagList:
        await create_tags_that_not_exist(conn, article.tagList)
        await link_tags_with_article(conn, slug, article.tagList)

    return ArticleInDB(
        **row, author=author, tagList=article.tagList, favoritesCount=1, favorited=True
    )


async def update_article_by_slug(
    conn: Connection, slug: str, article: ArticleInUpdate, username: str
) -> ArticleInDB:
    dbarticle = await get_article_by_slug(conn, slug, username)

    if article.title:
        dbarticle.slug = slugify(article.title)
        dbarticle.title = article.title
    dbarticle.body = article.body if article.body else dbarticle.body
    dbarticle.description = (
        article.description if article.description else dbarticle.description
    )

    row = await conn.fetchrow(
        """
        UPDATE articles
        SET slug = $1, title = $2, body = $3, description = $4
        WHERE slug = $5 AND author_id = (SELECT id FROM users WHERE username = $6)
        RETURNING updated_at
        """,
        dbarticle.slug,
        dbarticle.title,
        dbarticle.body,
        dbarticle.description,
        slug,
        username,
    )

    dbarticle.updatedAt = row["updated_at"]
    return dbarticle


async def delete_article_by_slug(conn: Connection, slug: str, username: str):
    await conn.execute(
        """
        DELETE FROM articles 
        WHERE slug = $1 AND author_id = (SELECT id FROM users WHERE username = $2)
        """,
        slug,
        username,
    )


async def get_user_articles(
    conn: Connection, username: str, limit=20, offset=0
) -> List[ArticleInDB]:
    articles: List[ArticleInDB] = []
    rows = await conn.fetch(
        """
        SELECT a.id, a.slug, a.title, a.description, a.body, a.created_at, a.updated_at,
            (SELECT username FROM users WHERE id = author_id) AS author_username
        FROM articles a 
        INNER JOIN favorites f on a.id = f.article_id AND user_id = (SELECT id FROM users WHERE username = $1)
        ORDER BY a.created_at
        LIMIT $2
        OFFSET $3
        """,
        username,
        limit,
        offset,
    )
    for row in rows:
        slug = row["slug"]
        author = await get_profile_for_user(conn, row["author_username"], username)
        tags = await get_tags_for_article(conn, slug)
        favorites_count = await get_favorites_count_for_article(conn, slug)
        favorited_by_user = await is_article_favorited_by_user(conn, slug, username)
        articles.append(
            ArticleInDB(
                **row,
                author=author,
                tagList=[tag.tag for tag in tags],
                favoritesCount=favorites_count,
                favorited=favorited_by_user,
            )
        )
    return articles


async def get_articles_with_filters(
    conn: Connection, filters: ArticleFilterParams, username: Optional[str] = None
) -> List[ArticleInDB]:
    articles: List[ArticleInDB] = []
    query_params_count = 0
    base_query = """
        SELECT 
            a.id, 
            a.slug, 
            a.title, 
            a.description, 
            a.body, 
            a.created_at, 
            a.updated_at, 
            (SELECT username FROM users WHERE id = a.author_id) AS author_username
        FROM articles a
        """

    if filters.tag:
        query_params_count += 1
        base_query += f"""
        INNER JOIN article_tags at ON 
            a.id = at.article_id 
            AND 
            at.tag_id = (SELECT id FROM tags WHERE tag = ${query_params_count})
        """

    if filters.favorited:
        query_params_count += 1
        base_query += f"""
        INNER JOIN favorites fav ON 
            a.id = fav.article_id 
            AND 
            fav.user_id = (SELECT id FROM users WHERE username = ${query_params_count})
        """

    if filters.author:
        query_params_count += 1
        base_query += f"""
        LEFT OUTER JOIN users u ON 
            a.author_id = u.id 
            AND 
            u.id = (SELECT id FROM users WHERE u.username = ${query_params_count})
        """

    base_query += f"""
        LIMIT ${query_params_count + 1}
        OFFSET ${query_params_count + 2}
        """

    params = [
        param
        for param in [
            filters.tag or None,
            filters.favorited or None,
            filters.author or None,
            filters.limit,
            filters.offset,
        ]
        if param is not None
    ]

    rows = await conn.fetch(base_query, *params)

    for row in rows:
        slug = row["slug"]
        author = await get_profile_for_user(conn, row["author_username"], username)
        tags = await get_tags_for_article(conn, slug)
        favorites_count = await get_favorites_count_for_article(conn, slug)
        favorited_by_user = await is_article_favorited_by_user(conn, slug, username)
        articles.append(
            ArticleInDB(
                **row,
                author=author,
                tagList=[tag.tag for tag in tags],
                favoritesCount=favorites_count,
                favorited=favorited_by_user,
            )
        )
    return articles
