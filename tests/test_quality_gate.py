import os
import csv
import hashlib
import logging
import duckdb
import pytest
from pipeline.quality_gate import run_quality_gate
from pipeline.publish import publish_warehouse

def get_file_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def setup_dummy_duckdb(db_path, row_count=1000):
    con = duckdb.connect(db_path)
    con.execute("CREATE SCHEMA IF NOT EXISTS main_marts;")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    con.execute("""
        CREATE TABLE main_marts.fct_resale_transaction AS
        SELECT
            'sk_' || i AS transaction_sk,
            '2026-11' AS month,
            'BEDOK' AS town,
            '4 ROOM' AS flat_type,
            '101' AS block,
            'BEDOK RESERVOIR RD' AS street_name,
            500000.0 AS resale_price,
            90.0 AS floor_area_sqm,
            65.0 AS remaining_lease_years,
            5.0 AS storey_mid,
            1.35 AS block_latitude,
            103.85 AS block_longitude,
            1 AS occurrence_no
        FROM range(1, ?) t(i);
    """, [row_count + 1])
    con.execute("""
        CREATE TABLE raw.hdb_resale_snapshot AS
        SELECT
            'run_dummy' AS run_id,
            '2026-11-04' AS run_date,
            CURRENT_TIMESTAMP AS loaded_at_utc,
            row_number() over () AS source_row_number,
            month, town, flat_type, block, street_name,
            '04 TO 06' AS storey_range,
            cast(floor_area_sqm as varchar) AS floor_area_sqm,
            'Model A' AS flat_model,
            '1985' AS lease_commence_date,
            '65 years' AS remaining_lease,
            cast(resale_price as varchar) AS resale_price
        FROM main_marts.fct_resale_transaction;
    """)
    con.close()

def test_quality_gate_failure_on_missing_column(tmp_path):
    # Scenario 1: Missing column
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(staging_db, row_count=500)
    setup_dummy_duckdb(prod_db, row_count=500)

    # Corrupted CSV with missing columns
    bad_csv = str(tmp_path / "bad_cols.csv")
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "town", "resale_price"]) # Missing 8 columns
        writer.writerow(["2026-11", "BEDOK", "500000"])

    res = run_quality_gate(staging_db, raw_csv_path=bad_csv, prod_db_path=prod_db)
    assert res["passed"] is False, "Quality Gate should have failed due to missing columns"

    # Verify publish is blocked and prod_db is not overwritten (both mtime and SHA-256 hash)
    initial_prod_mtime = os.path.getmtime(prod_db)
    initial_prod_hash = get_file_sha256(prod_db)
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime
    assert get_file_sha256(prod_db) == initial_prod_hash, "prod_db hash must be identical after blocked publish"

def test_quality_gate_failure_on_empty_file(tmp_path):
    # Scenario 2: Empty file
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(staging_db, row_count=500)
    setup_dummy_duckdb(prod_db, row_count=500)

    empty_csv = str(tmp_path / "empty.csv")
    with open(empty_csv, "w", encoding="utf-8") as f:
        pass # 0 bytes

    res = run_quality_gate(staging_db, raw_csv_path=empty_csv, prod_db_path=prod_db)
    assert res["passed"] is False, "Quality Gate should have failed due to empty file"

    initial_prod_mtime = os.path.getmtime(prod_db)
    initial_prod_hash = get_file_sha256(prod_db)
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime
    assert get_file_sha256(prod_db) == initial_prod_hash, "prod_db hash must be identical after blocked publish"

def test_quality_gate_failure_on_row_count_drop(tmp_path):
    # Scenario 3: Significant drop in row count (> 1%)
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(prod_db, row_count=10000)
    setup_dummy_duckdb(staging_db, row_count=9000) # Dropped by 10% (> 1%)

    res = run_quality_gate(staging_db, prod_db_path=prod_db)
    assert res["passed"] is False, "Quality Gate should have failed due to row count drop > 1%"

    initial_prod_mtime = os.path.getmtime(prod_db)
    initial_prod_hash = get_file_sha256(prod_db)
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime
    assert get_file_sha256(prod_db) == initial_prod_hash, "prod_db hash must be identical after blocked publish"

def test_quality_gate_failure_preserves_file_hash(tmp_path):
    # Dedicated verification: SHA-256 hash before and after failed publish must match
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(staging_db, row_count=100)
    setup_dummy_duckdb(prod_db, row_count=100)

    hash_before = get_file_sha256(prod_db)
    # Attempt publish with quality_passed=False
    success = publish_warehouse(staging_db, prod_db, quality_passed=False)
    assert success is False
    hash_after = get_file_sha256(prod_db)

    assert hash_before == hash_after, f"Hash changed! Before: {hash_before}, After: {hash_after}"

def test_publish_behavior_when_read_connection_open_on_windows(tmp_path):
    # Test retry mechanism and safe fallback when a reader holds an open handle on Windows
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(staging_db, row_count=200)
    setup_dummy_duckdb(prod_db, row_count=100)

    hash_before = get_file_sha256(prod_db)

    # Simulate an active reader holding a file handle (e.g. active query)
    con_reader = duckdb.connect(prod_db, read_only=True)
    try:
        # On Windows, file replacement fails gracefully with retry, logs warning without killing reader,
        # preserves old warehouse and returns False (FAILED)
        success = publish_warehouse(staging_db, prod_db, quality_passed=True, max_retries=2, retry_delay_sec=0.1)
        assert success is False, "Publish should return False when all retries encounter file lock"

        # Confirm prod_db was not corrupted or modified
        assert get_file_sha256(prod_db) == hash_before, "prod_db hash must remain untouched after failed retry publish"
    finally:
        # Once the read connection is closed/released, publish succeeds cleanly
        con_reader.close()

    success = publish_warehouse(staging_db, prod_db, quality_passed=True)
    assert success is True, "Publish must succeed once read lock is released"
    # The new database hash should now reflect the updated staging database
    assert get_file_sha256(prod_db) != hash_before

def test_publish_retry_exhausted_persists_lock_and_fails(tmp_path):
    # Kiem tra giu file khoa qua toan bo so lan retry theo cau hinh:
    # 1. Giu file khoa qua so lan retry va kiem tra ket qua FAILED (False)
    # 2. Kiem tra warehouse duckdb giu nguyen ma hash SHA-256
    # 3. Kiem tra so lan retry dung theo cau hinh (max_retries = 5)
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(staging_db, row_count=300)
    setup_dummy_duckdb(prod_db, row_count=100)

    hash_before = get_file_sha256(prod_db)

    class ListLogHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []
        def emit(self, record):
            self.records.append(record)

    test_logger = logging.getLogger("test_publish_retry_exhausted")
    test_logger.setLevel(logging.DEBUG)
    handler = ListLogHandler()
    test_logger.addHandler(handler)

    configured_retries = 5
    con_reader = duckdb.connect(prod_db, read_only=True)
    try:
        # Giu file bi khoa qua toan bo so lan retry
        success = publish_warehouse(
            staging_db,
            prod_db,
            quality_passed=True,
            max_retries=configured_retries,
            retry_delay_sec=0.05,
            logger=test_logger
        )
        # 1. Kiem tra ket qua FAILED
        assert success is False, "Ket qua phai la FAILED (False) khi file bi khoa qua toan bo so lan retry"

        # 2. Kiem tra warehouse giu nguyen hash
        hash_after = get_file_sha256(prod_db)
        assert hash_after == hash_before, f"Ma hash cua warehouse da bi thay doi! Truoc: {hash_before}, Sau: {hash_after}"

        # 3. Kiem tra so lan retry dung theo cau hinh
        retry_warnings = [
            r.getMessage() for r in handler.records
            if "Publish attempt" in r.getMessage() and "failed due to file lock" in r.getMessage()
        ]
        assert len(retry_warnings) == configured_retries, (
            f"Ky vong {configured_retries} lan thu nhung ghi nhan {len(retry_warnings)} lan"
        )

        # Kiem tra co log ghi nhan trang thai publish FAILED
        failed_logs = [r.getMessage() for r in handler.records if "FAILED" in r.getMessage()]
        assert len(failed_logs) >= 1, "Phai ghi log thong bao FAILED khi het toan bo so lan retry"
    finally:
        con_reader.close()

