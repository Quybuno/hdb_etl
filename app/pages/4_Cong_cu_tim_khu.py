import streamlit as st
import plotly.express as px
import pandas as pd
from db import query_df, get_latest_data_date

st.set_page_config(page_title="Công cụ Tìm kiếm Khu vực", page_icon="🔍", layout="wide")

latest_month = get_latest_data_date()
st.title("🔍 Công cụ Hỗ trợ Tìm kiếm Khu vực & Block Phù hợp (12 Tháng Gần Nhất)")
st.caption(f"Dữ liệu cập nhật lô đến tháng: **{latest_month}** | Dựa trên giao dịch đã đăng ký chính thức trong 12 tháng gần nhất")

st.markdown("""
**Hỗ trợ người mua nhà (Q4):** Giúp người mua nhanh chóng thu hẹp danh sách các khu vực và block nhà có giao dịch thực tế phù hợp với khả năng tài chính và tiêu chí thời hạn thuê, cự ly MRT.
""")

st.warning("⚠️ **Lưu ý bắt buộc:** Kết quả mô tả giao dịch đã đăng ký gần đây, không phải định giá. Hệ thống không tạo điểm 'đáng mua' và không dự báo giá tương lai.")

try:
    df_search = query_df("SELECT * FROM main_marts.mart_budget_search;")
except Exception as e:
    st.error(f"Lỗi truy vấn `main_marts.mart_budget_search`: {e}")
    st.stop()

if df_search.empty:
    st.warning("Không có dữ liệu giao dịch trong cửa sổ 12 tháng gần nhất.")
    st.stop()

# Sidebar / Top filters
st.sidebar.header("Bộ lọc tìm kiếm")

# 1. Flat type
flat_types = sorted(df_search["flat_type"].unique().tolist())
selected_flat_types = st.sidebar.multiselect("Loại căn hộ:", flat_types, default=["4 ROOM", "3 ROOM"])

# 2. Budget range
min_p = int(df_search["min_resale_price"].min())
max_p = int(df_search["max_resale_price"].max())
budget_range = st.sidebar.slider(
    "Ngân sách (SGD):",
    min_value=200000,
    max_value=1500000,
    value=(350000, 750000),
    step=25000,
    format="$%d"
)

# 3. Minimum remaining lease
min_lease = st.sidebar.slider(
    "Thời hạn thuê tối thiểu (năm):",
    min_value=45,
    max_value=95,
    value=60,
    step=5
)

# 4. MRT distance band
mrt_bands = ["Tất cả", "< 400m", "400-799m", "800-1199m", ">= 1200m"]
selected_mrt_band = st.sidebar.selectbox("Cự ly đến ga MRT gần nhất:", mrt_bands, index=0)

# Apply filters
filtered = df_search.copy()

if selected_flat_types:
    filtered = filtered[filtered["flat_type"].isin(selected_flat_types)]

filtered = filtered[
    (filtered["median_resale_price"] >= budget_range[0]) &
    (filtered["median_resale_price"] <= budget_range[1]) &
    (filtered["avg_remaining_lease_years"] >= min_lease)
]

if selected_mrt_band != "Tất cả":
    filtered = filtered[filtered["mrt_band"] == selected_mrt_band]

# Filter out towns with under 10 transactions across the selection per spec
town_counts = filtered.groupby("town")["recent_transaction_count"].sum()
qualifying_towns_list = town_counts[town_counts >= 10].index.tolist()
filtered = filtered[filtered["town"].isin(qualifying_towns_list)]

total_qualifying_tx = filtered["recent_transaction_count"].sum()
total_qualifying_blocks = filtered[["block", "street_name"]].drop_duplicates().shape[0]

# Display metrics
m1, m2, m3 = st.columns(3)
m1.metric("Số giao dịch phù hợp tiêu chí", f"{total_qualifying_tx:,} giao dịch")
m2.metric("Số block nhà ở thỏa mãn", f"{total_qualifying_blocks:,} block")
m3.metric("Số khu vực hành chính", f"{len(qualifying_towns_list)} khu (có >= 10 giao dịch)")

st.write("---")

if filtered.empty:
    st.info("Không tìm thấy block hoặc khu vực nào thỏa mãn toàn bộ các tiêu chí trên. Vui lòng mở rộng ngân sách hoặc hạ yêu cầu thời hạn thuê.")
else:
    # Aggregated table by town
    st.subheader("1. Tổng hợp theo Khu vực hành chính")
    town_summary = filtered.groupby("town").agg(
        giao_dich=("recent_transaction_count", "sum"),
        trung_vi_gia=("median_resale_price", "median"),
        thoi_han_tb=("avg_remaining_lease_years", "mean"),
        dien_tich_tb=("avg_floor_area_sqm", "mean"),
        cu_ly_mrt_tb=("mrt_distance_m", "mean")
    ).reset_index().sort_values("giao_dich", ascending=False)

    st.dataframe(
        town_summary.rename(columns={
            "town": "Khu vực",
            "giao_dich": "Số giao dịch (12 tháng)",
            "trung_vi_gia": "Trung vị giá (SGD)",
            "thoi_han_tb": "Thời hạn TB (năm)",
            "dien_tich_tb": "Diện tích TB (m²)",
            "cu_ly_mrt_tb": "Cự ly MRT TB (m)"
        }).style.format({
            "Trung vị giá (SGD)": "${:,.0f}",
            "Thời hạn TB (năm)": "{:.1f}",
            "Diện tích TB (m²)": "{:.1f}",
            "Cự ly MRT TB (m)": "{:.0f}"
        }),
        use_container_width=True
    )

    # Price distribution chart
    st.subheader("2. Phân bố trung vị giá của các cụm block đủ điều kiện")
    fig_hist = px.histogram(
        filtered,
        x="median_resale_price",
        color="town",
        nbins=30,
        title="Phân bố trung vị giá theo từng khu vực (SGD)",
        labels={"median_resale_price": "Trung vị giá (SGD)", "count": "Số block"}
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Detailed table of blocks
    st.subheader("3. Danh sách cụm Block nhà ở chi tiết")
    display_blocks = filtered[[
        "town", "block", "street_name", "flat_type", "recent_transaction_count",
        "min_resale_price", "median_resale_price", "max_resale_price",
        "avg_remaining_lease_years", "nearest_mrt_station", "mrt_distance_m", "cbd_distance_km"
    ]].sort_values(["town", "median_resale_price"])

    st.dataframe(
        display_blocks.rename(columns={
            "town": "Khu vực",
            "block": "Block",
            "street_name": "Tên đường",
            "flat_type": "Loại căn",
            "recent_transaction_count": "Số GD",
            "min_resale_price": "Giá min (SGD)",
            "median_resale_price": "Giá trung vị (SGD)",
            "max_resale_price": "Giá max (SGD)",
            "avg_remaining_lease_years": "Thời hạn TB (năm)",
            "nearest_mrt_station": "Ga MRT gần nhất",
            "mrt_distance_m": "Cự ly MRT (m)",
            "cbd_distance_km": "Cự ly CBD (km)"
        }).style.format({
            "Giá min (SGD)": "${:,.0f}",
            "Giá trung vị (SGD)": "${:,.0f}",
            "Giá max (SGD)": "${:,.0f}",
            "Thời hạn TB (năm)": "{:.1f}",
            "Cự ly MRT (m)": "{:.0f}",
            "Cự ly CBD (km)": "{:.1f}"
        }),
        use_container_width=True
    )

st.write("---")

st.info("""
**🎯 Quyết định hỗ trợ:**  
Giúp người mua lập danh sách rút gọn (shortlist) các tòa nhà block và khu vực tiềm năng phù hợp với trần ngân sách vay vốn / vốn tự có và nhu cầu sinh hoạt thực tế (gần ga tàu điện ngầm, thời hạn thuê đủ điều kiện thế chấp hoặc bảo lưu giá trị).
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- Kết quả mô tả các giao dịch đã hoàn tất thủ tục sang tên đổi chủ trong 12 tháng gần nhất, không đảm bảo rằng hiện tại các block này đang có căn hộ rao bán cùng tầm giá.  
- Khoảng cách đến MRT và CBD được đo đạc theo đường thẳng (Haversine), có thể chênh lệch với khoảng cách đi bộ hoặc lộ trình giao thông thực tế.  
- Không tạo điểm số "đáng mua nhất" để tránh rủi ro định hướng sai lệch cho người dùng.
""")
