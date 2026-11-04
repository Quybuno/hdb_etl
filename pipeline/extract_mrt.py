import os
import sys
import time
import json
import csv
import hashlib
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pipeline.common.logger import setup_logger
from pipeline.common.retry import fetch_with_retry
from pipeline.common.manifest import get_latest_manifest, write_manifest

def extract_mrt(run_id: str, run_date: str, config: Optional[Dict[str, Any]] = None, logger=None) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("extract_mrt")
    if config is None:
        with open("config/settings.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    started_at_utc = datetime.now(timezone.utc).isoformat()
    logger.info(f"Starting MRT extract for run_id={run_id}, run_date={run_date}")

    mrt_cfg = config["sources"]["mrt"]
    dataset_id = mrt_cfg["dataset_id"]
    base_url = mrt_cfg["base_url"].rstrip("/")
    timeout = config["network"]["timeout_seconds"]
    max_retries = config["network"]["max_retries"]
    backoff = config["network"]["backoff_seconds"]

    raw_dir = config["paths"]["raw_dir"]
    output_dir = os.path.join(raw_dir, "mrt_exits", f"run_date={run_date}", f"run_id={run_id}")
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

        time.sleep(1)
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
        download_url = data_obj.get("url")

        if not download_url:
            raise RuntimeError("No download URL returned from MRT poll-download.")

        logger.info("Downloading MRT GeoJSON content...")
        r_dl = fetch_with_retry(
            download_url,
            method="GET",
            timeout=timeout,
            max_retries=max_retries,
            backoff_seconds=backoff,
            logger=logger
        )
        geojson_bytes = r_dl.content
        sha256_hash = hashlib.sha256(geojson_bytes).hexdigest()
        logger.info(f"Downloaded MRT GeoJSON: {len(geojson_bytes)} bytes, SHA-256: {sha256_hash}")

        # Save raw geojson
        target_geojson_path = os.path.join(output_dir, "mrt_exits.geojson")
        with open(target_geojson_path, "wb") as f_out:
            f_out.write(geojson_bytes)

        # Parse GeoJSON into reference CSV
        geojson_data = json.loads(geojson_bytes.decode("utf-8", errors="replace"))
        features = geojson_data.get("features", [])
        
        parsed_rows = []
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None])
            # GeoJSON coordinates are [longitude, latitude]
            lon = coords[0]
            lat = coords[1]
            
            # Find station name and exit code in properties
            # Common property names in LTA GeoJSON: STN_NAME, STATION_NAME, EXIT_CODE
            stn_name = props.get("STATION_NAME") or props.get("STN_NAME") or props.get("station_name") or ""
            exit_code = props.get("EXIT_CODE") or props.get("exit_code") or ""
            
            # Clean HTML description if stn_name is empty
            if not stn_name and "Description" in props:
                import re
                desc = props["Description"]
                m_stn = re.search(r'<th>STN_NAME<\/th>\s*<td>(.*?)<\/td>', desc)
                m_exit = re.search(r'<th>EXIT_CODE<\/th>\s*<td>(.*?)<\/td>', desc)
                if m_stn:
                    stn_name = m_stn.group(1).strip()
                if m_exit:
                    exit_code = m_exit.group(1).strip()

            parsed_rows.append({
                "station": str(stn_name).strip().upper(),
                "exit_code": str(exit_code).strip().upper(),
                "latitude": float(lat) if lat is not None else None,
                "longitude": float(lon) if lon is not None else None
            })

        # Save reference CSV
        ref_dir = config["paths"]["reference_dir"]
        os.makedirs(ref_dir, exist_ok=True)
        ref_csv_path = os.path.join(ref_dir, "mrt_station_exits.csv")
        with open(ref_csv_path, "w", newline="", encoding="utf-8") as f_ref:
            writer = csv.DictWriter(f_ref, fieldnames=["station", "exit_code", "latitude", "longitude"])
            writer.writeheader()
            writer.writerows(parsed_rows)
        logger.info(f"Parsed {len(parsed_rows)} MRT exits saved to {ref_csv_path}")

        finished_at_utc = datetime.now(timezone.utc).isoformat()
        manifest = {
            "run_id": run_id,
            "source": "mrt_exits",
            "dataset_id": dataset_id,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "http_status": 200,
            "row_count": len(parsed_rows),
            "columns": ["station", "exit_code", "latitude", "longitude"],
            "sha256": sha256_hash,
            "status": "success",
            "error": None
        }
        write_manifest(output_dir, manifest)
        return {
            "manifest": manifest,
            "geojson_path": target_geojson_path,
            "reference_csv": ref_csv_path,
            "row_count": len(parsed_rows)
        }

    except Exception as e:
        logger.error(f"Error during MRT extract: {e}")
        finished_at_utc = datetime.now(timezone.utc).isoformat()
        manifest = {
            "run_id": run_id,
            "source": "mrt_exits",
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
    extract_mrt(run_id, run_date)
