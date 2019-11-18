from typing import List, Sequence

from app.db.repositories.base import BaseRepository

GET_ALL_TAGS_QUERY = """
SELECT tag
FROM tags
"""

CREATE_TAGS_THAT_DONT_EXIST = """
INSERT INTO tags (tag)
VALUES ($1)
ON CONFLICT DO NOTHING
"""


class TagsRepository(BaseRepository):
    async def get_all_tags(self) -> List[str]:
        tags_row = await self._log_and_fetch(GET_ALL_TAGS_QUERY)
        return [tag[0] for tag in tags_row]

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        await self._log_and_execute_many(
            CREATE_TAGS_THAT_DONT_EXIST, [(tag,) for tag in tags]
        )
