import os
import glob
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

def get_latest_manifest(raw_dir: str, source: str) -> Optional[Dict[str, Any]]:
    """Finds the most recent manifest for a given source."""
    pattern = os.path.join(raw_dir, source, "run_date=*", "run_id=*", "manifest.json")
    manifest_files = glob.glob(pattern)
    if not manifest_files:
        return None

    # Sort by file modification time or path
    manifest_files.sort(key=os.path.getmtime)
    latest_file = manifest_files[-1]
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def write_manifest(output_dir: str, manifest_data: Dict[str, Any]) -> str:
    """Writes the manifest.json file into the output directory."""
    os.makedirs(output_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    return manifest_path

