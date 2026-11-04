import os
import csv
import duckdb
import pytest
from pipeline.quality_gate import run_quality_gate
from pipeline.publish import publish_warehouse

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

    # Verify publish is blocked and prod_db is not overwritten
    initial_prod_mtime = os.path.getmtime(prod_db)
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime

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
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime

def test_quality_gate_failure_on_row_count_drop(tmp_path):
    # Scenario 3: Significant drop in row count (> 1%)
    staging_db = str(tmp_path / "staging.duckdb")
    prod_db = str(tmp_path / "prod.duckdb")
    setup_dummy_duckdb(prod_db, row_count=10000)
    setup_dummy_duckdb(staging_db, row_count=9000) # Dropped by 10% (> 1%)

    res = run_quality_gate(staging_db, prod_db_path=prod_db)
    assert res["passed"] is False, "Quality Gate should have failed due to row count drop > 1%"

    initial_prod_mtime = os.path.getmtime(prod_db)
    pub_result = publish_warehouse(staging_db, prod_db, quality_passed=res["passed"])
    assert pub_result is False
    assert os.path.getmtime(prod_db) == initial_prod_mtime
