from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from slugify import slugify
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from ....core.jwt import get_current_user_authorizer
from ....core.utils import create_aliased_response
from ....crud.article import (
    add_article_to_favorites,
    create_article_by_slug,
    delete_article_by_slug,
    get_article_by_slug,
    get_articles_with_filters,
    get_user_articles,
    remove_article_from_favorites,
    update_article_by_slug,
)
from ....crud.shortcuts import (
    check_article_for_existence_and_modifying_permissions,
    get_article_or_404,
)
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.article import (
    ArticleFilterParams,
    ArticleInCreate,
    ArticleInResponse,
    ArticleInUpdate,
    ManyArticlesInResponse,
)
from ....models.user import User

router = APIRouter()


@router.get("/articles", response_model=ManyArticlesInResponse, tags=["articles"])
async def get_articles(
        tag: str = "",
        author: str = "",
        favorited: str = "",
        limit: int = Query(20, gt=0),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user_authorizer(required=False)),
        db: AsyncIOMotorClient = Depends(get_database),
):
    filters = ArticleFilterParams(
        tag=tag, author=author, favorited=favorited, limit=limit, offset=offset
    )
    dbarticles = await get_articles_with_filters(
        db, filters, user.username if user else None
    )
    return create_aliased_response(
        ManyArticlesInResponse(articles=dbarticles, articles_count=len(dbarticles))
    )


@router.get("/articles/feed", response_model=ManyArticlesInResponse, tags=["articles"])
async def articles_feed(
        limit: int = Query(20, gt=0),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbarticles = await get_user_articles(db, user.username, limit, offset)
    return create_aliased_response(
        ManyArticlesInResponse(articles=dbarticles, articles_count=len(dbarticles))
    )


@router.get("/articles/{slug}", response_model=ArticleInResponse, tags=["articles"])
async def get_article(
        slug: str = Path(..., min_length=1),
        user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbarticle = await get_article_by_slug(
        db, slug, user.username if user else None
    )
    if not dbarticle:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Article with slug '{slug}' not found",
        )

    return create_aliased_response(ArticleInResponse(article=dbarticle))


@router.post(
    "/articles",
    response_model=ArticleInResponse,
    tags=["articles"],
    status_code=HTTP_201_CREATED,
)
async def create_new_article(
        article: ArticleInCreate = Body(..., embed=True),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    article_by_slug = await get_article_by_slug(
        db, slugify(article.title), user.username
    )
    if article_by_slug:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文章已存在 slug='{article_by_slug.slug}'",
        )

    dbarticle = await create_article_by_slug(db, article, user.username)
    return create_aliased_response(ArticleInResponse(article=dbarticle))


@router.put("/articles/{slug}", response_model=ArticleInResponse, tags=["articles"])
async def update_article(
        slug: str = Path(..., min_length=1),
        article: ArticleInUpdate = Body(..., embed=True),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    await check_article_for_existence_and_modifying_permissions(
        db, slug, user.username
    )

    dbarticle = await update_article_by_slug(db, slug, article, user.username)
    return create_aliased_response(ArticleInResponse(article=dbarticle))


@router.delete("/articles/{slug}", tags=["articles"], status_code=HTTP_204_NO_CONTENT)
async def delete_article(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    await check_article_for_existence_and_modifying_permissions(
        db, slug, user.username
    )

    await delete_article_by_slug(db, slug, user.username)


@router.post(
    "/articles/{slug}/favorite", response_model=ArticleInResponse, tags=["articles"]
)
async def favorite_article(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbarticle = await get_article_or_404(db, slug, user.username)
    if dbarticle.favorited:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You already added this article to favorites",
        )

    dbarticle.favorited = True
    dbarticle.favorites_count += 1

    await add_article_to_favorites(db, slug, user.username)
    return create_aliased_response(ArticleInResponse(article=dbarticle))


@router.delete(
    "/articles/{slug}/favorite", response_model=ArticleInResponse, tags=["articles"]
)
async def delete_article_from_favorites(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbarticle = await get_article_or_404(db, slug, user.username)

    if not dbarticle.favorited:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You don't have this article in favorites",
        )

    dbarticle.favorited = False
    dbarticle.favorites_count -= 1

    await remove_article_from_favorites(db, slug, user.username)
    return create_aliased_response(ArticleInResponse(article=dbarticle))
