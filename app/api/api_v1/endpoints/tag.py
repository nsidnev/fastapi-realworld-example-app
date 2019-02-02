from fastapi import APIRouter, Depends

from app.crud.tag import fetch_all_tags
from app.db.database import DataBase, get_database
from app.models.tag import TagsList

router = APIRouter()


@router.get("/tags", response_model=TagsList, tags=["tags"])
async def get_all_tags(db: DataBase = Depends(get_database)):
    async with db.pool.acquire() as conn:
        tags = await fetch_all_tags(conn)
        return TagsList(tags=[tag.tag for tag in tags])
