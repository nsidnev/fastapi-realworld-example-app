from datetime import datetime
from typing import Optional

from pypika import Parameter as CommonParameter, Query, Table


class Parameter(CommonParameter):
    def __init__(self, count: int) -> None:
        super().__init__("${0}".format(count))


class TypedTable(Table):
    __table__ = ""

    def __init__(
        self,
        name: Optional[str] = None,
        schema: Optional[str] = None,
        alias: Optional[str] = None,
        query_cls: Optional[Query] = None,
    ) -> None:
        if name is None:
            if self.__table__:
                name = self.__table__
            else:
                name = self.__class__.__name__

        super().__init__(name, schema, alias, query_cls)


class Users(TypedTable):
    __table__ = "users"

    id: int
    username: str


class Articles(TypedTable):
    __table__ = "articles"

    id: int
    slug: str
    title: str
    description: str
    body: str
    author_id: int
    created_at: datetime
    updated_at: datetime


class Tags(TypedTable):
    __table__ = "tags"

    tag: str


class ArticlesToTags(TypedTable):
    __table__ = "articles_to_tags"

    article_id: int
    tag: str


class Favorites(TypedTable):
    __table__ = "favorites"

    article_id: int
    user_id: int


users = Users()
articles = Articles()
tags = Tags()
articles_to_tags = ArticlesToTags()
favorites = Favorites()
