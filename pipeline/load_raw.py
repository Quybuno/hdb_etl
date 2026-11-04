import os
import sys
import glob
import json
import duckdb
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pipeline.common.logger import setup_logger

def load_raw(
    run_id: str,
    run_date: str,
    hdb_csv_path: Optional[str] = None,
    db_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    logger = None
) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("load_raw")
    if config is None:
        with open("config/settings.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    if db_path is None:
        db_path = config["paths"]["staging_db"]

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    loaded_at_utc = datetime.now(timezone.utc).isoformat()
    logger.info(f"Loading raw data into DuckDB at {db_path} for run_id={run_id}")

    # If hdb_csv_path is not specified, find latest raw CSV
    if not hdb_csv_path:
        pattern = os.path.join(config["paths"]["raw_dir"], "hdb_resale", "run_date=*", "run_id=*", "hdb_resale.csv")
        csvs = glob.glob(pattern)
        if not csvs:
            raise FileNotFoundError("No raw HDB resale CSV found to load.")
        csvs.sort(key=os.path.getmtime)
        hdb_csv_path = csvs[-1]

    ref_dir = config["paths"]["reference_dir"]
    mrt_csv_path = os.path.join(ref_dir, "mrt_station_exits.csv")
    block_csv_path = os.path.join(ref_dir, "block_coordinates.csv")

    con = duckdb.connect(db_path)
    try:
        # Create raw schema
        con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

        # 1. Create and populate raw.hdb_resale_snapshot
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw.hdb_resale_snapshot (
                run_id VARCHAR,
                run_date VARCHAR,
                loaded_at_utc TIMESTAMP,
                source_row_number BIGINT,
                month VARCHAR,
                town VARCHAR,
                flat_type VARCHAR,
                block VARCHAR,
                street_name VARCHAR,
                storey_range VARCHAR,
                floor_area_sqm VARCHAR,
                flat_model VARCHAR,
                lease_commence_date VARCHAR,
                remaining_lease VARCHAR,
                resale_price VARCHAR
            );
        """)

        # Check if this run_id was already loaded to prevent duplicate insertion
        existing = con.execute("SELECT count(*) FROM raw.hdb_resale_snapshot WHERE run_id = ?", [run_id]).fetchone()[0]
        if existing > 0:
            logger.info(f"run_id={run_id} already exists in raw.hdb_resale_snapshot ({existing} rows). Skipping HDB insert.")
            hdb_inserted = 0
        else:
            logger.info(f"Inserting HDB resale snapshot from {hdb_csv_path}...")
            # Normalize path for DuckDB SQL
            norm_hdb_path = hdb_csv_path.replace("\\", "/")
            con.execute(f"""
                INSERT INTO raw.hdb_resale_snapshot
                SELECT
                    '{run_id}' AS run_id,
                    '{run_date}' AS run_date,
                    TIMESTAMP '{loaded_at_utc}' AS loaded_at_utc,
                    row_number() OVER () AS source_row_number,
                    cast("month" as varchar) as "month",
                    cast("town" as varchar) as "town",
                    cast("flat_type" as varchar) as "flat_type",
                    cast("block" as varchar) as "block",
                    cast("street_name" as varchar) as "street_name",
                    cast("storey_range" as varchar) as "storey_range",
                    cast("floor_area_sqm" as varchar) as "floor_area_sqm",
                    cast("flat_model" as varchar) as "flat_model",
                    cast("lease_commence_date" as varchar) as "lease_commence_date",
                    cast("remaining_lease" as varchar) as "remaining_lease",
                    cast("resale_price" as varchar) as "resale_price"
                FROM read_csv_auto('{norm_hdb_path}', all_varchar=true, header=true);
            """)
            hdb_inserted = con.execute("SELECT count(*) FROM raw.hdb_resale_snapshot WHERE run_id = ?", [run_id]).fetchone()[0]
            logger.info(f"Loaded {hdb_inserted} rows into raw.hdb_resale_snapshot.")

        # 2. Populate raw.mrt_station_exits
        con.execute("DROP TABLE IF EXISTS raw.mrt_station_exits;")
        con.execute("""
            CREATE TABLE raw.mrt_station_exits (
                station VARCHAR,
                exit_code VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            );
        """)
        if os.path.exists(mrt_csv_path):
            norm_mrt_path = mrt_csv_path.replace("\\", "/")
            con.execute(f"""
                INSERT INTO raw.mrt_station_exits
                SELECT station, exit_code, latitude, longitude
                FROM read_csv_auto('{norm_mrt_path}', header=true);
            """)
            mrt_count = con.execute("SELECT count(*) FROM raw.mrt_station_exits;").fetchone()[0]
            logger.info(f"Loaded {mrt_count} rows into raw.mrt_station_exits.")
        else:
            mrt_count = 0
            logger.warning(f"MRT CSV not found at {mrt_csv_path}")

        # 3. Populate raw.block_coordinates
        con.execute("DROP TABLE IF EXISTS raw.block_coordinates;")
        con.execute("""
            CREATE TABLE raw.block_coordinates (
                block VARCHAR,
                street_name VARCHAR,
                lat DOUBLE,
                lon DOUBLE,
                source VARCHAR,
                matched_address VARCHAR,
                match VARCHAR
            );
        """)
        if os.path.exists(block_csv_path):
            norm_blk_path = block_csv_path.replace("\\", "/")
            con.execute(f"""
                INSERT INTO raw.block_coordinates
                SELECT block, street_name, lat, lon, source, matched_address, match
                FROM read_csv_auto('{norm_blk_path}', header=true);
            """)
            blk_count = con.execute("SELECT count(*) FROM raw.block_coordinates;").fetchone()[0]
            logger.info(f"Loaded {blk_count} rows into raw.block_coordinates.")
        else:
            blk_count = 0
            logger.warning(f"Block coordinates CSV not found at {block_csv_path}")

        return {
            "status": "success",
            "run_id": run_id,
            "hdb_rows": hdb_inserted,
            "mrt_rows": mrt_count,
            "block_rows": blk_count
        }

    finally:
        con.close()

if __name__ == "__main__":
    import uuid
    run_id = str(uuid.uuid4())
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    load_raw(run_id, run_date)
