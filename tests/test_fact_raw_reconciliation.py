import os
import glob
import csv
import duckdb
import pytest

def test_fact_to_raw_20_rows_reconciliation():
    db_path = "data/warehouse/warehouse_staging.duckdb"
    assert os.path.exists(db_path), f"Staging database not found at {db_path}"

    csv_pattern = os.path.join("data", "raw", "hdb_resale", "run_date=*", "run_id=*", "hdb_resale.csv")
    csv_files = glob.glob(csv_pattern)
    assert csv_files, "No raw HDB resale CSV found"
    csv_files.sort(key=os.path.getmtime)
    latest_csv = csv_files[-1]

    con = duckdb.connect(db_path, read_only=True)
    # Sample 20 random rows from fact table
    sample_rows = con.execute("""
        SELECT
            source_row_number,
            month,
            town,
            flat_type,
            block,
            street_name,
            storey_range,
            floor_area_sqm,
            flat_model,
            lease_commence_year,
            resale_price,
            business_hash
        FROM main_marts.fct_resale_transaction
        USING SAMPLE 20 (reservoir, 42);
    """).fetchall()
    con.close()

    assert len(sample_rows) == 20, f"Expected 20 sample rows, got {len(sample_rows)}"

    # Read the full raw CSV into memory or index by line number
    with open(latest_csv, "r", encoding="utf-8", errors="replace") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    # Header is line 0. source_row_number 1 corresponds to reader[1].

    reconciled_count = 0
    for r in sample_rows:
        src_row_num = r[0]
        fact_month = r[1]
        fact_town = r[2]
        fact_flat_type = r[3]
        fact_block = r[4]
        fact_street = r[5]
        fact_storey = r[6]
        fact_floor_area = r[7]
        fact_model = r[8]
        fact_commence = r[9]
        fact_price = r[10]

        raw_line = reader[src_row_num]
        raw_dict = dict(zip(header, raw_line))

        # Check all attributes
        assert raw_dict["month"].strip() == fact_month
        assert raw_dict["town"].strip().upper() == fact_town
        assert raw_dict["flat_type"].strip().upper() == fact_flat_type
        assert raw_dict["block"].strip().upper() == fact_block
        assert raw_dict["street_name"].strip().upper() == fact_street
        assert raw_dict["storey_range"].strip() == fact_storey
        assert float(raw_dict["floor_area_sqm"].strip()) == pytest.approx(fact_floor_area)
        assert raw_dict["flat_model"].strip() == fact_model
        assert int(raw_dict["lease_commence_date"].strip()) == fact_commence
        assert float(raw_dict["resale_price"].strip()) == pytest.approx(fact_price)

        reconciled_count += 1

    assert reconciled_count == 20
    print(f"Successfully reconciled {reconciled_count}/20 rows between fact and raw CSV.")

if __name__ == "__main__":
    test_fact_to_raw_20_rows_reconciliation()
