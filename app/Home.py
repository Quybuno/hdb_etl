import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from db import query_df, get_latest_data_date

st.set_page_config(
    page_title="HDB Resale ELT & Phân tích Thời hạn thuê",
    page_icon="🏢",
    layout="wide"
)

latest_month = get_latest_data_date()

st.title("🏢 Thị trường Căn hộ HDB Singapore & Thời hạn Thuê còn lại")
st.caption(f"Dữ liệu cập nhật định kỳ dạng theo lô (Batch ELT) từ data.gov.sg | Dữ liệu mới nhất đến tháng: **{latest_month}** (Không phải hệ thống realtime)")

st.markdown("""
Hệ thống ELT và dashboard phân tích đề tài: **"Căn hộ có hạn dùng: Giá HDB Singapore thay đổi thế nào khi thời hạn thuê còn lại ngắn đi?"**  
Người mua căn hộ HDB không chỉ mua diện tích và vị trí mà còn mua số năm còn lại của hợp đồng thuê 99 năm. Dashboard cung cấp các công cụ trực quan hóa dựa trên dữ liệu giao dịch thực tế đã qua kiểm soát chất lượng nghiêm ngặt.
""")

st.write("---")

# Metrics row
try:
    kpi_df = query_df("""
        SELECT
            count(*) as total_transactions,
            median(resale_price) as overall_median_price,
            round(avg(floor_area_sqm), 1) as avg_area,
            round(median(remaining_lease_years), 1) as median_lease,
            count(distinct town) as total_towns,
            count(distinct block || '_' || street_name) as total_blocks
        FROM main_marts.fct_resale_transaction;
    """)

    recent_kpi = query_df("""
        SELECT
            count(*) as recent_tx,
            median(resale_price) as recent_median_price
        FROM main_marts.fct_resale_transaction
        WHERE month >= (
            SELECT strftime(max(strptime(month || '-01', '%Y-%m-%d')) - interval 11 month, '%Y-%m')
            FROM main_marts.fct_resale_transaction
        );
    """)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Tổng số giao dịch", f"{kpi_df['total_transactions'].iloc[0]:,}")
    col2.metric("Trung vị giá toàn kỳ", f"${kpi_df['overall_median_price'].iloc[0]:,.0f} SGD")
    col3.metric("Trung vị giá (12 tháng gần nhất)", f"${recent_kpi['recent_median_price'].iloc[0]:,.0f} SGD")
    col4.metric("Trung vị thời hạn còn lại", f"{kpi_df['median_lease'].iloc[0]} năm")
    col5.metric("Số khu vực / Số Block", f"{kpi_df['total_towns'].iloc[0]} khu / {kpi_df['total_blocks'].iloc[0]:,} block")

except Exception as e:
    st.error(f"Lỗi truy vấn dữ liệu: {e}")

st.write("---")

# Section 1: Trend over time
st.subheader("1. Xu hướng giao dịch và giá bán lại theo thời gian")

trend_df = query_df("""
    SELECT
        year_quarter,
        count(*) as tx_count,
        median(resale_price) as median_price,
        round(median(price_per_sqm), 0) as median_sqm_price
    FROM main_marts.fct_resale_transaction f
    JOIN main_marts.dim_month m ON f.month = m.month
    GROUP BY year_quarter
    ORDER BY year_quarter
""")

col_left, col_right = st.columns(2)

with col_left:
    fig_price = px.line(
        trend_df,
        x="year_quarter",
        y="median_price",
        title="Trung vị giá giao dịch theo quý (SGD)",
        markers=True,
        labels={"year_quarter": "Quý giao dịch", "median_price": "Trung vị giá (SGD)"}
    )
    fig_price.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_price, use_container_width=True)

with col_right:
    fig_vol = px.bar(
        trend_df,
        x="year_quarter",
        y="tx_count",
        title="Số lượng giao dịch bán lại theo quý",
        labels={"year_quarter": "Quý giao dịch", "tx_count": "Số lượng giao dịch"}
    )
    fig_vol.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_vol, use_container_width=True)

# Section 2: Distribution by Lease Band & Flat Type
st.subheader("2. Cơ cấu giao dịch theo nhóm thời hạn thuê và loại căn hộ")

col_d1, col_d2 = st.columns(2)

with col_d1:
    lease_dist = query_df("""
        SELECT
            lease_band_5yr,
            count(*) as tx_count,
            round(median(resale_price), 0) as median_price
        FROM main_marts.fct_resale_transaction
        GROUP BY lease_band_5yr
        ORDER BY lease_band_5yr
    """)
    fig_lease = px.bar(
        lease_dist,
        x="lease_band_5yr",
        y="tx_count",
        color="median_price",
        title="Số giao dịch theo nhóm thời hạn thuê (Màu biểu thị trung vị giá)",
        labels={"lease_band_5yr": "Nhóm thời hạn còn lại (năm)", "tx_count": "Số giao dịch", "median_price": "Trung vị giá (SGD)"},
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_lease, use_container_width=True)

with col_d2:
    flat_dist = query_df("""
        SELECT
            flat_type,
            count(*) as tx_count,
            round(median(resale_price), 0) as median_price
        FROM main_marts.fct_resale_transaction
        GROUP BY flat_type
        ORDER BY tx_count DESC
    """)
    fig_flat = px.pie(
        flat_dist,
        names="flat_type",
        values="tx_count",
        title="Tỷ trọng giao dịch theo loại căn hộ",
        hole=0.4
    )
    st.plotly_chart(fig_flat, use_container_width=True)

st.write("---")

# Decision Support & Limitations
st.info("""
**🎯 Quyết định hỗ trợ:**  
Trang tổng quan giúp người mua nhà và chuyên viên phân tích định vị mặt bằng chung của thị trường HDB: quy mô giao dịch hiện hành, phân bố các nhóm thời hạn thuê, và biến động trung vị giá qua các quý để có kỳ vọng ngân sách ban đầu hợp lý.
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- Dữ liệu dựa trên hợp đồng giao dịch đăng ký thành công tại HDB, không đại diện cho toàn bộ cung cầu chào bán.  
- Giá chưa điều chỉnh lạm phát và các yếu tố nội thất riêng lẻ của từng căn hộ.  
- Số liệu trung vị thô có thể bị ảnh hưởng bởi tỷ trọng căn hộ mới (MOP) bán ra trong từng thời kỳ. Không dùng để định giá một căn cụ thể.
""")

