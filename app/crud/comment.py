from typing import List, Optional

from asyncpg import Connection

from app.models.comment import CommentInCreate, CommentInDB

from .profile import get_profile_for_user


async def get_comments_for_article(
    conn: Connection, slug: str, username: Optional[str] = None
) -> List[CommentInDB]:
    comments: List[CommentInDB] = []
    rows = await conn.fetch(
        """
        SELECT 
            c.id, 
            c.body, 
            c.created_at, 
            c.updated_at, 
            (SELECT username FROM users WHERE id = c.author_id) as author_username
        FROM commentaries c
        INNER JOIN articles a ON c.article_id = a.id AND (a.slug = $1)
        """,
        slug,
    )
    for row in rows:
        author = await get_profile_for_user(conn, row["author_username"], username)
        comments.append(CommentInDB(**row, author=author))
    return comments


async def create_comment(
    conn: Connection, slug: str, comment: CommentInCreate, username: str
) -> CommentInDB:
    row = await conn.fetchrow(
        """
        INSERT INTO commentaries (body, author_id, article_id) 
        VALUES ($1, (SELECT id FROM users WHERE username = $2), (SELECT id FROM articles WHERE slug = $3))
        RETURNING id, created_at, updated_at
        """,
        comment.body,
        username,
        slug,
    )
    if row:
        author = await get_profile_for_user(conn, username, "")
        return CommentInDB(**row, body=comment.body, author=author)


async def delete_comment(conn: Connection, id: int, username: str):
    await conn.execute(
        """
        DELETE FROM commentaries
        WHERE id = $1 AND author_id = (SELECT id FROM users WHERE username = $2)
        """,
        id,
        username,
    )
