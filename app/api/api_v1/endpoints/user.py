from fastapi import APIRouter, Body, Depends

from app.core.jwt import get_current_user_authorizer
from app.crud.shortcuts import check_free_username_and_email
from app.crud.user import update_user
from app.db.database import DataBase, get_database
from app.models.user import User, UserInResponse, UserInUpdate

router = APIRouter()


@router.get("/user", response_model=UserInResponse, tags=["users"])
async def retrieve_current_user(user: User = Depends(get_current_user_authorizer())):
    return UserInResponse(user=user)


@router.put("/user", response_model=UserInResponse, tags=["users"])
async def update_current_user(
    user: UserInUpdate = Body(..., embed=True),
    current_user: User = Depends(get_current_user_authorizer()),
    db: DataBase = Depends(get_database),
):
    async with db.pool.acquire() as conn:
        if user.username == current_user.username:
            user.username = None
        if user.email == current_user.email:
            user.email = None

        await check_free_username_and_email(conn, user.username, user.email)

        async with conn.transaction():
            dbuser = await update_user(conn, current_user.username, user)
            return UserInResponse(user=User(**dbuser.dict(), token=current_user.token))
