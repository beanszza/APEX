"""MongoDB client setup using Motor async driver."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_mongo_client: AsyncIOMotorClient | None = None
_mongo_db: AsyncIOMotorDatabase | None = None


async def connect_mongo(uri: str, db_name: str) -> None:
    global _mongo_client, _mongo_db
    _mongo_client = AsyncIOMotorClient(uri)
    _mongo_db = _mongo_client[db_name]
    logger.info("Connected to MongoDB database: %s", db_name)


async def close_mongo() -> None:
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("Closed MongoDB connection.")


def get_database() -> AsyncIOMotorDatabase:
    if _mongo_db is None:
        raise RuntimeError("MongoDB connection is not initialized.")
    return _mongo_db
