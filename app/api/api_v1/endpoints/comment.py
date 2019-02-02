from datetime import timezone

from fastapi import APIRouter, Path, Depends, Body
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.jwt import get_current_user_authorizer
from app.crud.comment import create_comment, get_comments_for_article, delete_comment
from app.crud.shortcuts import get_article_or_404
from app.db.database import DataBase, get_database
from app.models.comment import (
    CommentInCreate,
    CommentInDB,
    Comment,
    CommentInResponse,
    ManyCommentsInResponse,
)
from app.models.user import User

router = APIRouter()


# TODO: remove after json_encoders fix in fastapi
def _return_fixed_comment(dbcomment: CommentInDB) -> Comment:
    cm = dbcomment.dict()
    cm.update(
        {
            "createdAt": dbcomment.createdAt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "updatedAt": dbcomment.updatedAt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
    )
    return Comment(**cm)


@router.post(
    "/articles/{slug}/comments",
    response_model=CommentInResponse,
    tags=["comments"],
    status_code=HTTP_201_CREATED,
)
async def create_comment_for_article(
    *,
    slug: str = Path(..., min_length=1),
    comment: CommentInCreate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        await get_article_or_404(conn, slug, user.username)

        async with conn.transaction():
            dbcomment = await create_comment(conn, slug, comment, user.username)
            return CommentInResponse(comment=_return_fixed_comment(dbcomment))


@router.get(
    "/articles/{slug}/comments",
    response_model=ManyCommentsInResponse,
    tags=["comments"],
)
async def get_comment_from_article(
    slug: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer(required=False)),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        await get_article_or_404(conn, slug, user.username)

        dbcomments = await get_comments_for_article(conn, slug, user.username)
        return ManyCommentsInResponse(
            comments=[_return_fixed_comment(dbcomment) for dbcomment in dbcomments]
        )


@router.delete(
    "/articles/{slug}/comments/{id}", tags=["comments"], status_code=HTTP_204_NO_CONTENT
)
async def delete_comment_from_article(
    slug: str = Path(..., min_length=1),
    id: int = Path(..., ge=1),
    user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        await get_article_or_404(conn, slug, user.username)

        await delete_comment(conn, id, user.username)
