"""Database verification helper script for APEX."""

import sys
import logging
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.db.postgres import ensure_analytics_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ensure-dbs")


def verify_databases() -> bool:
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

    # 2. Verify analytics_documents table in PostgreSQL
    if all_ok:
        try:
            ensure_analytics_table()
            logger.info("✓ PostgreSQL analytics_documents table verified.")
        except Exception as e:
            logger.error("✗ Failed to verify analytics_documents table: %s", e)
            all_ok = False

    return all_ok


if __name__ == "__main__":
    ok = verify_databases()
    if not ok:
        logger.warning("PostgreSQL is unreachable. APEX features may degrade.")
        sys.exit(1)
    else:
        logger.info("PostgreSQL database dependency verified successfully.")
        sys.exit(0)
