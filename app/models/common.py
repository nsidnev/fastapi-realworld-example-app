import datetime

from pydantic import BaseModel, Field, validator


class DateTimeModelMixin(BaseModel):
    created_at: datetime.datetime = None  # type: ignore
    updated_at: datetime.datetime = None  # type: ignore

    @validator("created_at", "updated_at", pre=True)
    def default_datetime(
        cls, value: datetime.datetime,  # noqa: N805, WPS110
    ) -> datetime.datetime:
        return value or datetime.datetime.now()


class IDModelMixin(BaseModel):
    id_: int = Field(0, alias="id")
