from typing import List, Optional

from pydantic import BaseModel, Schema

from app.models.domain.articles import Article
from app.models.domain.rwmodel import RWModel

DEFAULT_ARTICLES_LIMIT = 20
DEFAULT_ARTICLES_OFFSET = 0


class ArticleForResponse(Article):
    tags: List[str] = Schema(..., alias="tagList")  # type: ignore


class ArticleInResponse(RWModel):
    article: ArticleForResponse


class ArticleInCreate(RWModel):
    title: str
    description: str
    body: str
    tags: List[str] = Schema([], alias="tagList")  # type: ignore


class ArticleInUpdate(RWModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None


class ListOfArticlesInResponse(RWModel):
    articles: List[ArticleForResponse]
    articles_count: int


class ArticlesFilters(BaseModel):
    tag: Optional[str] = None
    author: Optional[str] = None
    favorited: Optional[str] = None
    limit: int = Schema(DEFAULT_ARTICLES_LIMIT, ge=1)  # type: ignore
    offset: int = Schema(DEFAULT_ARTICLES_OFFSET, ge=0)  # type: ignore
