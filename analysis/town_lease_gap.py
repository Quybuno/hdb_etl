import os
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
from typing import Dict, Any, List

def run_q2_town_lease_gap(db_path: str) -> Dict[str, Any]:
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("""
        SELECT
            town,
            month,
            flat_type,
            block || '_' || street_name AS block_id,
            storey_mid,
            floor_area_sqm,
            remaining_lease_years,
            resale_price,
            ln(resale_price) AS log_price,
            CASE
                WHEN remaining_lease_years >= 55.0 AND remaining_lease_years < 65.0 THEN 1
                WHEN remaining_lease_years >= 70.0 AND remaining_lease_years < 80.0 THEN 0
                ELSE NULL
            END AS is_short_lease,
            CASE
                WHEN month <= '2022-12' THEN 'Period 1 (2017-2022)'
                ELSE 'Period 2 (2023-Present)'
            END AS period
        FROM main_marts.fct_resale_transaction
        WHERE (
            (remaining_lease_years >= 55.0 AND remaining_lease_years < 65.0) OR
            (remaining_lease_years >= 70.0 AND remaining_lease_years < 80.0)
        )
        AND floor_area_sqm > 0 AND resale_price > 0 AND storey_mid IS NOT NULL
    """).df()
    con.close()

    # Find towns that qualify (at least 200 in both short and ref groups for each period)
    towns = sorted(df["town"].unique())
    qualifying_towns = []

    for t in towns:
        tdf = df[df["town"] == t]
        p1 = tdf[tdf["period"] == "Period 1 (2017-2022)"]
        p2 = tdf[tdf["period"] == "Period 2 (2023-Present)"]

        p1_short = (p1["is_short_lease"] == 1).sum()
        p1_ref = (p1["is_short_lease"] == 0).sum()
        p2_short = (p2["is_short_lease"] == 1).sum()
        p2_ref = (p2["is_short_lease"] == 0).sum()

        if p1_short >= 200 and p1_ref >= 200 and p2_short >= 200 and p2_ref >= 200:
            qualifying_towns.append(t)

    results_rows = []
    gaps_p1 = {}
    gaps_p2 = {}

    HDB_MATURE_TOWNS = {
        'ANG MO KIO', 'BEDOK', 'BISHAN', 'BUKIT MERAH', 'BUKIT TIMAH',
        'CENTRAL AREA', 'CLEMENTI', 'GEYLANG', 'KALLANG/WHAMPOA',
        'MARINE PARADE', 'PASIR RIS', 'QUEENSTOWN', 'SERANGOON',
        'TAMPINES', 'TOA PAYOH'
    }

    for t in qualifying_towns:
        estate_type = 'Mature' if t in HDB_MATURE_TOWNS else 'Non-Mature'
        for p_name in ["Period 1 (2017-2022)", "Period 2 (2023-Present)"]:
            sub_df = df[(df["town"] == t) & (df["period"] == p_name)].copy()

            flat_dummies = pd.get_dummies(sub_df["flat_type"], prefix="flat", drop_first=True, dtype=float)
            month_dummies = pd.get_dummies(sub_df["month"], prefix="month", drop_first=True, dtype=float)

            X = pd.concat([
                pd.Series(1.0, index=sub_df.index, name="const"),
                sub_df[["is_short_lease", "floor_area_sqm", "storey_mid"]],
                flat_dummies,
                month_dummies
            ], axis=1)

            y = sub_df["log_price"]
            clusters = sub_df["block_id"]

            model = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': clusters})

            gap_coef = float(model.params["is_short_lease"])
            gap_se = float(model.bse["is_short_lease"])
            ci = model.conf_int().loc["is_short_lease"]
            p_val = float(model.pvalues["is_short_lease"])

            short_n = int((sub_df["is_short_lease"] == 1).sum())
            ref_n = int((sub_df["is_short_lease"] == 0).sum())

            if p_name == "Period 1 (2017-2022)":
                gaps_p1[t] = gap_coef
            else:
                gaps_p2[t] = gap_coef

            results_rows.append({
                "town": t,
                "estate_type": estate_type,
                "period": p_name,
                "short_lease_count": short_n,
                "ref_lease_count": ref_n,
                "lease_gap_coef": round(gap_coef, 4),
                "std_err": round(gap_se, 4),
                "ci_lower": round(float(ci[0]), 4),
                "ci_upper": round(float(ci[1]), 4),
                "p_value": round(p_val, 4),
                "pct_gap": round((np.exp(gap_coef) - 1.0) * 100.0, 2),
                "nobs": int(model.nobs),
                "rsquared": round(float(model.rsquared), 3)
            })

    # Evaluate criteria
    has_min_towns = len(qualifying_towns) >= 10
    spearman_corr = 0.0
    spearman_ok = False
    leave_one_out_results = []

    if has_min_towns:
        p1_series = [gaps_p1[t] for t in qualifying_towns]
        p2_series = [gaps_p2[t] for t in qualifying_towns]
        spearman_corr, _ = spearmanr(p1_series, p2_series)
        spearman_ok = (spearman_corr >= 0.60)

        # Leave-one-out sensitivity analysis (report only, does not alter locked outcome)
        for t in qualifying_towns:
            sub_towns = [x for x in qualifying_towns if x != t]
            s_p1 = [gaps_p1[x] for x in sub_towns]
            s_p2 = [gaps_p2[x] for x in sub_towns]
            rho, p = spearmanr(s_p1, s_p2)
            leave_one_out_results.append({
                "omitted_town": t,
                "estate_type": 'Mature' if t in HDB_MATURE_TOWNS else 'Non-Mature',
                "spearman_rho": round(float(rho), 4),
                "p_value": round(float(p), 4)
            })

    overall_passed = bool(has_min_towns and spearman_ok)

    return {
        "status": "PASS" if overall_passed else "FAIL",
        "qualifying_towns_count": len(qualifying_towns),
        "qualifying_towns": qualifying_towns,
        "criteria": {
            "min_qualifying_towns_ge_10": {
                "passed": bool(has_min_towns),
                "measured": len(qualifying_towns),
                "threshold": ">= 10 towns"
            },
            "spearman_rank_corr": {
                "passed": bool(spearman_ok),
                "measured": round(float(spearman_corr), 4),
                "threshold": ">= 0.60"
            }
        },
        "leave_one_out": leave_one_out_results,
        "dataframe": pd.DataFrame(results_rows)
    }

if __name__ == "__main__":
    res = run_q2_town_lease_gap("data/warehouse/warehouse_staging.duckdb")
    print("Q2 Status:", res["status"])
    print("Q2 Criteria:", res["criteria"])
    print("Qualifying Towns:", res["qualifying_towns_count"])

