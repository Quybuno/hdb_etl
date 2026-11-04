import os
import json
import pytest
from pipeline.common.manifest import write_manifest, get_latest_manifest

def test_manifest_write_and_read(tmp_path):
    output_dir = tmp_path / "run_id=test_1"
    manifest_data = {
        "run_id": "test_1",
        "source": "hdb_resale",
        "dataset_id": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",
        "started_at_utc": "2026-11-04T12:00:00Z",
        "finished_at_utc": "2026-11-04T12:01:00Z",
        "http_status": 200,
        "row_count": 100,
        "columns": ["month", "town"],
        "sha256": "abcdef123456",
        "status": "success",
        "error": None
    }
    m_path = write_manifest(str(output_dir), manifest_data)
    assert os.path.exists(m_path)

    with open(m_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["run_id"] == "test_1"
    assert loaded["status"] == "success"
    assert loaded["sha256"] == "abcdef123456"
