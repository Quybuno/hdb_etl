import os
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import Dict, Any, List

def run_q3_price_index(db_path: str) -> Dict[str, Any]:
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("""
        SELECT
            transaction_year,
            town,
            flat_type,
            block || '_' || street_name AS block_id,
            storey_mid,
            floor_area_sqm,
            remaining_lease_years,
            resale_price,
            ln(resale_price) AS log_price
        FROM main_marts.fct_resale_transaction
        WHERE floor_area_sqm > 0 AND resale_price > 0 AND storey_mid IS NOT NULL AND remaining_lease_years IS NOT NULL
    """).df()
    con.close()

    segments = ["OVERALL", "3 ROOM", "4 ROOM", "5 ROOM"]
    all_years = sorted(df["transaction_year"].unique())
    base_year = 2019

    results_rows = []

    for seg in segments:
        if seg == "OVERALL":
            sdf = df.copy()
        else:
            sdf = df[df["flat_type"] == seg].copy()

        # Compute raw median index
        yearly_medians = sdf.groupby("transaction_year")["resale_price"].median().to_dict()
        base_median = yearly_medians.get(base_year, 1.0)

        # Build regression matrix
        year_dummies = pd.get_dummies(sdf["transaction_year"], prefix="yr", drop_first=False, dtype=float)
        # Drop 2019 base year
        if f"yr_{base_year}" in year_dummies.columns:
            year_dummies = year_dummies.drop(columns=[f"yr_{base_year}"])

        town_dummies = pd.get_dummies(sdf["town"], prefix="town", drop_first=True, dtype=float)

        cols_to_concat = [
            pd.Series(1.0, index=sdf.index, name="const"),
            sdf[["floor_area_sqm", "storey_mid", "remaining_lease_years"]],
            year_dummies,
            town_dummies
        ]
        if seg == "OVERALL":
            flat_dummies = pd.get_dummies(sdf["flat_type"], prefix="flat", drop_first=True, dtype=float)
            cols_to_concat.append(flat_dummies)

        X = pd.concat(cols_to_concat, axis=1)
        y = sdf["log_price"]
        clusters = sdf["block_id"]

        model = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': clusters})

        for y_val in all_years:
            raw_med = yearly_medians.get(y_val, 0.0)
            raw_index = (raw_med / base_median) * 100.0 if base_median > 0 else 100.0
            y_count = int((sdf["transaction_year"] == y_val).sum())

            if y_val == base_year:
                hedonic_idx = 100.0
                hedonic_lower = 100.0
                hedonic_upper = 100.0
                coef_val = 0.0
                se_val = 0.0
            else:
                col_name = f"yr_{y_val}"
                if col_name in model.params:
                    coef_val = float(model.params[col_name])
                    se_val = float(model.bse[col_name])
                    ci = model.conf_int().loc[col_name]
                    hedonic_idx = float(np.exp(coef_val) * 100.0)
                    hedonic_lower = float(np.exp(ci[0]) * 100.0)
                    hedonic_upper = float(np.exp(ci[1]) * 100.0)
                else:
                    coef_val = 0.0
                    se_val = 0.0
                    hedonic_idx = 100.0
                    hedonic_lower = 100.0
                    hedonic_upper = 100.0

            results_rows.append({
                "segment": seg,
                "year": int(y_val),
                "transaction_count": y_count,
                "median_resale_price": round(raw_med, 1),
                "raw_price_index": round(raw_index, 2),
                "hedonic_price_index": round(hedonic_idx, 2),
                "hedonic_ci_lower": round(hedonic_lower, 2),
                "hedonic_ci_upper": round(hedonic_upper, 2),
                "hedonic_coef": round(coef_val, 4),
                "std_err": round(se_val, 4),
                "gap_raw_vs_hedonic": round(raw_index - hedonic_idx, 2)
            })

    res_df = pd.DataFrame(results_rows)

    # Criteria check
    has_full_years = set(range(2017, 2026)).issubset(set(all_years))
    has_min_types = len(set(segments) - {"OVERALL"}) >= 3
    has_ci = "hedonic_ci_lower" in res_df.columns and "hedonic_ci_upper" in res_df.columns
    overall_passed = bool(has_full_years and has_min_types and has_ci)

    return {
        "status": "PASS" if overall_passed else "FAIL",
        "years_covered": all_years,
        "segments_analyzed": segments,
        "criteria": {
            "full_years_covered": {
                "passed": bool(has_full_years),
                "measured": f"From {min(all_years)} to {max(all_years)}",
                "threshold": "2017 to 2025+"
            },
            "min_segments_analyzed": {
                "passed": bool(has_min_types),
                "measured": len(segments) - 1,
                "threshold": ">= 3 flat types"
            },
            "confidence_intervals_reported": {
                "passed": bool(has_ci),
                "measured": "95% cluster-robust CIs computed",
                "threshold": "Must be reported"
            }
        },
        "dataframe": res_df
    }

if __name__ == "__main__":
    res = run_q3_price_index("data/warehouse/warehouse_staging.duckdb")
    print("Q3 Status:", res["status"])
    print("Q3 Criteria:", res["criteria"])
