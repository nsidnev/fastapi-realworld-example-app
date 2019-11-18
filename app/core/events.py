from loguru import logger

from app.db.events import close_db_connection, connect_to_db


async def start_app() -> None:
    await connect_to_db()


@logger.catch
async def stop_app() -> None:
    await close_db_connection()
