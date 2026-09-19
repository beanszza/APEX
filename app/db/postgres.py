"""PostgreSQL database engine and storage for APEX analytics."""

import json
import logging
import time
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pg_engine: Engine | None = None

# In-memory TTL cache to replace Redis
_in_memory_cache: dict[str, tuple[float, str]] = {}


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


def ensure_analytics_table() -> None:
    """Ensures the analytics_documents table exists in scm_db without modifying any existing tables."""
    engine = get_pg_engine()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS analytics_documents (
        key VARCHAR(64) PRIMARY KEY,
        data JSONB NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        logger.info("Verified/created 'analytics_documents' table in PostgreSQL.")
    except Exception as ex:
        logger.error("Failed to ensure analytics_documents table: %s", ex)
        raise


def save_document(key: str, data: dict[str, Any] | str) -> None:
    """Upserts an analytics JSON document into PostgreSQL scm_db."""
    engine = get_pg_engine()
    if isinstance(data, str):
        data_str = data
    else:
        data_str = json.dumps(data, default=str)
    upsert_sql = """
    INSERT INTO analytics_documents (key, data, updated_at)
    VALUES (:key, CAST(:data AS jsonb), CURRENT_TIMESTAMP)
    ON CONFLICT (key) DO UPDATE
    SET data = EXCLUDED.data, updated_at = EXCLUDED.updated_at;
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(upsert_sql), {"key": key, "data": data_str})
        logger.debug("Successfully saved analytics document '%s' to PostgreSQL.", key)
    except Exception as ex:
        logger.error("Failed to save analytics document '%s' to PostgreSQL: %s", key, ex)
        raise


def load_document(key: str) -> dict[str, Any] | None:
    """Loads an analytics JSON document from PostgreSQL scm_db."""
    engine = get_pg_engine()
    select_sql = "SELECT data FROM analytics_documents WHERE key = :key LIMIT 1;"
    try:
        with engine.connect() as conn:
            result = conn.execute(text(select_sql), {"key": key}).fetchone()
            if result and result[0] is not None:
                val = result[0]
                if isinstance(val, str):
                    return json.loads(val)
                return val
            return None
    except Exception as ex:
        logger.warning("Failed to load analytics document '%s' from PostgreSQL: %s", key, ex)
        return None


def cache_get(key: str) -> str | None:
    """In-memory cache retrieval replacing Redis."""
    now = time.time()
    item = _in_memory_cache.get(key)
    if not item:
        return None
    expires_at, val = item
    if now > expires_at:
        _in_memory_cache.pop(key, None)
        return None
    return val


def cache_set(key: str, val: str, ttl_seconds: int = 86400) -> None:
    """In-memory cache storage replacing Redis."""
    _in_memory_cache[key] = (time.time() + ttl_seconds, val)
