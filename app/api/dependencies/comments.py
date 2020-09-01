from typing import Optional

from fastapi import Depends, HTTPException, Path
from starlette import status

from app.api.dependencies import articles, authentication, database
from app.db.errors import EntityDoesNotExist
from app.db.repositories.comments import CommentsRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from app.resources import strings
from app.services.comments import check_user_can_modify_comment


async def get_comment_by_id_from_path(
    comment_id: int = Path(..., ge=1),
    article: Article = Depends(articles.get_article_by_slug_from_path),
    user: Optional[User] = Depends(
        authentication.get_current_user_authorizer(required=False),
    ),
    comments_repo: CommentsRepository = Depends(
        database.get_repository(CommentsRepository),
    ),
) -> Comment:
    try:
        return await comments_repo.get_comment_by_id(
            comment_id=comment_id,
            article=article,
            user=user,
        )
    except EntityDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=strings.COMMENT_DOES_NOT_EXIST,
        )


def check_comment_modification_permissions(
    comment: Comment = Depends(get_comment_by_id_from_path),
    user: User = Depends(authentication.get_current_user_authorizer()),
) -> None:
    if not check_user_can_modify_comment(comment, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.USER_IS_NOT_AUTHOR_OF_ARTICLE,
        )
