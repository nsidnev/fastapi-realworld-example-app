from datetime import datetime
from typing import List

from pydantic import BaseModel

from .dbmodel import DBModelMixin
from .dtconfig import ISODatetimeConfig
from .profile import Profile


class CommentInDB(DBModelMixin, BaseModel):
    body: str
    author: Profile


class Comment(CommentInDB):
    createdAt: datetime
    updatedAt: datetime


class CommentInCreate(BaseModel):
    body: str


class CommentInResponse(BaseModel):
    comment: Comment

    class Config(ISODatetimeConfig):
        pass


class ManyCommentsInResponse(BaseModel):
    comments: List[Comment]

    class Config(ISODatetimeConfig):
        pass
