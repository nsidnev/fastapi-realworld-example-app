from typing import List

from pydantic import BaseModel

from .dbmodel import DBModelMixin
from .profile import Profile


class Comment(BaseModel):
    body: str
    author: Profile

    # TODO: replace with DBModelMixin after fix of encoders
    id: int
    createdAt: str
    updatedAt: str


class CommentInDB(DBModelMixin, BaseModel):
    body: str
    author: Profile


class CommentInCreate(BaseModel):
    body: str


class CommentInResponse(BaseModel):
    comment: Comment


class ManyCommentsInResponse(BaseModel):
    comments: List[Comment]
