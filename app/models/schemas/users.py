from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl

from app.models.domain.rwmodel import RWModel
from app.models.domain.users import User


class UserInLogin(RWModel):
    email: EmailStr
    password: str


class UserInCreate(UserInLogin):
    username: str


class UserInUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[HttpUrl] = None


class UserWithToken(User):
    token: str


class UserInResponse(RWModel):
    user: UserWithToken
