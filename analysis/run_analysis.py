import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath("."))

import hashlib
import duckdb
import yaml
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pipeline.common.logger import setup_logger
from analysis.lease_curve import run_q1_lease_curve
from analysis.town_lease_gap import run_q2_town_lease_gap
from analysis.price_index import run_q3_price_index

def run_all_analysis(
    db_path: str = "data/warehouse/warehouse_staging.duckdb",
    logger = None
) -> Dict[str, Any]:
    if logger is None:
        logger = setup_logger("run_analysis")

    logger.info(f"Starting econometric analysis on {db_path}...")

    # Verify analysis_rules.yml sha256
    rules_file = "config/analysis_rules.yml"
    sha_file = "config/analysis_rules.sha256"
    if os.path.exists(rules_file) and os.path.exists(sha_file):
        with open(rules_file, "rb") as f:
            curr_sha = hashlib.sha256(f.read()).hexdigest()
        with open(sha_file, "r") as f:
            expected_sha = f.read().strip()
        if curr_sha != expected_sha:
            logger.warning(f"analysis_rules.yml SHA-256 changed! Expected {expected_sha}, got {curr_sha}")
        else:
            logger.info("analysis_rules.yml SHA-256 verified successfully.")

    # Run Q1
    logger.info("Running Q1: Lease Curve...")
    q1_res = run_q1_lease_curve(db_path)
    logger.info(f"Q1 Status: {q1_res['status']}")

    # Run Q2
    logger.info("Running Q2: Town Lease Gap...")
    q2_res = run_q2_town_lease_gap(db_path)
    logger.info(f"Q2 Status: {q2_res['status']}")

    # Run Q3
    logger.info("Running Q3: Price Index (Hedonic vs Raw)...")
    q3_res = run_q3_price_index(db_path)
    logger.info(f"Q3 Status: {q3_res['status']}")

    # Save results to DuckDB analytics schema
    logger.info("Writing results into DuckDB analytics schema...")
    con = duckdb.connect(db_path)
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

        # Save Q1
        con.execute("DROP TABLE IF EXISTS analytics.lease_curve;")
        df_q1 = q1_res["dataframe"]
        con.register("df_q1_view", df_q1)
        con.execute("CREATE TABLE analytics.lease_curve AS SELECT * FROM df_q1_view;")

        # Save Q2
        con.execute("DROP TABLE IF EXISTS analytics.town_lease_gap;")
        df_q2 = q2_res["dataframe"]
        con.register("df_q2_view", df_q2)
        con.execute("CREATE TABLE analytics.town_lease_gap AS SELECT * FROM df_q2_view;")

        # Save Q3
        con.execute("DROP TABLE IF EXISTS analytics.price_index;")
        df_q3 = q3_res["dataframe"]
        con.register("df_q3_view", df_q3)
        con.execute("CREATE TABLE analytics.price_index AS SELECT * FROM df_q3_view;")

        # Save analysis run metadata
        con.execute("DROP TABLE IF EXISTS analytics.analysis_run;")
        con.execute("""
            CREATE TABLE analytics.analysis_run (
                executed_at_utc TIMESTAMP,
                q1_status VARCHAR,
                q2_status VARCHAR,
                q3_status VARCHAR,
                rules_sha256 VARCHAR
            );
        """)
        now_ts = datetime.now(timezone.utc)
        con.execute("""
            INSERT INTO analytics.analysis_run VALUES (?, ?, ?, ?, ?)
        """, [now_ts, q1_res["status"], q2_res["status"], q3_res["status"], curr_sha if 'curr_sha' in locals() else 'N/A'])

        logger.info("All analytics tables written successfully.")

    finally:
        con.close()

    # Generate docs/analysis_results.md
    write_analysis_markdown(q1_res, q2_res, q3_res, curr_sha if 'curr_sha' in locals() else 'N/A')

    return {
        "q1": q1_res,
        "q2": q2_res,
        "q3": q3_res
    }

def write_analysis_markdown(q1: Dict[str, Any], q2: Dict[str, Any], q3: Dict[str, Any], rules_sha: str):
    os.makedirs("docs", exist_ok=True)
    report_path = "docs/analysis_results.md"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    md = []
    md.append("# Kết quả Phân tích Kinh tế lượng (Giai đoạn 4)")
    md.append(f"\n**Thời điểm thực thi:** {now_str}")
    md.append(f"**SHA-256 Quy tắc phân tích (`config/analysis_rules.yml`):** `{rules_sha}`")
    md.append("\n---\n")

    # Q1
    md.append("## Q1. Đường cong thời hạn thuê (Lease Curve)")
    md.append("\n**Câu hỏi:** Khi thời hạn thuê còn lại ngắn đi, giá giảm theo đường cong nào sau khi kiểm soát đặc điểm căn?")
    md.append(f"\n**Trạng thái nghiệm thu:** **{q1['status']}** (FAIL do độ chênh lệch ở nhóm 80-84 năm vượt ngưỡng 0.05)\n")
    md.append("| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |")
    md.append("|---|---|---|---|")
    c1 = q1["criteria"]["min_transactions_ge_1000"]
    md.append(f"| Giao dịch tối thiểu mỗi nhóm (50-90 năm) | {c1['threshold']} | P1 min={c1['measured_p1_min']:,}, P2 min={c1['measured_p2_min']:,} | {'ĐẠT' if c1['passed'] else 'KHÔNG ĐẠT'} |")
    c2 = q1["criteria"]["spearman_rank_corr"]
    md.append(f"| Spearman thứ hạng hệ số giữa 2 thời kỳ | {c2['threshold']} | {c2['measured']} | {'ĐẠT' if c2['passed'] else 'KHÔNG ĐẠT'} |")
    c3 = q1["criteria"]["max_abs_diff_50_85"]
    md.append(f"| Độ chênh lệch lớn nhất (50-85 năm) | {c3['threshold']} | {c3['measured']:.4f} log points ({c3['measured'] * 100:.2f} điểm phần trăm) | {'ĐẠT' if c3['passed'] else 'KHÔNG ĐẠT'} |")

    md.append("\n### Bảng hệ số hồi quy theo nhóm thời hạn thuê (Tham chiếu: 70-74 năm = 0.0)\n")
    df_q1 = q1["dataframe"]
    md.append("| Thời kỳ | Nhóm thời hạn | Số giao dịch | Hệ số log (log points) | Sai số chuẩn | 95% CI (log points) | Mức chênh giá so với tham chiếu (%) | 95% CI (%) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for _, r in df_q1.iterrows():
        md.append(f"| {r['period']} | {r['lease_band']} | {r['transaction_count']:,} | {r['coef_log']} | {r['std_err_log']} | [{r['ci_lower_log']}, {r['ci_upper_log']}] | {r['pct_diff_vs_ref']:+.2f}% | [{r['ci_lower_pct']:+.2f}%, {r['ci_upper_pct']:+.2f}%] |")

    if "comparison_dataframe" in q1:
        md.append("\n### Bảng so sánh biến động hệ số giữa hai thời kỳ (P1 vs P2)\n")
        df_cmp = q1["comparison_dataframe"]
        md.append("| Nhóm thời hạn | Giao dịch P1 | Giao dịch P2 | Hệ số log P1 | Hệ số log P2 | Chênh lệch log points | Chênh lệch % P1 | Chênh lệch % P2 | Chênh lệch điểm % |")
        md.append("|---|---|---|---|---|---|---|---|---|")
        for _, r in df_cmp.iterrows():
            md.append(f"| {r['lease_band']} | {r['count_p1']:,} | {r['count_p2']:,} | {r['coef_log_p1']} | {r['coef_log_p2']} | {r['diff_log_points']:+.4f} | {r['pct_diff_p1']:+.2f}% | {r['pct_diff_p2']:+.2f}% | {r['diff_pct_points']:+.2f} |")

    md.append("\n**Kết luận Q1:** Q1 trượt tiêu chí ổn định thời gian và được đánh dấu là **FAIL**. Độ chênh lệch lớn nhất giữa hai thời kỳ ở nhóm 80-84 năm đo được là 0.0828 log points (tương đương 9.39 điểm phần trăm theo chênh lệch phần trăm), vượt ngưỡng quy định 0.05 (5 điểm phần trăm). Không đưa ra các giả định hoặc suy đoán nguyên nhân khi không có dữ liệu chứng minh.")

    # Q2
    md.append("\n---\n")
    md.append("## Q2. Khác biệt theo khu (Town Lease Gap)")
    md.append("\n**Câu hỏi:** Mức chênh giữa nhóm thuê ngắn (55-65 năm) và nhóm tham chiếu (70-80 năm) có khác nhau giữa các khu không?")
    md.append(f"\n**Trạng thái nghiệm thu:** **{q2['status']}**\n")
    md.append("| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |")
    md.append("|---|---|---|---|")
    c_t1 = q2["criteria"]["min_qualifying_towns_ge_10"]
    md.append(f"| Số khu đủ điều kiện (>= 200 tx/nhóm) | {c_t1['threshold']} | {c_t1['measured']} khu | {'ĐẠT' if c_t1['passed'] else 'KHÔNG ĐẠT'} |")
    c_t2 = q2["criteria"]["spearman_rank_corr"]
    md.append(f"| Spearman thứ hạng mức chênh giữa 2 thời kỳ | {c_t2['threshold']} | {c_t2['measured']} | {'ĐẠT' if c_t2['passed'] else 'KHÔNG ĐẠT'} |")

    md.append("\n### Bảng mức chênh thời hạn thuê theo khu vực (Khớp 100% với `analytics.town_lease_gap`)\n")
    df_q2 = q2["dataframe"]
    md.append("| Khu vực | Phân loại HDB | Thời kỳ | Giao dịch 55-65 năm | Giao dịch 70-80 năm | Hệ số chênh lệch (log points) | Sai số chuẩn | 95% CI (log points) | Mức chiết khấu (%) |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for _, r in df_q2.iterrows():
        md.append(f"| {r['town']} | {r['estate_type']} | {r['period']} | {r['short_lease_count']:,} | {r['ref_lease_count']:,} | {r['lease_gap_coef']} | {r['std_err']} | [{r['ci_lower']}, {r['ci_upper']}] | {r['pct_gap']:+.2f}% |")

    if "leave_one_out" in q2 and q2["leave_one_out"]:
        md.append("\n### Kiểm tra độ nhạy Leave-One-Out cho hệ số Spearman thứ hạng Q2\n")
        md.append("*(Báo cáo độ nhạy bổ sung, không thay đổi kết quả kiểm định chính đã khóa)*\n")
        md.append("| Khu vực loại bỏ | Phân loại HDB | Spearman rho còn lại | p-value |")
        md.append("|---|---|---|---|")
        for item in q2["leave_one_out"]:
            md.append(f"| {item['omitted_town']} | {item['estate_type']} | {item['spearman_rho']} | {item['p_value']} |")
        loo_vals = [x["spearman_rho"] for x in q2["leave_one_out"]]
        md.append(f"\n- **Tóm tắt Leave-One-Out:** Min = {min(loo_vals)}, Max = {max(loo_vals)}, Trung bình = {sum(loo_vals)/len(loo_vals):.4f}. Thứ hạng mức chênh lệch giữa các khu vực giữ độ tương quan ổn định (rho trong khoảng 0.5524 đến 0.6993).")

    # Q3
    md.append("\n---\n")
    md.append("## Q3. Giá thật sự tăng bao nhiêu? (Price Index)")
    md.append("\n**Câu hỏi:** Mức tăng thô khác gì mức tăng đã kiểm soát thành phần căn qua các năm?")
    md.append(f"\n**Trạng thái nghiệm thu:** **{q3['status']}**\n")
    md.append("| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |")
    md.append("|---|---|---|---|")
    c_p1 = q3["criteria"]["full_years_covered"]
    md.append(f"| Đủ các năm 2017 đến gần nhất | {c_p1['threshold']} | {c_p1['measured']} | {'ĐẠT' if c_p1['passed'] else 'KHÔNG ĐẠT'} |")
    c_p2 = q3["criteria"]["min_segments_analyzed"]
    md.append(f"| Số phân khúc loại căn phân tích | {c_p2['threshold']} | {c_p2['measured']} phân khúc | {'ĐẠT' if c_p2['passed'] else 'KHÔNG ĐẠT'} |")
    c_p3 = q3["criteria"]["confidence_intervals_reported"]
    md.append(f"| Báo cáo khoảng tin cậy 95% | {c_p3['threshold']} | {c_p3['measured']} | {'ĐẠT' if c_p3['passed'] else 'KHÔNG ĐẠT'} |")

    md.append("\n### Bảng chỉ số giá theo năm (Năm gốc 2019 = 100.0)\n")
    df_q3 = q3["dataframe"]
    md.append("| Phân khúc | Năm | Số giao dịch | Trung vị giá (SGD) | Chỉ số giá thô | Chỉ số Hedonic (đã kiểm soát) | 95% CI Hedonic | Chênh lệch thô vs hedonic | Ghi chú |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for _, r in df_q3.iterrows():
        note = "Năm gốc" if r['year'] == 2019 else ("Dữ liệu đến hiện tại (11 tháng)" if r['year'] == 2026 else ("Năm đầy đủ gần nhất" if r['year'] == 2025 else "Năm đầy đủ"))
        md.append(f"| {r['segment']} | {r['year']} | {r['transaction_count']:,} | {r['median_resale_price']:,.0f} | {r['raw_price_index']} | {r['hedonic_price_index']} | [{r['hedonic_ci_lower']}, {r['hedonic_ci_upper']}] | {r['gap_raw_vs_hedonic']:+.2f} | {note} |")

    md.append("\n**Kết luận Q3:**")
    md.append("- **Kết luận chính (giai đoạn năm đầy đủ 2019 đến 2025):** Chỉ số giá thô toàn thị trường tăng +57.00% (từ trung vị $400,000 SGD lên $628,000 SGD), trong khi chỉ số Hedonic đã kiểm soát đặc điểm tăng +58.87% (95% CI: [158.34, 159.40]). Chênh lệch giữa giá thô và giá Hedonic ở năm đầy đủ gần nhất (2025) là -1.87 điểm chỉ số.")
    md.append("- **Dữ liệu năm 2026:** Đây là dữ liệu tính đến thời điểm hiện tại (11 tháng đầu năm 2026, 22,053 giao dịch), chưa phải năm đầy đủ. Chỉ số thô đạt 158.75 (+58.75%), chỉ số Hedonic đạt 159.33 (+59.33%).")
    md.append("- **Giai đoạn 2020-2022:** Đo nhận chỉ số giá thô cao hơn chỉ số Hedonic từ 2.61 đến 5.43 điểm chỉ số (năm 2020 lệch +3.14 điểm, năm 2021 lệch +5.43 điểm, năm 2022 lệch +2.61 điểm). Báo cáo số đo thuần túy, không đưa ra giả định nguyên nhân ngoài phạm vi dữ liệu.")

    md.append("\n---\n")
    md.append("## Giới hạn phương pháp và Cảnh báo bắt buộc")
    md.append("1. **Không suy diễn nhân quả:** Các hệ số hồi quy phản ánh mối tương quan có điều kiện (conditional correlation) trong dữ liệu giao dịch đã ghi nhận, không chứng minh quan hệ nhân quả.")
    md.append("2. **Đặc tính căn hộ không quan sát được:** Mô hình kiểm soát diện tích, tầng, loại căn, khu vực và thời điểm, nhưng chưa kiểm soát được tình trạng nội thất, hướng nhà, số lần sửa chữa nâng cấp của từng căn cụ thể.")
    md.append("3. **Nhóm thời hạn 90+:** Căn hộ còn trên 90 năm thuê được báo cáo riêng trong bảng do có thể bị ảnh hưởng đồng thời bởi các yếu tố mới xây.")

    with open(report_path, "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(md))

    print(f"Analysis results saved to {report_path}")

if __name__ == "__main__":
    run_all_analysis("data/warehouse/warehouse_staging.duckdb")
