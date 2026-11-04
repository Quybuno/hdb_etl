import os
import sys
import time
import hashlib
import csv
import io
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pipeline.common.logger import setup_logger
from pipeline.common.retry import fetch_with_retry, HTTPForbiddenError
from pipeline.common.manifest import get_latest_manifest, write_manifest

def extract_hdb(run_id: str, run_date: str, config: Optional[Dict[str, Any]] = None, logger=None) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("extract_hdb")
    if config is None:
        with open("config/settings.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    started_at_utc = datetime.now(timezone.utc).isoformat()
    logger.info(f"Starting HDB extract for run_id={run_id}, run_date={run_date}")

    hdb_cfg = config["sources"]["hdb"]
    dataset_id = hdb_cfg["dataset_id"]
    base_url = hdb_cfg["base_url"].rstrip("/")
    timeout = config["network"]["timeout_seconds"]
    max_retries = config["network"]["max_retries"]
    backoff = config["network"]["backoff_seconds"]

    raw_dir = config["paths"]["raw_dir"]
    output_dir = os.path.join(raw_dir, "hdb_resale", f"run_date={run_date}", f"run_id={run_id}")
    os.makedirs(output_dir, exist_ok=True)

    initiate_url = f"{base_url}/{dataset_id}/initiate-download"
    poll_url = f"{base_url}/{dataset_id}/poll-download"

    try:
        r_init = fetch_with_retry(
            initiate_url,
            method="GET",
            timeout=timeout,
            max_retries=max_retries,
            backoff_seconds=backoff,
            logger=logger
        )
        logger.info(f"HDB initiate-download returned HTTP {r_init.status_code}")

        download_url = None
        poll_count = 0
        while poll_count < 15:
            poll_count += 1
            time.sleep(2)
            r_poll = fetch_with_retry(
                poll_url,
                method="GET",
                timeout=timeout,
                max_retries=max_retries,
                backoff_seconds=backoff,
                logger=logger
            )
            data_json = r_poll.json()
            data_obj = data_json.get("data") or {}
            status_val = data_obj.get("status")
            url_val = data_obj.get("url")

            if status_val == "DOWNLOAD_SUCCESS" or url_val:
                download_url = url_val
                logger.info(f"Download URL acquired on poll #{poll_count}")
                break

        if not download_url:
            raise RuntimeError("Failed to acquire download URL after polling.")

        # Download CSV
        logger.info("Downloading HDB resale CSV content...")
        r_dl = fetch_with_retry(
            download_url,
            method="GET",
            timeout=120,
            max_retries=max_retries,
            backoff_seconds=backoff,
            logger=logger
        )
        csv_bytes = r_dl.content
        sha256_hash = hashlib.sha256(csv_bytes).hexdigest()
        logger.info(f"Downloaded {len(csv_bytes)} bytes. SHA-256: {sha256_hash}")

        # Parse CSV header and count rows
        f_csv = io.StringIO(csv_bytes.decode("utf-8", errors="replace"))
        reader = csv.reader(f_csv)
        columns = next(reader)
        row_count = sum(1 for _ in reader)

        # Check latest manifest for deduplication
        latest_manifest = get_latest_manifest(raw_dir, "hdb_resale")
        target_csv_path = os.path.join(output_dir, "hdb_resale.csv")

        if latest_manifest and latest_manifest.get("sha256") == sha256_hash:
            logger.info("SHA-256 matches latest snapshot. Setting status to 'no_change' without duplicating CSV.")
            status = "no_change"
            saved_csv_path = None
        else:
            with open(target_csv_path, "wb") as f_out:
                f_out.write(csv_bytes)
            logger.info(f"Saved new raw CSV snapshot to {target_csv_path}")
            status = "success"
            saved_csv_path = target_csv_path

        finished_at_utc = datetime.now(timezone.utc).isoformat()

        manifest = {
            "run_id": run_id,
            "source": "hdb_resale",
            "dataset_id": dataset_id,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "http_status": 200,
            "row_count": row_count,
            "columns": columns,
            "sha256": sha256_hash,
            "status": status,
            "error": None
        }
        write_manifest(output_dir, manifest)
        logger.info(f"Manifest written for run_id={run_id}")

        return {
            "manifest": manifest,
            "csv_path": saved_csv_path,
            "output_dir": output_dir,
            "status": status
        }

    except Exception as e:
        logger.error(f"Error during HDB extract: {e}")
        finished_at_utc = datetime.now(timezone.utc).isoformat()
        manifest = {
            "run_id": run_id,
            "source": "hdb_resale",
            "dataset_id": dataset_id,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "http_status": 500,
            "row_count": 0,
            "columns": [],
            "sha256": "",
            "status": "failed",
            "error": str(e)
        }
        write_manifest(output_dir, manifest)
        raise e

if __name__ == "__main__":
    import uuid
    run_id = str(uuid.uuid4())
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    extract_hdb(run_id, run_date)

