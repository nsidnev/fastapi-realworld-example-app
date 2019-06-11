from fastapi import APIRouter, Depends

from ....crud.tag import fetch_all_tags
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.tag import TagsList

router = APIRouter()


@router.get("/tags", response_model=TagsList, tags=["tags"])
async def get_all_tags(db: AsyncIOMotorClient = Depends(get_database)):
    tags = await fetch_all_tags(db)
    return TagsList(tags=[tag.tag for tag in tags])
