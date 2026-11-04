import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from db import query_df, get_latest_data_date

st.set_page_config(page_title="Đường cong thời hạn thuê", page_icon="📉", layout="wide")

latest_month = get_latest_data_date()
st.title("📉 Đường cong Giá theo Thời hạn Thuê còn lại (Lease Curve)")
st.caption(f"Dữ liệu cập nhật lô đến tháng: **{latest_month}** | Phân tích hồi quy Hedonic kiểm soát đặc điểm căn hộ và sai số gom cụm theo block")

st.markdown("""
**Câu hỏi phân tích chính (Q1):** Khi thời hạn thuê còn lại ngắn đi, giá căn hộ giảm theo đường cong nào sau khi kiểm soát diện tích, tầng cao, loại căn, khu vực và thời điểm giao dịch?  
*(Nhóm tham chiếu: Căn hộ còn 70–74 năm thời hạn thuê).*
""")

try:
    df_curve = query_df("SELECT * FROM analytics.lease_curve ORDER BY period, lease_band;")
except Exception as e:
    st.error(f"Không thể đọc bảng `analytics.lease_curve`: {e}")
    st.stop()

if df_curve.empty:
    st.warning("Bảng `analytics.lease_curve` chưa có dữ liệu. Vui lòng chạy pipeline phân tích.")
    st.stop()

# Filter for plot (exclude or highlight 90+)
p1_df = df_curve[df_curve["period"].str.contains("2017-2022")].copy()
p2_df = df_curve[df_curve["period"].str.contains("2023")].copy()

# Sort bands chronologically
band_order = ["<50", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90+"]
p1_df["sort_key"] = p1_df["lease_band"].map(lambda x: band_order.index(x) if x in band_order else 99)
p2_df["sort_key"] = p2_df["lease_band"].map(lambda x: band_order.index(x) if x in band_order else 99)
p1_df = p1_df.sort_values("sort_key")
p2_df = p2_df.sort_values("sort_key")

fig = go.Figure()

# Period 1 line + error bars
fig.add_trace(go.Scatter(
    x=p1_df["lease_band"],
    y=p1_df["pct_diff_vs_ref"],
    error_y=dict(
        type='data',
        symmetric=False,
        array=(p1_df["ci_upper"] - p1_df["coef"]) * 100,
        arrayminus=(p1_df["coef"] - p1_df["ci_lower"]) * 100
    ),
    mode='lines+markers',
    name='Giai đoạn 1 (2017–2022)',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8)
))

# Period 2 line + error bars
fig.add_trace(go.Scatter(
    x=p2_df["lease_band"],
    y=p2_df["pct_diff_vs_ref"],
    error_y=dict(
        type='data',
        symmetric=False,
        array=(p2_df["ci_upper"] - p2_df["coef"]) * 100,
        arrayminus=(p2_df["coef"] - p2_df["ci_lower"]) * 100
    ),
    mode='lines+markers',
    name='Giai đoạn 2 (2023–Hiện tại)',
    line=dict(color='#ff7f0e', width=3, dash='dash'),
    marker=dict(size=8)
))

# Baseline horizontal line at 0%
fig.add_hline(y=0, line_dash="dot", line_color="gray", annotation_text="Tham chiếu (70-74 năm) = 0%")

fig.update_layout(
    title="Mức chênh lệch giá (%) so với nhóm tham chiếu 70-74 năm (Kèm khoảng tin cậy 95%)",
    xaxis_title="Nhóm thời hạn thuê còn lại (năm)",
    yaxis_title="Mức chênh lệch giá so với tham chiếu (%)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Bảng hệ số và số lượng giao dịch chi tiết")
st.dataframe(
    df_curve[["period", "lease_band", "transaction_count", "coef", "std_err", "ci_lower", "ci_upper", "pct_diff_vs_ref"]].rename(columns={
        "period": "Thời kỳ",
        "lease_band": "Nhóm thuê (năm)",
        "transaction_count": "Số giao dịch",
        "coef": "Hệ số log",
        "std_err": "Sai số cụm",
        "ci_lower": "95% CI dưới",
        "ci_upper": "95% CI trên",
        "pct_diff_vs_ref": "Chênh lệch giá (%)"
    }),
    use_container_width=True
)

st.error("""
**Kết luận kiểm định Q1:** **FAIL**  
- Mẫu giao dịch đạt chuẩn (P1 min = 5,879; P2 min = 2,591 giao dịch/nhóm; ngưỡng >= 1,000).  
- Thứ hạng Spearman đạt 1.0000 (tăng đơn điệu theo thời hạn thuê).  
- **Tiêu chí không đạt:** Độ chênh lệch giữa hai thời kỳ ở nhóm 80–84 năm đo được là **0.0828 log points** (tương đương **9.39 điểm phần trăm**), vượt ngưỡng khóa quy định là 0.05 (5 điểm phần trăm). Đường cong chiết khấu thời hạn thuê không giữ được tính ổn định qua thời gian. Không đưa ra giả định nguyên nhân khi không có dữ liệu chứng minh.
""")

st.write("---")

st.info("""
**🎯 Quyết định hỗ trợ:**  
- Cho phép người mua ước lượng được mức chiết khấu giá kỳ vọng khi mua các căn hộ có tuổi thọ cao (dưới 60 năm: chiết khấu từ -10% đến hơn -28% so với căn hộ 70-74 năm).
- Giúp người bán và môi giới đặt giá tham chiếu hợp lý tương ứng với niên hạn còn lại của hợp đồng thuê.
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- **Nhóm 90+ năm:** Căn hộ còn trên 90 năm thuê được phân tích và báo cáo riêng trong bảng số liệu do có thể bị ảnh hưởng đồng thời bởi các yếu tố mới xây.  
- **Tương quan không phải nhân quả:** Đường cong phản ánh mức giá giao dịch trên thị trường theo các biến kiểm soát, không chứng minh quan hệ nhân quả hay đo lường hiệu ứng khấu hao cơ học độc lập.
""")

