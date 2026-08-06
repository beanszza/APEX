"""APEX — Analytical Platform for Enterprise eXcellence Application Entry Point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.core.config import get_settings
from app.db.mongo import connect_mongo, close_mongo
from app.db.redis import connect_redis, close_redis
from app.db.postgres import close_pg
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.routes.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Startup
    logger.info("Connecting to MongoDB at %s", settings.mongo_uri)
    await connect_mongo(settings.mongo_uri, settings.mongo_database)

    logger.info("Connecting to Redis at %s", settings.redis_url)
    await connect_redis(settings.redis_url)

    start_scheduler()

    # Trigger background compilation on APEX startup so Redis/MongoDB are instantly populated
    try:
        from app.db.mongo import get_database
        from app.db.redis import get_redis_client
        from app.services.analytics_compiler import AnalyticsCompilerService
        mongo_db = get_database()
        redis_cl = get_redis_client()
        compiler = AnalyticsCompilerService(mongo_db=mongo_db, redis_client=redis_cl)
        await compiler.compile_all_analytics()
        logger.info("APEX initial analytics compilation complete on startup.")
    except Exception as ex:
        logger.warning("Notice: APEX startup analytics compilation skipped/failed: %s", ex)

    yield

    # Shutdown
    stop_scheduler()
    await close_redis()
    await close_mongo()
    close_pg()
    logger.info("APEX shutdown complete.")


app = FastAPI(
    title="APEX - Analytics Engine for SCMS",
    description="AI-Powered Supply Chain Analytics and Intelligence Engine for SCMS.",
    version="1.0.0",
    docs_url=None,
    lifespan=lifespan,
)

cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
    "http://localhost:5001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3004",
    "http://127.0.0.1:5001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router)


@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "APEX Analytics Engine"}
