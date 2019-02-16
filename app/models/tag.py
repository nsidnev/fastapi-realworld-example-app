from typing import List

from .dbmodel import DBModelMixin
from .rwmodel import RWModel


class Tag(RWModel):
    tag: str


class TagInDB(DBModelMixin, Tag):
    pass


class TagsList(RWModel):
    tags: List[str] = []
