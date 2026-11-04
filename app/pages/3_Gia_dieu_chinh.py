import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from db import query_df, get_latest_data_date

st.set_page_config(page_title="Chỉ số giá đã điều chỉnh", page_icon="📈", layout="wide")

latest_month = get_latest_data_date()
st.title("📈 Chỉ số Giá Thô vs Chỉ số Giá đã Kiểm soát (Hedonic Price Index)")
st.caption(f"Dữ liệu cập nhật lô đến tháng: **{latest_month}** | Năm gốc 2019 = 100 | Kiểm soát diện tích, tầng, khu, loại căn và thời hạn thuê")

st.markdown("""
**Câu hỏi phân tích chính (Q3):** Mức tăng giá bán lại trên thị trường thô khác gì mức tăng giá thực tế sau khi đã kiểm soát sự thay đổi thành phần căn hộ (căn mới hơn, diện tích lớn hơn, tầng cao hơn)?  
*(Năm gốc: 2019 = 100.0 điểm chỉ số).*
""")

try:
    df_idx = query_df("SELECT * FROM analytics.price_index ORDER BY segment, year;")
except Exception as e:
    st.error(f"Không thể đọc bảng `analytics.price_index`: {e}")
    st.stop()

if df_idx.empty:
    st.warning("Bảng `analytics.price_index` chưa có dữ liệu.")
    st.stop()

# Segment selector
available_segments = df_idx["segment"].unique().tolist()
selected_seg = st.selectbox("Chọn phân khúc hiển thị:", available_segments, index=0)

sub_df = df_idx[df_idx["segment"] == selected_seg].copy()

fig = go.Figure()

# Raw Index line
fig.add_trace(go.Scatter(
    x=sub_df["year"],
    y=sub_df["raw_price_index"],
    mode='lines+markers',
    name='Chỉ số giá thô (Trung vị thô)',
    line=dict(color='#d62728', width=3, dash='dot'),
    marker=dict(size=8)
))

# Hedonic Index line + CI
fig.add_trace(go.Scatter(
    x=sub_df["year"],
    y=sub_df["hedonic_price_index"],
    mode='lines+markers',
    name='Chỉ số Hedonic (Đã kiểm soát đặc điểm)',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8)
))

# Upper CI
fig.add_trace(go.Scatter(
    x=sub_df["year"],
    y=sub_df["hedonic_ci_upper"],
    mode='lines',
    line=dict(width=0),
    showlegend=False,
    name='95% CI trên'
))

# Lower CI with fill
fig.add_trace(go.Scatter(
    x=sub_df["year"],
    y=sub_df["hedonic_ci_lower"],
    mode='lines',
    line=dict(width=0),
    fill='tonexty',
    fillcolor='rgba(31, 119, 180, 0.2)',
    name='Khoảng tin cậy 95% Hedonic'
))

# Reference 100 line
fig.add_hline(y=100, line_dash="solid", line_color="gray", annotation_text="Gốc 2019 = 100")

fig.update_layout(
    title=f"So sánh Chỉ số Giá Thô và Chỉ số Giá Hedonic ({selected_seg})",
    xaxis_title="Năm giao dịch",
    yaxis_title="Điểm chỉ số (2019 = 100)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

st.plotly_chart(fig, use_container_width=True)

# Latest gap metric (Main full-year comparison: 2019 -> 2025)
full_year_row = sub_df[sub_df["year"] == 2025].iloc[0] if (sub_df["year"] == 2025).any() else sub_df.sort_values("year").iloc[-1]
latest_row = sub_df.sort_values("year").iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Tăng giá thô (2019 -> 2025: Năm đầy đủ)", f"+{full_year_row['raw_price_index'] - 100:.1f}%")
c2.metric("Tăng giá Hedonic (2019 -> 2025: Năm đầy đủ)", f"+{full_year_row['hedonic_price_index'] - 100:.1f}%")
c3.metric("Sai lệch thành phần năm 2025 (Thô - Hedonic)", f"{full_year_row['gap_raw_vs_hedonic']:+.2f} điểm")

st.caption(f"📌 **Dữ liệu năm 2026 (Đến hiện tại - 11 tháng):** Chỉ số giá thô đạt {latest_row['raw_price_index']:.2f} (+{latest_row['raw_price_index'] - 100:.2f}%), chỉ số Hedonic đạt {latest_row['hedonic_price_index']:.2f} (+{latest_row['hedonic_price_index'] - 100:.2f}%). Độ lệch: {latest_row['gap_raw_vs_hedonic']:+.2f} điểm.")

st.subheader("Bảng chi tiết theo năm")
st.dataframe(
    sub_df[["year", "transaction_count", "median_resale_price", "raw_price_index", "hedonic_price_index", "hedonic_ci_lower", "hedonic_ci_upper", "gap_raw_vs_hedonic"]].rename(columns={
        "year": "Năm",
        "transaction_count": "Số GD",
        "median_resale_price": "Trung vị giá (SGD)",
        "raw_price_index": "Chỉ số thô",
        "hedonic_price_index": "Chỉ số Hedonic",
        "hedonic_ci_lower": "95% CI dưới",
        "hedonic_ci_upper": "95% CI trên",
        "gap_raw_vs_hedonic": "Chênh lệch thô - hedonic"
    }),
    use_container_width=True
)

st.write("---")

st.info("""
**🎯 Quyết định hỗ trợ:**  
- Cho phép người theo dõi thị trường phân biệt rõ giữa mức tăng giá danh nghĩa thô và mức tăng giá thuần sau khi đã chuẩn hóa cơ cấu căn hộ.  
- Giúp tránh việc ngộ nhận thị trường tăng quá nóng hoặc chậm lại chỉ vì cơ cấu căn hộ giao dịch (diện tích, khoảng tầng, vị trí) thay đổi giữa các năm.
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- Chỉ số mô tả biến động danh nghĩa bằng SGD, chưa khấu trừ lạm phát chung của nền kinh tế (CPI).  
- Mô hình kiểm soát các biến quan sát được trong dữ liệu công khai (diện tích, tầng, khu, thời hạn thuê, loại căn); các yếu tố nội thất cao cấp của từng giao dịch cá biệt không nằm trong phạm vi kiểm soát.
""")

