from typing import Optional

from pydantic import BaseModel, UrlStr


class Profile(BaseModel):
    username: str
    bio: Optional[str] = ""
    image: Optional[UrlStr] = None
    following: bool = False


class ProfileInResponse(BaseModel):
    profile: Profile
