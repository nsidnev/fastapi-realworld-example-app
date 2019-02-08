from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel

from .dbmodel import DBModelMixin
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

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class ManyCommentsInResponse(BaseModel):
    comments: List[Comment]
