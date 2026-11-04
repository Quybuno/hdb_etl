import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from db import query_df, get_latest_data_date

st.set_page_config(page_title="So sánh chênh lệch giá theo khu", page_icon="🗺️", layout="wide")

latest_month = get_latest_data_date()
st.title("🗺️ Chênh lệch Giá theo Thời hạn Thuê giữa các Khu vực (Town Lease Gap)")
st.caption(f"Dữ liệu cập nhật lô đến tháng: **{latest_month}** | So sánh nhóm thuê 55–65 năm với nhóm tham chiếu 70–80 năm")

st.markdown("""
**Câu hỏi phân tích chính (Q2):** Mức chiết khấu giữa căn hộ thời hạn thuê ngắn (55–65 năm) so với căn hộ tham chiếu (70–80 năm) có khác nhau giữa các khu vực hành chính không?  
*(Chỉ phân tích các khu vực có tối thiểu 200 giao dịch ở mỗi nhóm thời hạn cho cả hai thời kỳ, kiểm soát diện tích, tầng, loại căn và tháng).*
""")

try:
    df_gap = query_df("SELECT * FROM analytics.town_lease_gap ORDER BY town, period;")
except Exception as e:
    st.error(f"Không thể đọc bảng `analytics.town_lease_gap`: {e}")
    st.stop()

if df_gap.empty:
    st.warning("Bảng `analytics.town_lease_gap` chưa có dữ liệu.")
    st.stop()

# Interactive filter: Choose Period to view or compare both
period_choice = st.radio("Chọn thời kỳ hiển thị:", ["So sánh cả hai thời kỳ", "Period 1 (2017-2022)", "Period 2 (2023-Present)"], horizontal=True)

if period_choice == "So sánh cả hai thời kỳ":
    fig = px.bar(
        df_gap,
        x="town",
        y="pct_gap",
        color="period",
        barmode="group",
        title="Mức chiết khấu giá của nhóm 55-65 năm so với nhóm 70-80 năm theo khu (%)",
        labels={"town": "Khu vực", "pct_gap": "Mức chiết khấu (%)", "period": "Thời kỳ"},
        color_discrete_map={"Period 1 (2017-2022)": "#1f77b4", "Period 2 (2023-Present)": "#ff7f0e"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
else:
    sub = df_gap[df_gap["period"] == period_choice].sort_values("pct_gap")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub["town"],
        y=sub["pct_gap"],
        error_y=dict(
            type='data',
            symmetric=False,
            array=((np.exp(sub["ci_upper"]) - 1.0) * 100 - sub["pct_gap"]).clip(lower=0),
            arrayminus=(sub["pct_gap"] - (np.exp(sub["ci_lower"]) - 1.0) * 100).clip(lower=0)
        ),
        marker_color="#2ca02c",
        name="Chiết khấu (%)"
    ))
    fig.update_layout(
        title=f"Mức chiết khấu giá theo khu vực trong {period_choice} (%)",
        xaxis_title="Khu vực",
        yaxis_title="Mức chiết khấu (%)",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Bảng dữ liệu chi tiết theo từng khu vực (Khớp 100% với analytics.town_lease_gap)")
display_cols = ["town", "estate_type", "period", "short_lease_count", "ref_lease_count", "lease_gap_coef", "ci_lower", "ci_upper", "pct_gap", "nobs"] if "estate_type" in df_gap.columns else ["town", "period", "short_lease_count", "ref_lease_count", "lease_gap_coef", "ci_lower", "ci_upper", "pct_gap", "nobs"]
st.dataframe(
    df_gap[display_cols].rename(columns={
        "town": "Khu vực",
        "estate_type": "Phân loại HDB",
        "period": "Thời kỳ",
        "short_lease_count": "Số GD (55-65 năm)",
        "ref_lease_count": "Số GD (70-80 năm)",
        "lease_gap_coef": "Hệ số OLS",
        "ci_lower": "95% CI dưới",
        "ci_upper": "95% CI trên",
        "pct_gap": "Chiết khấu (%)",
        "nobs": "Tổng mẫu khu"
    }),
    use_container_width=True
)

st.caption("📌 **Kiểm tra độ nhạy Leave-One-Out:** Khi lần lượt loại bỏ từng khu vực trong 13 khu, hệ số tương quan hạng Spearman giữa hai thời kỳ dao động từ 0.5524 đến 0.6993 (trung bình 0.6192), xác nhận tính nhất quán của thứ hạng chiết khấu.")

st.write("---")

st.info("""
**🎯 Quyết định hỗ trợ:**  
- Giúp người mua nhận diện khu vực có mức chiết khấu thời hạn thuê rõ rệt: phần lớn các khu vực trưởng thành (như Toa Payoh, Ang Mo Kio, Geylang, Bukit Merah) có mức chiết khấu sâu từ -14% đến -24%, trong khi một số khu vực như Hougang, Jurong West, hoặc Tampines có mức chênh lệch dưới -8%.
- Giúp các tổ chức định chế tài chính xác định phân khúc cần đánh giá kỹ lưỡng giá trị tài sản bảo đảm khi thời hạn thuê ngắn đi.
""")

st.warning("""
**⚠️ Giới hạn bắt buộc:**  
- **Không xếp hạng "đáng mua":** Mức chiết khấu lớn tại một số khu vực không đồng nghĩa với việc khu đó "đáng mua hơn". Giá phản ánh tổng hòa của vị trí, cơ sở hạ tầng, mật độ dân cư và nhu cầu thực tế.  
- Chỉ bao gồm 13 khu vực có đủ thanh khoản giao dịch ở cả hai nhóm thời hạn và hai thời kỳ.
""")

