"""APScheduler setup for periodic analytics compilation."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.analytics_compiler import AnalyticsCompilerService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def periodic_compile_job() -> None:
    logger.info("Executing scheduled APEX analytics compilation job...")
    try:
        service = AnalyticsCompilerService()
        await service.compile_all_analytics()
        logger.info("Scheduled APEX compilation complete.")
    except Exception as ex:
        logger.error("Failed to execute scheduled compilation: %s", ex)


def start_scheduler() -> None:
    if not scheduler.running:
        # Schedule automatic recompilation daily at 11:00 PM (23:00)
        scheduler.add_job(
            periodic_compile_job,
            CronTrigger(hour=23, minute=0),
            id="daily_11pm_analytics_compile",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started with daily_11pm_analytics_compile job (triggers at 11:00 PM).")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down.")
