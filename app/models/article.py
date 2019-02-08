from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel

from .dbmodel import DBModelMixin
from .profile import Profile


class ArticleFilterParams(BaseModel):
    tag: str = ""
    author: str = ""
    favorited: str = ""
    limit: int = 20
    offset: int = 0


class ArticleBase(BaseModel):
    title: str
    description: str
    body: str
    tagList: List[str] = []


class Article(ArticleBase):
    slug: str
    author: Profile
    favorited: bool
    favoritesCount: int
    createdAt: datetime
    updatedAt: datetime


class ArticleInDB(DBModelMixin, Article):
    pass


class ArticleInResponse(BaseModel):
    article: Article

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class ManyArticlesInResponse(BaseModel):
    articles: List[Article]
    articlesCount: int

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class ArticleInCreate(ArticleBase):
    pass


class ArticleInUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
