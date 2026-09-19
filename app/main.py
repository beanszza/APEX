"""APEX — Analytical Platform for Enterprise eXcellence Application Entry Point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.core.config import get_settings
from app.db.postgres import ensure_analytics_table, close_pg
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.rate_limiter import RateLimitMiddleware
from app.api.routes.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL analytics_documents table exists
    try:
        ensure_analytics_table()
    except Exception as ex:
        logger.warning("Notice: Could not verify analytics_documents table on startup (PostgreSQL might be starting up): %s", ex)

    start_scheduler()

    # Trigger background compilation on APEX startup to populate analytics
    try:
        from app.services.analytics_compiler import AnalyticsCompilerService
        compiler = AnalyticsCompilerService()
        await compiler.compile_all_analytics()
        logger.info("APEX initial analytics compilation complete on startup.")
    except Exception as ex:
        logger.warning("Notice: APEX startup analytics compilation skipped/failed: %s", ex)

    yield

    # Shutdown
    stop_scheduler()
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

settings = get_settings()
if settings.allowed_origins:
    for origin in settings.allowed_origins.split(","):
        stripped = origin.strip()
        if stripped and stripped not in cors_origins:
            cors_origins.append(stripped)

# Add Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Add CORS Middleware
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
    if not get_settings().is_development:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "APEX Analytics Engine"}
