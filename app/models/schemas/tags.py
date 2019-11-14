from typing import List

from pydantic import BaseModel


class TagsInList(BaseModel):
    tags: List[str]
