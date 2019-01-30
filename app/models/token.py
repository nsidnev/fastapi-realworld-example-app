from pydantic import BaseModel


class TokenPayload(BaseModel):
    username: str = ""
