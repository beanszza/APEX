"""APScheduler setup for periodic analytics compilation."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.mongo import get_database
from app.db.redis import get_redis_client
from app.services.analytics_compiler import AnalyticsCompilerService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def periodic_compile_job() -> None:
    logger.info("Executing scheduled APEX analytics compilation job...")
    try:
        db = get_database()
        redis = get_redis_client()
        service = AnalyticsCompilerService(mongo_db=db, redis_client=redis)
        await service.compile_all_analytics()
        logger.info("Scheduled APEX compilation complete.")
    except Exception as ex:
        logger.error("Failed to execute scheduled compilation: %s", ex)


def start_scheduler() -> None:
    if not scheduler.running:
        # Schedule periodic compilation every 30 minutes
        scheduler.add_job(periodic_compile_job, "interval", minutes=30, id="periodic_analytics_compile")
        scheduler.start()
        logger.info("APScheduler started with periodic_analytics_compile job.")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down.")
