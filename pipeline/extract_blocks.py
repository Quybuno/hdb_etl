import os
import sys
import time
import csv
import re
import yaml
import requests
from typing import Dict, Any, Optional, Set, Tuple

from pipeline.common.logger import setup_logger
from pipeline.common.retry import fetch_with_retry

def normalize_street(street: str) -> str:
    s = street.upper()
    replacements = [
        (r'\bBT\b', 'BUKIT'),
        (r'\bCTRL\b', 'CENTRAL'),
        (r'\bCL\b', 'CLOSE'),
        (r'\bCRES\b', 'CRESCENT'),
        (r'\bDR\b', 'DRIVE'),
        (r'\bGDNS\b', 'GARDENS'),
        (r'\bHTS\b', 'HEIGHTS'),
        (r'\bJLN\b', 'JALAN'),
        (r'\bLOR\b', 'LORONG'),
        (r'\bPK\b', 'PARK'),
        (r'\bPL\b', 'PLACE'),
        (r'\bRD\b', 'ROAD'),
        (r'\bST\b', 'STREET'),
        (r'\bTER\b', 'TERRACE'),
        (r'\bUPP\b', 'UPPER'),
        (r'\bAVE\b', 'AVENUE'),
        (r'\bSTN\b', 'STATION'),
    ]
    for pattern, rep in replacements:
        s = re.sub(pattern, rep, s)
    return s

def query_onemap(
    search_val: str,
    base_url: str,
    token: Optional[str] = None,
    timeout: int = 30,
    logger = None
) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": "hdb-elt-student-project/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = {
        "searchVal": search_val,
        "returnGeom": "Y",
        "getAddrDetails": "Y",
        "pageNum": "1"
    }
    try:
        r = fetch_with_retry(
            base_url,
            method="GET",
            params=params,
            headers=headers,
            timeout=timeout,
            logger=logger
        )
        data = r.json()
        if data.get("found", 0) > 0 and data.get("results"):
            return data["results"]
    except Exception as e:
        if logger:
            logger.warning(f"OneMap query error for '{search_val}': {e}")
    return None

def extract_blocks(
    hdb_csv_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    logger = None
) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("extract_blocks")
    if config is None:
        with open("config/settings.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    ref_dir = config["paths"]["reference_dir"]
    ref_file = os.path.join(ref_dir, "block_coordinates.csv")
    os.makedirs(ref_dir, exist_ok=True)

    existing_coords = {}
    if os.path.exists(ref_file):
        with open(ref_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row["block"].strip().upper(), row["street_name"].strip().upper())
                existing_coords[key] = row
        logger.info(f"Loaded {len(existing_coords)} existing block coordinates from {ref_file}")

    # If hdb_csv_path not provided, find the latest raw CSV
    if not hdb_csv_path:
        import glob
        pattern = os.path.join(config["paths"]["raw_dir"], "hdb_resale", "run_date=*", "run_id=*", "hdb_resale.csv")
        csvs = glob.glob(pattern)
        if csvs:
            csvs.sort(key=os.path.getmtime)
            hdb_csv_path = csvs[-1]

    needed_blocks: Set[Tuple[str, str]] = set()
    if hdb_csv_path and os.path.exists(hdb_csv_path):
        with open(hdb_csv_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                b = row.get("block", "").strip().upper()
                s = row.get("street_name", "").strip().upper()
                if b and s:
                    needed_blocks.add((b, s))
        logger.info(f"Found {len(needed_blocks)} unique block-street pairs in HDB resale CSV")

    missing = [b for b in needed_blocks if b not in existing_coords]
    logger.info(f"Blocks missing coordinates: {len(missing)}")

    onemap_url = config["sources"]["onemap"]["search_url"]
    rate_delay = config["sources"]["onemap"].get("rate_limit_delay_seconds", 1.0)
    onemap_token = os.environ.get("ONEMAP_TOKEN", None)

    new_records = []
    for idx, (block, street) in enumerate(missing):
        logger.info(f"Geocoding {idx+1}/{len(missing)}: Block {block} {street}")
        search_str = f"{block} {street}"
        results = query_onemap(search_str, onemap_url, token=onemap_token, logger=logger)
        time.sleep(rate_delay)

        matched = False
        if results:
            for item in results:
                item_blk = item.get("BLK_NO", "").strip().upper()
                item_road = item.get("ROAD_NAME", "").strip().upper()
                if item_blk == block:
                    rec = {
                        "block": block,
                        "street_name": street,
                        "lat": item.get("LATITUDE"),
                        "lon": item.get("LONGITUDE"),
                        "source": "onemap",
                        "matched_address": item.get("ADDRESS", ""),
                        "match": "exact"
                    }
                    new_records.append(rec)
                    existing_coords[(block, street)] = rec
                    matched = True
                    break

        if not matched:
            # Try normalized street
            norm_street = normalize_street(street)
            if norm_street != street:
                results_norm = query_onemap(f"{block} {norm_street}", onemap_url, token=onemap_token, logger=logger)
                time.sleep(rate_delay)
                if results_norm:
                    for item in results_norm:
                        if item.get("BLK_NO", "").strip().upper() == block:
                            rec = {
                                "block": block,
                                "street_name": street,
                                "lat": item.get("LATITUDE"),
                                "lon": item.get("LONGITUDE"),
                                "source": "onemap",
                                "matched_address": item.get("ADDRESS", ""),
                                "match": "expanded"
                            }
                            new_records.append(rec)
                            existing_coords[(block, street)] = rec
                            matched = True
                            break

        if not matched:
            rec = {
                "block": block,
                "street_name": street,
                "lat": None,
                "lon": None,
                "source": "onemap",
                "matched_address": "",
                "match": "not_found"
            }
            new_records.append(rec)
            existing_coords[(block, street)] = rec

    # Write back all existing + new coords to reference file
    fieldnames = ["block", "street_name", "lat", "lon", "source", "matched_address", "match"]
    with open(ref_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for k in sorted(existing_coords.keys()):
            writer.writerow(existing_coords[k])

    logger.info(f"Block coordinates updated. Total: {len(existing_coords)} records in {ref_file}")

    return {
        "total_blocks": len(existing_coords),
        "missing_checked": len(missing),
        "newly_added": len(new_records),
        "reference_file": ref_file
    }

if __name__ == "__main__":
    extract_blocks()
