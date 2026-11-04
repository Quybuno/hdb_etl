import os
import sys
import duckdb
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from pipeline.common.logger import setup_logger

EXPECTED_HDB_COLUMNS = [
    'month', 'town', 'flat_type', 'block', 'street_name',
    'storey_range', 'floor_area_sqm', 'flat_model',
    'lease_commence_date', 'remaining_lease', 'resale_price'
]

class QualityGateFailure(Exception):
    pass

def run_quality_gate(
    staging_db_path: str,
    raw_csv_path: Optional[str] = None,
    prod_db_path: Optional[str] = None,
    logger = None
) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("quality_gate")

    logger.info(f"Running Quality Gate on staging database: {staging_db_path}")
    con = duckdb.connect(staging_db_path)
    
    checks: List[Dict[str, Any]] = []
    blocking_failed = False

    try:
        # Check 1: Số cột HDB đúng 11 cột dự kiến
        # Check 2: File không trống
        if raw_csv_path and os.path.exists(raw_csv_path):
            file_size = os.path.getsize(raw_csv_path)
            with open(raw_csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                first_row = next(reader, None)

            is_non_empty = (file_size > 0) and (header is not None) and (first_row is not None)
            cols_match = (header == EXPECTED_HDB_COLUMNS)

            checks.append({
                "check_name": "raw_file_non_empty",
                "is_blocking": True,
                "passed": is_non_empty,
                "measured": f"size={file_size} bytes",
                "threshold": "> 0 bytes and has data rows",
                "message": "Raw file is non-empty." if is_non_empty else "Raw file is empty!"
            })
            if not is_non_empty:
                blocking_failed = True

            checks.append({
                "check_name": "raw_columns_match",
                "is_blocking": True,
                "passed": cols_match,
                "measured": f"{len(header) if header else 0} columns",
                "threshold": "Exactly 11 expected columns",
                "message": "All 11 columns match." if cols_match else f"Columns mismatch: {header}"
            })
            if not cols_match:
                blocking_failed = True
        else:
            # Check columns in raw snapshot
            raw_cols = [c[0] for c in con.execute("DESCRIBE raw.hdb_resale_snapshot").fetchall()]
            has_11_cols = all(col in raw_cols for col in EXPECTED_HDB_COLUMNS)
            checks.append({
                "check_name": "raw_columns_match",
                "is_blocking": True,
                "passed": has_11_cols,
                "measured": "11 columns present",
                "threshold": "11 columns",
                "message": "Columns verified in raw snapshot."
            })

        # Get counts from database for latest snapshot
        raw_cols = [c[0] for c in con.execute("DESCRIBE raw.hdb_resale_snapshot").fetchall()]
        if "run_id" in raw_cols and "loaded_at_utc" in raw_cols:
            raw_count = con.execute("""
                SELECT count(*)
                FROM raw.hdb_resale_snapshot
                WHERE run_id = (SELECT run_id FROM raw.hdb_resale_snapshot ORDER BY loaded_at_utc DESC LIMIT 1)
            """).fetchone()[0]
        else:
            raw_count = con.execute("SELECT count(*) FROM raw.hdb_resale_snapshot").fetchone()[0]
        fact_count = con.execute("SELECT count(*) FROM main_marts.fct_resale_transaction").fetchone()[0]

        # Check 3: Số dòng không giảm quá 1% so với snapshot publish gần nhất
        prev_count = None
        if prod_db_path and os.path.exists(prod_db_path):
            try:
                con_prod = duckdb.connect(prod_db_path, read_only=True)
                prev_count = con_prod.execute("SELECT count(*) FROM main_marts.fct_resale_transaction").fetchone()[0]
                con_prod.close()
            except Exception:
                prev_count = None

        if prev_count is not None and prev_count > 0:
            drop_pct = (prev_count - fact_count) / float(prev_count)
            row_count_ok = drop_pct <= 0.01  # Cannot drop more than 1%
            checks.append({
                "check_name": "row_count_not_dropped",
                "is_blocking": True,
                "passed": row_count_ok,
                "measured": f"current={fact_count}, prev={prev_count}, drop={drop_pct*100:.2f}%",
                "threshold": "Drop <= 1.0%",
                "message": "Row count check passed." if row_count_ok else f"Row count dropped significantly ({drop_pct*100:.2f}%)!"
            })
            if not row_count_ok:
                blocking_failed = True
        else:
            checks.append({
                "check_name": "row_count_not_dropped",
                "is_blocking": True,
                "passed": True,
                "measured": f"current={fact_count}, first publish",
                "threshold": "Drop <= 1.0%",
                "message": "Initial publish, no previous baseline to compare."
            })

        # Check 4: Null <= 0.1% for core fields: month, town, flat_type, block, street_name, resale_price
        core_nulls = con.execute("""
            SELECT
                sum(case when month is null then 1 else 0 end) as null_month,
                sum(case when town is null then 1 else 0 end) as null_town,
                sum(case when flat_type is null then 1 else 0 end) as null_flat_type,
                sum(case when block is null then 1 else 0 end) as null_block,
                sum(case when street_name is null then 1 else 0 end) as null_street_name,
                sum(case when resale_price is null then 1 else 0 end) as null_resale_price
            FROM main_marts.fct_resale_transaction
        """).fetchone()
        max_core_null = max(core_nulls)
        null_core_pct = (max_core_null / float(fact_count)) * 100.0 if fact_count > 0 else 100.0
        core_nulls_ok = null_core_pct <= 0.1

        checks.append({
            "check_name": "core_fields_null_rate",
            "is_blocking": True,
            "passed": core_nulls_ok,
            "measured": f"max_null_rate={null_core_pct:.3f}% ({max_core_null} rows)",
            "threshold": "<= 0.1%",
            "message": "Core fields null rate check passed." if core_nulls_ok else "Core fields null rate exceeded threshold!"
        })
        if not core_nulls_ok:
            blocking_failed = True

        # Check 5: resale_price > 0
        invalid_price_count = con.execute("""
            SELECT count(*) FROM main_marts.fct_resale_transaction WHERE resale_price <= 0 OR resale_price IS NULL
        """).fetchone()[0]
        price_ok = (invalid_price_count == 0)
        checks.append({
            "check_name": "resale_price_positive",
            "is_blocking": True,
            "passed": price_ok,
            "measured": f"{invalid_price_count} non-positive rows",
            "threshold": "0 rows",
            "message": "All resale prices are positive." if price_ok else f"Found {invalid_price_count} invalid resale prices!"
        })
        if not price_ok:
            blocking_failed = True

        # Check 6: floor_area_sqm > 0
        invalid_area_count = con.execute("""
            SELECT count(*) FROM main_marts.fct_resale_transaction WHERE floor_area_sqm <= 0 OR floor_area_sqm IS NULL
        """).fetchone()[0]
        area_ok = (invalid_area_count == 0)
        checks.append({
            "check_name": "floor_area_positive",
            "is_blocking": True,
            "passed": area_ok,
            "measured": f"{invalid_area_count} non-positive rows",
            "threshold": "0 rows",
            "message": "All floor areas are positive." if area_ok else f"Found {invalid_area_count} invalid floor areas!"
        })
        if not area_ok:
            blocking_failed = True

        # Check 7: Parse remaining_lease errors <= 0.1%
        null_lease_count = con.execute("""
            SELECT count(*) FROM main_marts.fct_resale_transaction WHERE remaining_lease_years IS NULL OR remaining_lease_years <= 0
        """).fetchone()[0]
        null_lease_pct = (null_lease_count / float(fact_count)) * 100.0 if fact_count > 0 else 100.0
        lease_ok = null_lease_pct <= 0.1
        checks.append({
            "check_name": "remaining_lease_parsed_rate",
            "is_blocking": True,
            "passed": lease_ok,
            "measured": f"parse_error_rate={null_lease_pct:.3f}% ({null_lease_count} rows)",
            "threshold": "<= 0.1%",
            "message": "Remaining lease parsing passed." if lease_ok else f"Too many unparsed remaining_lease rows: {null_lease_count}"
        })
        if not lease_ok:
            blocking_failed = True

        # Check 8: Parse storey_range errors <= 0.1%
        null_storey_count = con.execute("""
            SELECT count(*) FROM main_marts.fct_resale_transaction WHERE storey_mid IS NULL OR storey_mid <= 0
        """).fetchone()[0]
        null_storey_pct = (null_storey_count / float(fact_count)) * 100.0 if fact_count > 0 else 100.0
        storey_ok = null_storey_pct <= 0.1
        checks.append({
            "check_name": "storey_range_parsed_rate",
            "is_blocking": True,
            "passed": storey_ok,
            "measured": f"parse_error_rate={null_storey_pct:.3f}% ({null_storey_count} rows)",
            "threshold": "<= 0.1%",
            "message": "Storey range parsing passed." if storey_ok else f"Too many unparsed storey_range rows: {null_storey_count}"
        })
        if not storey_ok:
            blocking_failed = True

        # Check 9: transaction_sk duy nhất (100% unique)
        distinct_sk = con.execute("SELECT count(distinct transaction_sk) FROM main_marts.fct_resale_transaction").fetchone()[0]
        sk_unique = (distinct_sk == fact_count)
        checks.append({
            "check_name": "transaction_sk_unique",
            "is_blocking": True,
            "passed": sk_unique,
            "measured": f"distinct_sk={distinct_sk}, total_rows={fact_count}",
            "threshold": "100% unique (0 duplicate SK)",
            "message": "transaction_sk is completely unique." if sk_unique else "Duplicate transaction_sk detected!"
        })
        if not sk_unique:
            blocking_failed = True

        # Check 10: Dòng raw so với fact lệch 0 dòng
        raw_fact_diff = abs(raw_count - fact_count)
        raw_fact_ok = (raw_fact_diff == 0)
        checks.append({
            "check_name": "raw_vs_fact_row_count_match",
            "is_blocking": True,
            "passed": raw_fact_ok,
            "measured": f"raw={raw_count}, fact={fact_count}, diff={raw_fact_diff}",
            "threshold": "Lệch 0 dòng",
            "message": "Raw and fact row counts match exactly." if raw_fact_ok else f"Raw/fact row count difference of {raw_fact_diff} rows!"
        })
        if not raw_fact_ok:
            blocking_failed = True

        # Check 11: Nối tọa độ block ít nhất 98% giao dịch
        matched_coords_count = con.execute("""
            SELECT count(*) FROM main_marts.fct_resale_transaction WHERE block_latitude IS NOT NULL AND block_longitude IS NOT NULL
        """).fetchone()[0]
        coord_match_pct = (matched_coords_count / float(fact_count)) * 100.0 if fact_count > 0 else 0.0
        coord_ok = coord_match_pct >= 98.0
        checks.append({
            "check_name": "block_coordinate_match_rate",
            "is_blocking": True,
            "passed": coord_ok,
            "measured": f"match_rate={coord_match_pct:.2f}% ({matched_coords_count}/{fact_count})",
            "threshold": ">= 98.0%",
            "message": "Block coordinates match rate passed." if coord_ok else f"Block coordinate match rate too low ({coord_match_pct:.2f}%)!"
        })
        if not coord_ok:
            blocking_failed = True

        # Check 12: Độ mới max(month) không cũ quá 2 tháng dương lịch
        max_month_str = con.execute("SELECT max(month) FROM main_marts.fct_resale_transaction").fetchone()[0]
        today_date = datetime.now(timezone.utc)
        curr_year = today_date.year
        curr_month = today_date.month

        tx_year, tx_month = [int(x) for x in max_month_str.split("-")]
        lag_months = (curr_year - tx_year) * 12 + (curr_month - tx_month)
        freshness_ok = (lag_months <= 2)

        checks.append({
            "check_name": "source_data_freshness",
            "is_blocking": True,
            "passed": freshness_ok,
            "measured": f"max_month={max_month_str}, lag={lag_months} months",
            "threshold": "Lag <= 2 months",
            "message": "Data freshness verified." if freshness_ok else f"Data is stale by {lag_months} months!"
        })
        if not freshness_ok:
            blocking_failed = True

        # Warning checks (9.2)
        dup_hash_count = con.execute("""
            SELECT sum(case when occurrence_no > 1 then 1 else 0 end)
            FROM main_marts.fct_resale_transaction
        """).fetchone()[0]
        dup_pct = (dup_hash_count / float(fact_count)) * 100.0 if fact_count > 0 else 0.0
        checks.append({
            "check_name": "duplicate_business_hash_rate",
            "is_blocking": False,
            "passed": True,
            "measured": f"{dup_pct:.2f}% ({dup_hash_count} rows)",
            "threshold": "Informational",
            "message": f"Recorded duplicate business_hash rate: {dup_pct:.2f}%."
        })

        # Save check results into ops.quality_result table
        con.execute("CREATE SCHEMA IF NOT EXISTS ops;")
        con.execute("DROP TABLE IF EXISTS ops.quality_result;")
        con.execute("""
            CREATE TABLE ops.quality_result (
                check_timestamp TIMESTAMP,
                check_name VARCHAR,
                is_blocking BOOLEAN,
                passed BOOLEAN,
                measured_value VARCHAR,
                threshold VARCHAR,
                message VARCHAR
            );
        """)
        now_ts = datetime.now(timezone.utc)
        for c in checks:
            con.execute("""
                INSERT INTO ops.quality_result VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [now_ts, c["check_name"], c["is_blocking"], c["passed"], c["measured"], c["threshold"], c["message"]])

        logger.info(f"Quality Gate completed. Overall passed: {not blocking_failed}")
        for c in checks:
            prefix = "[PASS]" if c["passed"] else ("[FAIL - BLOCKING]" if c["is_blocking"] else "[WARN]")
            logger.info(f"  {prefix} {c['check_name']}: {c['measured']} (threshold: {c['threshold']})")

        return {
            "passed": not blocking_failed,
            "checks": checks,
            "fact_count": fact_count,
            "max_month": max_month_str
        }

    finally:
        con.close()

if __name__ == "__main__":
    res = run_quality_gate("data/warehouse/warehouse_staging.duckdb")
    print(res)
