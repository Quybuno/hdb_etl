import os
import sys
import uuid
import subprocess
from datetime import datetime, timezone
import yaml
import duckdb

# Ensure project root in pythonpath
sys.path.insert(0, os.path.abspath("."))

from pipeline.common.logger import setup_logger
from pipeline.extract_hdb import extract_hdb
from pipeline.extract_mrt import extract_mrt
from pipeline.extract_blocks import extract_blocks
from pipeline.load_raw import load_raw
from pipeline.quality_gate import run_quality_gate
from pipeline.publish import publish_warehouse
from analysis.run_analysis import run_all_analysis

def run_pipeline() -> int:
    logger = setup_logger("run_pipeline")
    run_id = str(uuid.uuid4())
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    logger.info(f"==================================================")
    logger.info(f"Starting HDB ELT Pipeline: run_id={run_id}, run_date={run_date}")
    logger.info(f"==================================================")

    with open("config/settings.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    staging_db = config["paths"]["staging_db"]
    prod_db = config["paths"]["prod_db"]

    try:
        # Step 1: Extract HDB Resale
        logger.info(">>> Step 1: Extract HDB Resale...")
        hdb_res = extract_hdb(run_id, run_date, config=config, logger=logger)
        logger.info(f"HDB extract status: {hdb_res['status']}")

        # Step 2: Extract MRT Exits
        logger.info(">>> Step 2: Extract MRT Exits...")
        mrt_res = extract_mrt(run_id, run_date, config=config, logger=logger)
        logger.info(f"MRT extract status: {mrt_res['manifest']['status']}, count={mrt_res['row_count']}")

        # Step 3: Extract & Geocode Block Coordinates
        logger.info(">>> Step 3: Check & Geocode Block Coordinates...")
        csv_for_blocks = hdb_res.get("csv_path")
        block_res = extract_blocks(hdb_csv_path=csv_for_blocks, config=config, logger=logger)
        logger.info(f"Block coordinates status: total={block_res['total_blocks']}, missing_checked={block_res['missing_checked']}")

        # Step 4: Load Raw into Staging DuckDB
        logger.info(">>> Step 4: Load Raw Data into warehouse_staging.duckdb...")
        load_res = load_raw(run_id, run_date, hdb_csv_path=csv_for_blocks, db_path=staging_db, config=config, logger=logger)
        logger.info(f"Load raw complete: HDB rows={load_res['hdb_rows']}, MRT rows={load_res['mrt_rows']}, Block rows={load_res['block_rows']}")

        # Step 5: Execute dbt Models
        logger.info(">>> Step 5: Run dbt build...")
        dbt_executable = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Packages", "PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0",
            "LocalCache", "local-packages", "Python312", "Scripts", "dbt.exe"
        )
        if not os.path.exists(dbt_executable):
            dbt_cmd = ["dbt", "build", "--profiles-dir", "."]
        else:
            dbt_cmd = [dbt_executable, "build", "--profiles-dir", "."]

        dbt_proc = subprocess.run(dbt_cmd, cwd="dbt_hdb", capture_output=True, text=True)
        if dbt_proc.returncode != 0:
            logger.error(f"dbt build failed with return code {dbt_proc.returncode}")
            logger.error(dbt_proc.stdout[-500:] if dbt_proc.stdout else "")
            logger.error(dbt_proc.stderr[-500:] if dbt_proc.stderr else "")
            return 1
        logger.info("dbt build completed successfully.")

        # Step 6: Run Econometric Analysis
        logger.info(">>> Step 6: Run Econometric Analysis...")
        analysis_res = run_all_analysis(db_path=staging_db, logger=logger)
        logger.info(f"Analysis completed: Q1={analysis_res['q1']['status']}, Q2={analysis_res['q2']['status']}, Q3={analysis_res['q3']['status']}")

        # Step 7: Run Quality Gate
        logger.info(">>> Step 7: Run Quality Gate...")
        qg_res = run_quality_gate(
            staging_db_path=staging_db,
            raw_csv_path=csv_for_blocks,
            prod_db_path=prod_db,
            logger=logger
        )
        logger.info(f"Quality Gate passed: {qg_res['passed']}")

        # Step 8: Atomic Publish
        logger.info(">>> Step 8: Publish to Production Warehouse...")
        published = publish_warehouse(
            staging_db_path=staging_db,
            prod_db_path=prod_db,
            quality_passed=qg_res["passed"],
            logger=logger
        )

        if not published:
            logger.error("Publish rejected. Pipeline finished with error.")
            return 1

        logger.info("==================================================")
        logger.info(f"HDB ELT Pipeline run_id={run_id} completed successfully!")
        logger.info("==================================================")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with unexpected exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(run_pipeline())
