from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Schema


class DBModelMixin(BaseModel):
    id: Optional[int] = None
    createdAt: Optional[datetime] = Schema(None, alias="created_at")
    updatedAt: Optional[datetime] = Schema(None, alias="updated_at")
