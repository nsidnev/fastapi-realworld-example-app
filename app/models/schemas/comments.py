from typing import List

from app.models.domain.comments import Comment
from app.models.domain.rwmodel import RWModel


class ListOfCommentsInResponse(RWModel):
    comments: List[Comment]


class CommentInResponse(RWModel):
    comment: Comment


class CommentInCreate(RWModel):
    body: str
