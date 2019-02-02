from typing import List

from asyncpg import Connection

from app.models.tag import TagInDB


async def fetch_all_tags(conn: Connection) -> List[TagInDB]:
    tags = []
    rows = await conn.fetch(
        """
        SELECT id, tag, created_at, updated_at
        FROM tags
        """
    )
    for row in rows:
        tags.append(TagInDB(**row))

    return tags


async def get_tags_for_article(conn: Connection, slug: str) -> List[TagInDB]:
    tags = []
    rows = await conn.fetch(
        """
        SELECT t.id, t.tag, t.created_at, t.updated_at
        FROM tags t
        LEFT OUTER JOIN article_tags a ON 
            t.id = a.tag_id 
            AND a.article_id = (SELECT id FROM articles WHERE slug = $1)
        """,
        slug,
    )
    for row in rows:
        tags.append(TagInDB(**row))

    return tags


async def create_tags_that_not_exist(conn: Connection, tags: List[str]):
    await conn.executemany(
        """
        INSERT INTO tags (tag)
        VALUES ($1)
        ON CONFLICT DO NOTHING
        """,
        ((tag,) for tag in tags),
    )


async def link_tags_with_article(conn: Connection, slug: str, tags: List[str]):
    await conn.executemany(
        """
        INSERT INTO article_tags (article_id, tag_id)
        VALUES (
            (SELECT id FROM articles WHERE slug = $1),
            (SELECT id FROM tags WHERE tag = $2)
        )
        """,
        ((slug, tag) for tag in tags),
    )
