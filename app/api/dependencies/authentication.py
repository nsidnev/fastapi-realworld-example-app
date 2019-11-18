from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from app.api.dependencies.database import get_repository
from app.core.config import JWT_TOKEN_PREFIX, SECRET_KEY
from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.resources import strings
from app.services import jwt


def get_current_user_authorizer(*, required: bool = True) -> Callable:
    return _get_current_user if required else _get_current_user_optional


def _get_authorization_header_retriever(*, required: bool = True) -> Callable:
    return _get_authorization_header if required else _get_authorization_header_optional


def _get_authorization_header(authorization: str = Header(...)) -> str:
    token_prefix, token = authorization.split(" ")
    if token_prefix != JWT_TOKEN_PREFIX:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=strings.WRONG_TOKEN_PREFIX_ERROR
        )

    return token


def _get_authorization_header_optional(
    authorization: Optional[str] = Header(None)
) -> str:
    if authorization:
        return _get_authorization_header(authorization)

    return ""


async def _get_current_user(
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token: str = Depends(_get_authorization_header_retriever()),
) -> User:
    try:
        username = jwt.get_username_from_token(token, str(SECRET_KEY))
    except ValueError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=strings.MALFORMED_PAYLOAD_ERROR
        )

    try:
        return await users_repo.get_user_by_username(username=username)
    except EntityDoesNotExist:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=strings.MALFORMED_PAYLOAD_ERROR
        )


async def _get_current_user_optional(
    repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token: str = Depends(_get_authorization_header_retriever(required=False)),
) -> Optional[User]:
    if token:
        return await _get_current_user(repo, token)

    return None
