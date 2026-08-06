"""PostgreSQL database engine for read-only analytics data extraction."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pg_engine: Engine | None = None


def get_pg_engine() -> Engine:
    global _pg_engine
    if _pg_engine is None:
        settings = get_settings()
        _pg_engine = create_engine(
            settings.postgres_connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _pg_engine


def close_pg() -> None:
    global _pg_engine
    if _pg_engine is not None:
        _pg_engine.dispose()
        _pg_engine = None
        logger.info("PostgreSQL engine disposed.")
