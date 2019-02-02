from fastapi import APIRouter, Depends

from app.models.tag import TagsList
from app.db.database import DataBase
from app.db.db_utils import get_database
from app.crud.tag import fetch_all_tags

router = APIRouter()


@router.get("/tags", response_model=TagsList, tags=["tags"])
async def get_all_tags(db: DataBase = Depends(get_database)):
    async with db.pool.acquire() as conn:
        tags = await fetch_all_tags(conn)
        return TagsList(tags=[tag.tag for tag in tags])
