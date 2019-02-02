from typing import List

from pydantic import BaseModel

from .dbmodel import DBModelMixin


class Tag(BaseModel):
    tag: str


class TagInDB(DBModelMixin, Tag):
    pass


class TagsList(BaseModel):
    tags: List[str] = []
