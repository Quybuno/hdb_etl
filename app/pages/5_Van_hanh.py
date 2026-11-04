import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from db import query_df, get_latest_data_date

st.set_page_config(page_title="Vận hành & Giám sát Pipeline", page_icon="⚙️", layout="wide")

latest_month = get_latest_data_date()
st.title("⚙️ Giám sát Vận hành & Chất lượng Dữ liệu (Operations & Quality Gate)")
st.caption(f"Trạng thái giám sát hệ thống ELT | Dữ liệu nguồn: data.gov.sg (HDB Resale & LTA MRT) | Độ mới: **{latest_month}**")

st.markdown("""
Trang vận hành cung cấp thông tin giám sát toàn diện về các phiên thực thi pipeline ELT, mức độ tươi mới của dữ liệu nguồn, biến động số dòng snapshot, và toàn bộ kết quả kiểm tra tại chốt kiểm soát chất lượng (Quality Gate).
""")

st.write("---")

# 1. Pipeline Runs & Freshness Status
st.subheader("1. Tình trạng chạy Pipeline và Độ mới Dữ liệu (Freshness)")

col1, col2 = st.columns(2)

with col1:
    try:
        fresh_df = query_df("SELECT * FROM main_ops.ops_source_freshness;")
        if not fresh_df.empty:
            row = fresh_df.iloc[0]
            st.metric("Tháng giao dịch mới nhất", str(row["latest_source_month"]))
            st.metric("Độ trễ lịch dương", f"{row['lag_calendar_months']} tháng (Ngưỡng <= 2 tháng)")
            st.metric("Trạng thái độ mới", str(row["freshness_status"]))
    except Exception as e:
        st.error(f"Lỗi đọc `main_ops.ops_source_freshness`: {e}")

with col2:
    try:
        run_df = query_df("SELECT * FROM main_ops.ops_pipeline_run ORDER BY loaded_at_utc DESC LIMIT 5;")
        st.write("**Lịch sử các phiên nạp dữ liệu gần nhất:**")
        st.dataframe(run_df.rename(columns={
            "run_id": "Mã phiên (run_id)",
            "run_date": "Ngày chạy",
            "loaded_at_utc": "Thời điểm nạp (UTC)",
            "total_rows_loaded": "Số dòng thô"
        }), use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi đọc `main_ops.ops_pipeline_run`: {e}")

st.write("---")

# 2. Quality Gate Results
st.subheader("2. Kết quả Kiểm định Chất lượng Dữ liệu (Quality Gate)")

try:
    q_df = query_df("SELECT * FROM ops.quality_result ORDER BY is_blocking DESC, check_name;")
    if not q_df.empty:
        blocking_fails = q_df[(q_df["is_blocking"] == True) & (q_df["passed"] == False)].shape[0]
        total_checks = q_df.shape[0]
        passed_checks = q_df[q_df["passed"] == True].shape[0]

        qc1, qc2, qc3 = st.columns(3)
        qc1.metric("Tổng số kiểm tra chất lượng", f"{total_checks} chỉ tiêu")
        qc2.metric("Số chỉ tiêu ĐẠT", f"{passed_checks} / {total_checks}")
        qc3.metric("Lỗi nghiêm trọng (Chặn Publish)", f"{blocking_fails} lỗi", delta_color="inverse")

        # Color-coded display table
        display_q = q_df.copy()
        display_q["Ket_qua"] = display_q["passed"].apply(lambda x: "✅ ĐẠT" if x else "❌ KHÔNG ĐẠT")
        display_q["Loai_kiem_tra"] = display_q["is_blocking"].apply(lambda x: "Chặn Publish" if x else "Cảnh báo")

        st.dataframe(
            display_q[["Loai_kiem_tra", "check_name", "Ket_qua", "measured_value", "threshold", "message"]].rename(columns={
                "Loai_kiem_tra": "Loại kiểm tra",
                "check_name": "Tên kiểm tra",
                "Ket_qua": "Kết quả",
                "measured_value": "Đo lường thực tế",
                "threshold": "Ngưỡng yêu cầu",
                "message": "Chi tiết"
            }),
            use_container_width=True
        )
    else:
        st.info("Chưa có kết quả ghi nhận trong bảng `ops.quality_result`.")
except Exception as e:
    st.error(f"Lỗi đọc `ops.quality_result`: {e}")

st.write("---")

# 3. Snapshot Deltas
st.subheader("3. Biến động Số dòng giữa các Snapshot (Snapshot Delta)")
try:
    delta_df = query_df("SELECT * FROM main_ops.ops_snapshot_delta ORDER BY loaded_at_utc DESC;")
    st.dataframe(
        delta_df.rename(columns={
            "run_id": "Mã phiên",
            "run_date": "Ngày chạy",
            "loaded_at_utc": "Thời điểm (UTC)",
            "row_count": "Số dòng snapshot",
            "prev_row_count": "Snapshot trước",
            "row_delta": "Chênh lệch dòng",
            "delta_pct": "Tỷ lệ tăng/giảm (%)"
        }),
        use_container_width=True
    )
except Exception as e:
    st.error(f"Lỗi đọc `main_ops.ops_snapshot_delta`: {e}")

st.write("---")

st.info("""
**🎯 Quyết định hỗ trợ:**  
Cung cấp góc nhìn vận hành minh bạch cho kỹ sư dữ liệu và quản trị viên hệ thống để giám sát độ tin cậy của quy trình ELT, phát hiện sớm các hiện tượng bất thường từ API nguồn (mất cột, trễ dữ liệu, giảm dòng đột ngột), và kiểm chứng rằng warehouse phục vụ dashboard luôn ở trạng thái lành mạnh nhất.
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- Hệ thống thực thi theo cơ chế lô (batch), không giám sát streaming theo từng giây.  
- Các chỉ số cảnh báo (như tỷ lệ dòng trùng lặp 0.13%) không chặn quy trình xuất bản nhưng đòi hỏi người phân tích lưu ý khi giải thích kết quả.
""")

