"""Database verification helper script for APEX."""

import sys
import logging
from sqlalchemy import create_engine, text
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import asyncio

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ensure-dbs")


async def verify_databases() -> bool:
    settings = get_settings()
    all_ok = True

    # 1. Verify PostgreSQL
    logger.info("Checking PostgreSQL connection to %s...", settings.postgres_connection_string)
    try:
        engine = create_engine(settings.postgres_connection_string, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            if res == 1:
                logger.info("✓ PostgreSQL is UP and reachable.")
            else:
                logger.error("✗ PostgreSQL returned invalid ping.")
                all_ok = False
        engine.dispose()
    except Exception as e:
        logger.error("✗ PostgreSQL connection FAILED: %s", e)
        all_ok = False

    # 2. Verify MongoDB
    logger.info("Checking MongoDB connection to %s...", settings.mongo_uri)
    try:
        mongo_client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
        res = await mongo_client.admin.command("ping")
        if res.get("ok") == 1:
            logger.info("✓ MongoDB is UP and reachable.")
        else:
            logger.error("✗ MongoDB returned invalid ping.")
            all_ok = False
        mongo_client.close()
    except Exception as e:
        logger.error("✗ MongoDB connection FAILED: %s", e)
        all_ok = False

    # 3. Verify Redis
    logger.info("Checking Redis connection to %s...", settings.redis_url)
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        pong = await r.ping()
        if pong:
            logger.info("✓ Redis is UP and reachable.")
        else:
            logger.error("✗ Redis ping failed.")
            all_ok = False
        await r.close()
    except Exception as e:
        logger.error("✗ Redis connection FAILED: %s", e)
        all_ok = False

    return all_ok


if __name__ == "__main__":
    ok = asyncio.run(verify_databases())
    if not ok:
        logger.warning("One or more databases are unreachable. APEX features may degrade.")
        sys.exit(1)
    else:
        logger.info("All database dependencies are verified successfully.")
        sys.exit(0)
