from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository


class TagsRepository(BaseRepository):
    async def get_all_tags(self) -> List[str]:
        tags_row = await queries.get_all_tags(self.connection)
        return [tag[0] for tag in tags_row]

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        await queries.create_new_tags(self.connection, [{"tag": tag} for tag in tags])
