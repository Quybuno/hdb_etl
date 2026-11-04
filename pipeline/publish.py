import os
import shutil
import logging
from typing import Dict, Any, Optional

from pipeline.common.logger import setup_logger

def publish_warehouse(
    staging_db_path: str,
    prod_db_path: str,
    quality_passed: bool,
    logger = None
) -> bool:
    if logger is None:
        logger = setup_logger("publish")

    if not quality_passed:
        logger.error("Quality Gate failed! Refusing to publish to production warehouse.")
        logger.error(f"Production database at '{prod_db_path}' remains untouched.")
        return False

    if not os.path.exists(staging_db_path):
        logger.error(f"Staging database does not exist at '{staging_db_path}'")
        return False

    logger.info(f"Publishing staging database '{staging_db_path}' -> '{prod_db_path}' atomically...")
    os.makedirs(os.path.dirname(prod_db_path), exist_ok=True)

    tmp_publish_path = prod_db_path + ".tmp"
    if os.path.exists(tmp_publish_path):
        try:
            os.remove(tmp_publish_path)
        except Exception:
            pass

    try:
        # Copy staging file to tmp path
        shutil.copy2(staging_db_path, tmp_publish_path)
        # Atomic replace
        os.replace(tmp_publish_path, prod_db_path)
        logger.info(f"Successfully published production warehouse to '{prod_db_path}'")
        return True
    except Exception as e:
        logger.error(f"Atomic publish failed: {e}")
        if os.path.exists(tmp_publish_path):
            try:
                os.remove(tmp_publish_path)
            except Exception:
                pass
        raise e

if __name__ == "__main__":
    publish_warehouse("data/warehouse/warehouse_staging.duckdb", "data/warehouse/warehouse.duckdb", True)

