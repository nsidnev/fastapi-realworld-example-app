from typing import Optional

from asyncpg import Connection
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.models.article import ArticleInDB

from .article import get_article_by_slug
from .user import get_user, get_user_by_email


async def check_free_username_and_email(
    conn: Connection, username: Optional[str] = None, email: Optional[EmailStr] = None
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


async def get_article_or_404(
    conn: Connection, slug: str, username: Optional[str] = None
) -> ArticleInDB:
    searched_article = await get_article_by_slug(conn, slug, username)
    if not searched_article:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Article with slug '{slug}' not found",
        )
    return searched_article


async def check_article_for_existence_and_modifying_permissions(
    conn: Connection, slug: str, username: str = ""
):
    searched_article = await get_article_by_slug(conn, slug, username)
    if not searched_article:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Article with slug '{slug}' not found",
        )
    if searched_article.author.username != username:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You have no permission for modifying this article",
        )
