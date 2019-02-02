from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Schema


class DateTimeModel(BaseModel):
    createdAt: datetime = Schema(..., alias="created_at")
    updatedAt: datetime = Schema(..., alias="updated_at")


class DBModelMixin(DateTimeModel):
    id: Optional[int] = None
