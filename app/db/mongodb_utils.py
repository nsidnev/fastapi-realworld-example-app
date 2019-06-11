import logging

from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import MONGODB_URL, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT
from .mongodb import db


async def connect_to_mongo():
    logging.info("连接数据库中...")
    db.client = AsyncIOMotorClient(str(MONGODB_URL),
                                   maxPoolSize=MAX_CONNECTIONS_COUNT,
                                   minPoolSize=MIN_CONNECTIONS_COUNT)
    logging.info("连接数据库成功！")


async def close_mongo_connection():
    logging.info("关闭数据库连接...")
    db.client.close()
    logging.info("数据库连接关闭！")
