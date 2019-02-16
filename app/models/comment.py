from typing import List

from .dbmodel import DBModelMixin
from .profile import Profile
from .rwmodel import RWModel


class CommentInDB(DBModelMixin, RWModel):
    body: str
    author: Profile


class Comment(CommentInDB):
    pass


class CommentInCreate(RWModel):
    body: str


class CommentInResponse(RWModel):
    comment: Comment


class ManyCommentsInResponse(RWModel):
    comments: List[Comment]
