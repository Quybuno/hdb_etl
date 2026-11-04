import os
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
from typing import Dict, Any, Tuple

def run_q1_lease_curve(db_path: str) -> Dict[str, Any]:
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("""
        SELECT
            transaction_sk,
            month,
            transaction_year,
            town,
            flat_type,
            block || '_' || street_name AS block_id,
            storey_mid,
            floor_area_sqm,
            remaining_lease_years,
            lease_band_5yr,
            resale_price,
            ln(resale_price) AS log_price,
            CASE
                WHEN month <= '2022-12' THEN 'Period 1 (2017-2022)'
                ELSE 'Period 2 (2023-Present)'
            END AS period
        FROM main_marts.fct_resale_transaction
        WHERE floor_area_sqm > 0 AND resale_price > 0 AND storey_mid IS NOT NULL
    """).df()
    con.close()

    eval_bands = ["50-54", "55-59", "60-64", "65-69", "75-79", "80-84", "85-89"]
    all_target_bands = ["<50"] + eval_bands + ["90+"]

    results_by_period = {}
    rows_to_save = []

    for period_name in ["Period 1 (2017-2022)", "Period 2 (2023-Present)"]:
        pdf = df[df["period"] == period_name].copy()

        # Check counts
        band_counts = pdf["lease_band_5yr"].value_counts().to_dict()

        # Prepare dummies with 70-74 as reference
        # One-hot encode lease_band_5yr
        band_dummies = pd.get_dummies(pdf["lease_band_5yr"], prefix="band", drop_first=False, dtype=float)
        # Drop reference band 70-74
        if "band_70-74" in band_dummies.columns:
            band_dummies = band_dummies.drop(columns=["band_70-74"])

        # Categorical controls
        town_dummies = pd.get_dummies(pdf["town"], prefix="town", drop_first=True, dtype=float)
        flat_dummies = pd.get_dummies(pdf["flat_type"], prefix="flat", drop_first=True, dtype=float)
        month_dummies = pd.get_dummies(pdf["month"], prefix="month", drop_first=True, dtype=float)

        X = pd.concat([
            pd.Series(1.0, index=pdf.index, name="const"),
            pdf[["floor_area_sqm", "storey_mid"]],
            band_dummies,
            town_dummies,
            flat_dummies,
            month_dummies
        ], axis=1)

        y = pdf["log_price"]
        clusters = pdf["block_id"]

        # Fit OLS with cluster-robust standard errors
        model = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': clusters})

        period_res = {
            "counts": band_counts,
            "coefs": {},
            "se": {},
            "pvalues": {},
            "ci_lower": {},
            "ci_upper": {},
            "nobs": int(model.nobs),
            "rsquared": float(model.rsquared)
        }

        # Reference band 70-74 has coef 0.0
        period_res["coefs"]["70-74"] = 0.0
        period_res["se"]["70-74"] = 0.0
        period_res["ci_lower"]["70-74"] = 0.0
        period_res["ci_upper"]["70-74"] = 0.0

        for b in all_target_bands:
            col_name = f"band_{b}"
            if col_name in model.params:
                c = float(model.params[col_name])
                se = float(model.bse[col_name])
                ci = model.conf_int().loc[col_name]
                period_res["coefs"][b] = c
                period_res["se"][b] = se
                period_res["pvalues"][b] = float(model.pvalues[col_name])
                period_res["ci_lower"][b] = float(ci[0])
                period_res["ci_upper"][b] = float(ci[1])

                rows_to_save.append({
                    "period": period_name,
                    "lease_band": b,
                    "transaction_count": int(band_counts.get(b, 0)),
                    "coef": round(c, 4),
                    "std_err": round(se, 4),
                    "ci_lower": round(float(ci[0]), 4),
                    "ci_upper": round(float(ci[1]), 4),
                    "pct_diff_vs_ref": round((np.exp(c) - 1.0) * 100.0, 2),
                    "is_reference": False
                })
            elif b == "70-74":
                rows_to_save.append({
                    "period": period_name,
                    "lease_band": "70-74",
                    "transaction_count": int(band_counts.get("70-74", 0)),
                    "coef": 0.0,
                    "std_err": 0.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "pct_diff_vs_ref": 0.0,
                    "is_reference": True
                })

        results_by_period[period_name] = period_res

    # Evaluate criteria
    p1 = results_by_period["Period 1 (2017-2022)"]
    p2 = results_by_period["Period 2 (2023-Present)"]

    # Criterion 1: Mọi nhóm từ 50-90 năm có ít nhất 1.000 giao dịch trong mỗi giai đoạn
    min_count_p1 = min(p1["counts"].get(b, 0) for b in eval_bands)
    min_count_p2 = min(p2["counts"].get(b, 0) for b in eval_bands)
    count_ok = (min_count_p1 >= 1000) and (min_count_p2 >= 1000)

    # Criterion 2: Spearman giữa hệ số hai giai đoạn >= 0.90
    coefs_p1 = [p1["coefs"][b] for b in eval_bands]
    coefs_p2 = [p2["coefs"][b] for b in eval_bands]
    spearman_corr, _ = spearmanr(coefs_p1, coefs_p2)
    spearman_ok = (spearman_corr >= 0.90)

    # Criterion 3: Sai khác tuyệt đối giữa hai giai đoạn <= 5 điểm phần trăm ở các nhóm từ 50-85 năm
    bands_50_85 = ["50-54", "55-59", "60-64", "65-69", "75-79", "80-84"]
    max_abs_diff = max(abs(p1["coefs"][b] - p2["coefs"][b]) for b in bands_50_85)
    diff_ok = (max_abs_diff <= 0.05)

    overall_passed = bool(count_ok and spearman_ok and diff_ok)

    summary = {
        "status": "PASS" if overall_passed else "FAIL",
        "criteria": {
            "min_transactions_ge_1000": {
                "passed": bool(count_ok),
                "measured_p1_min": min_count_p1,
                "measured_p2_min": min_count_p2,
                "threshold": ">= 1000 per band"
            },
            "spearman_rank_corr": {
                "passed": bool(spearman_ok),
                "measured": round(float(spearman_corr), 4),
                "threshold": ">= 0.90"
            },
            "max_abs_diff_50_85": {
                "passed": bool(diff_ok),
                "measured": round(float(max_abs_diff), 4),
                "threshold": "<= 0.05 (5 percentage points)"
            }
        },
        "details_by_period": results_by_period,
        "dataframe": pd.DataFrame(rows_to_save)
    }

    return summary

if __name__ == "__main__":
    res = run_q1_lease_curve("data/warehouse/warehouse_staging.duckdb")
    print("Q1 Status:", res["status"])
    print("Q1 Criteria:", res["criteria"])
