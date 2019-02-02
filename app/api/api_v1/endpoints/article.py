from typing import Optional
from pprint import pprint
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Body, Query
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_204_NO_CONTENT,
    HTTP_201_CREATED,
)
from slugify import slugify

from app.core.jwt import get_current_user_authorizer
from app.db.database import DataBase
from app.db.db_utils import get_database
from app.models.user import User
from app.crud.shortcuts import (
    check_article_for_existence_and_modifying_permissions,
    get_article_or_404,
)
from app.models.article import (
    ArticleInResponse,
    ManyArticlesInResponse,
    ArticleInCreate,
    Article,
    ArticleInUpdate,
    ArticleInDB,
    ArticleFilterParams,
)
from app.crud.article import (
    get_article_by_slug,
    create_article_by_slug,
    update_article_by_slug,
    delete_article_by_slug,
    add_article_to_favorites,
    remove_article_from_favorites,
    get_user_articles,
    get_articles_with_filters,
)

router = APIRouter()


# TODO: remove after json_encoders fix in fastapi
def _return_fixed_article(dbarticle: ArticleInDB) -> Article:
    ad = dbarticle.dict()
    ad.update(
        {
            "createdAt": dbarticle.createdAt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "updatedAt": dbarticle.updatedAt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
    )
    return Article(**ad)


@router.get("/articles", response_model=ManyArticlesInResponse, tags=["articles"])
async def get_articles(
    tag: str = "",
    author: str = "",
    favorited: str = "",
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_authorizer(required=False)),
    db: DataBase = Depends(get_database),
):
    filters = ArticleFilterParams(
        tag=tag, author=author, favorited=favorited, limit=limit, offset=offset
    )
    async with db.pool.acquire() as conn:
        dbarticles = await get_articles_with_filters(conn, filters, user.username)
        return ManyArticlesInResponse(
            articles=[_return_fixed_article(dbarticle) for dbarticle in dbarticles],
            articlesCount=len(dbarticles),
        )


@router.get("/articles/feed", response_model=ManyArticlesInResponse, tags=["articles"])
async def articles_feed(
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbarticles = await get_user_articles(conn, user.username, limit, offset)
        return ManyArticlesInResponse(
            articles=[_return_fixed_article(dbarticle) for dbarticle in dbarticles],
            articlesCount=len(dbarticles),
        )


@router.get("/articles/{slug}", response_model=ArticleInResponse, tags=["articles"])
async def get_article(
    slug: str,
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbarticle = await get_article_by_slug(
            conn, slug, user.username if user else None
        )
        if not dbarticle:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Article with slug '{slug}' not found",
            )

        return ArticleInResponse(article=_return_fixed_article(dbarticle))


@router.post(
    "/articles",
    response_model=ArticleInResponse,
    tags=["articles"],
    status_code=HTTP_201_CREATED,
)
async def create_new_article(
    article: ArticleInCreate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        article_by_slug = await get_article_by_slug(
            conn, slugify(article.title), user.username
        )
        if article_by_slug:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Article with slug '{article_by_slug.slug}' already exists",
            )

        async with conn.transaction():
            dbarticle = await create_article_by_slug(conn, article, user.username)
            return ArticleInResponse(article=_return_fixed_article(dbarticle))


@router.put("/articles/{slug}", response_model=ArticleInResponse, tags=["articles"])
async def update_article(
    slug: str,
    article: ArticleInUpdate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        await check_article_for_existence_and_modifying_permissions(
            conn, slug, user.username
        )

        async with conn.transaction():
            dbarticle = await update_article_by_slug(conn, slug, article, user.username)
            return ArticleInResponse(article=_return_fixed_article(dbarticle))


@router.delete("/articles/{slug}", tags=["articles"], status_code=HTTP_204_NO_CONTENT)
async def delete_article(
    slug: str,
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        await check_article_for_existence_and_modifying_permissions(
            conn, slug, user.username
        )

        async with conn.transaction():
            await delete_article_by_slug(conn, slug, user.username)


@router.post(
    "/articles/{slug}/favorite", response_model=ArticleInResponse, tags=["articles"]
)
async def favorite_article(
    slug: str,
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbarticle = await get_article_or_404(conn, slug, user.username)
        if dbarticle.favorited:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="You already added this article to favorites",
            )

        dbarticle.favorited = True
        dbarticle.favoritesCount += 1

        async with conn.transaction():
            await add_article_to_favorites(conn, slug, user.username)
            return ArticleInResponse(article=_return_fixed_article(dbarticle))


@router.delete(
    "/articles/{slug}/favorite", response_model=ArticleInResponse, tags=["articles"]
)
async def delete_article_from_favorites(
    slug: str,
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        dbarticle = await get_article_or_404(conn, slug, user.username)

        if not dbarticle.favorited:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="You don't have this article in favorites",
            )

        dbarticle.favorited = False
        dbarticle.favoritesCount -= 1

        async with conn.transaction():
            await remove_article_from_favorites(conn, slug, user.username)
            return ArticleInResponse(article=_return_fixed_article(dbarticle))
