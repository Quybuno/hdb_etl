# Kết quả Phân tích Kinh tế lượng (Giai đoạn 4)

**Thời điểm thực thi:** 2026-11-04 10:12 UTC
**SHA-256 Quy tắc phân tích (`config/analysis_rules.yml`):** `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`

---

## Q1. Đường cong thời hạn thuê (Lease Curve)

**Câu hỏi:** Khi thời hạn thuê còn lại ngắn đi, giá giảm theo đường cong nào sau khi kiểm soát đặc điểm căn?

**Trạng thái nghiệm thu:** **FAIL** (FAIL do độ chênh lệch ở nhóm 80-84 năm vượt ngưỡng 0.05)

| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |
|---|---|---|---|
| Giao dịch tối thiểu mỗi nhóm (50-90 năm) | >= 1000 per band | P1 min=5,879, P2 min=2,591 | ĐẠT |
| Spearman thứ hạng hệ số giữa 2 thời kỳ | >= 0.90 | 1.0 | ĐẠT |
| Độ chênh lệch lớn nhất (50-85 năm) | <= 0.05 (5 percentage points) | 0.0828 log points (8.28 điểm phần trăm) | KHÔNG ĐẠT |

### Bảng hệ số hồi quy theo nhóm thời hạn thuê (Tham chiếu: 70-74 năm = 0.0)

| Thời kỳ | Nhóm thời hạn | Số giao dịch | Hệ số log (log points) | Sai số chuẩn | 95% CI (log points) | Mức chênh giá so với tham chiếu (%) | 95% CI (%) |
|---|---|---|---|---|---|---|---|
| Period 1 (2017-2022) | <50 | 2,779 | -0.3104 | 0.0085 | [-0.327, -0.2938] | -26.68% | [-27.89%, -25.46%] |
| Period 1 (2017-2022) | 50-54 | 6,242 | -0.2009 | 0.0073 | [-0.2152, -0.1866] | -18.20% | [-19.36%, -17.02%] |
| Period 1 (2017-2022) | 55-59 | 12,799 | -0.1237 | 0.0047 | [-0.1328, -0.1145] | -11.63% | [-12.44%, -10.82%] |
| Period 1 (2017-2022) | 60-64 | 19,303 | -0.035 | 0.0035 | [-0.0418, -0.0283] | -3.44% | [-4.09%, -2.79%] |
| Period 1 (2017-2022) | 65-69 | 19,622 | -0.0037 | 0.0029 | [-0.0093, 0.002] | -0.37% | [-0.93%, +0.20%] |
| Period 1 (2017-2022) | 70-74 | 11,369 | 0.0 | 0.0 | [0.0, 0.0] | +0.00% | [+0.00%, +0.00%] |
| Period 1 (2017-2022) | 75-79 | 18,278 | 0.049 | 0.0029 | [0.0432, 0.0547] | +5.02% | [+4.42%, +5.63%] |
| Period 1 (2017-2022) | 80-84 | 15,083 | 0.0845 | 0.0043 | [0.0762, 0.0929] | +8.82% | [+7.91%, +9.74%] |
| Period 1 (2017-2022) | 85-89 | 5,879 | 0.2026 | 0.0064 | [0.1901, 0.215] | +22.46% | [+20.94%, +23.99%] |
| Period 1 (2017-2022) | 90+ | 32,042 | 0.2603 | 0.0041 | [0.2522, 0.2684] | +29.74% | [+28.69%, +30.79%] |
| Period 2 (2023-Present) | <50 | 5,223 | -0.3327 | 0.0071 | [-0.3466, -0.3189] | -28.30% | [-29.29%, -27.30%] |
| Period 2 (2023-Present) | 50-54 | 8,254 | -0.2107 | 0.0046 | [-0.2197, -0.2018] | -19.00% | [-19.72%, -18.27%] |
| Period 2 (2023-Present) | 55-59 | 11,826 | -0.1017 | 0.0035 | [-0.1085, -0.0949] | -9.67% | [-10.28%, -9.06%] |
| Period 2 (2023-Present) | 60-64 | 13,070 | -0.0489 | 0.0028 | [-0.0544, -0.0434] | -4.77% | [-5.29%, -4.25%] |
| Period 2 (2023-Present) | 65-69 | 6,257 | -0.0448 | 0.0028 | [-0.0503, -0.0393] | -4.38% | [-4.90%, -3.85%] |
| Period 2 (2023-Present) | 70-74 | 11,945 | 0.0 | 0.0 | [0.0, 0.0] | +0.00% | [+0.00%, +0.00%] |
| Period 2 (2023-Present) | 75-79 | 9,239 | 0.0275 | 0.0033 | [0.0211, 0.034] | +2.79% | [+2.13%, +3.45%] |
| Period 2 (2023-Present) | 80-84 | 2,591 | 0.1673 | 0.0071 | [0.1535, 0.1812] | +18.21% | [+16.59%, +19.86%] |
| Period 2 (2023-Present) | 85-89 | 9,269 | 0.1813 | 0.0042 | [0.1731, 0.1895] | +19.88% | [+18.90%, +20.87%] |
| Period 2 (2023-Present) | 90+ | 23,049 | 0.2004 | 0.0035 | [0.1936, 0.2072] | +22.19% | [+21.36%, +23.02%] |

### Bảng so sánh biến động hệ số giữa hai thời kỳ (P1 vs P2)

| Nhóm thời hạn | Giao dịch P1 | Giao dịch P2 | Hệ số log P1 | Hệ số log P2 | Chênh lệch log points | Chênh lệch % P1 | Chênh lệch % P2 | Chênh lệch điểm % |
|---|---|---|---|---|---|---|---|---|
| <50 | 2,779 | 5,223 | -0.3104 | -0.3327 | -0.0224 | -26.68% | -28.30% | -1.62 |
| 50-54 | 6,242 | 8,254 | -0.2009 | -0.2107 | -0.0098 | -18.20% | -19.00% | -0.80 |
| 55-59 | 12,799 | 11,826 | -0.1237 | -0.1017 | +0.0220 | -11.63% | -9.67% | +1.96 |
| 60-64 | 19,303 | 13,070 | -0.035 | -0.0489 | -0.0139 | -3.44% | -4.77% | -1.33 |
| 65-69 | 19,622 | 6,257 | -0.0037 | -0.0448 | -0.0411 | -0.37% | -4.38% | -4.01 |
| 70-74 | 11,369 | 11,945 | 0.0 | 0.0 | +0.0000 | +0.00% | +0.00% | +0.00 |
| 75-79 | 18,278 | 9,239 | 0.049 | 0.0275 | -0.0215 | +5.02% | +2.79% | -2.23 |
| 80-84 | 15,083 | 2,591 | 0.0845 | 0.1673 | +0.0828 | +8.82% | +18.21% | +9.39 |
| 85-89 | 5,879 | 9,269 | 0.2026 | 0.1813 | -0.0213 | +22.46% | +19.88% | -2.58 |
| 90+ | 32,042 | 23,049 | 0.2603 | 0.2004 | -0.0600 | +29.74% | +22.19% | -7.55 |

**Kết luận Q1:** Q1 trượt tiêu chí ổn định thời gian và được đánh dấu là **FAIL**. Độ chênh lệch lớn nhất giữa hai thời kỳ ở nhóm 80-84 năm đo được là 0.0828 log points (tương đương 9.39 điểm phần trăm theo chênh lệch phần trăm), vượt ngưỡng quy định 0.05 (5 điểm phần trăm). Không đưa ra các giả định hoặc suy đoán nguyên nhân khi không có dữ liệu chứng minh.

---

## Q2. Khác biệt theo khu (Town Lease Gap)

**Câu hỏi:** Mức chênh giữa nhóm thuê ngắn (55-65 năm) và nhóm tham chiếu (70-80 năm) có khác nhau giữa các khu không?

**Trạng thái nghiệm thu:** **PASS**

| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |
|---|---|---|---|
| Số khu đủ điều kiện (>= 200 tx/nhóm) | >= 10 towns | 13 khu | ĐẠT |
| Spearman thứ hạng mức chênh giữa 2 thời kỳ | >= 0.60 | 0.6209 | ĐẠT |

### Bảng mức chênh thời hạn thuê theo khu vực (Khớp 100% với `analytics.town_lease_gap`)

| Khu vực | Phân loại HDB | Thời kỳ | Giao dịch 55-65 năm | Giao dịch 70-80 năm | Hệ số chênh lệch (log points) | Sai số chuẩn | 95% CI (log points) | Mức chiết khấu (%) |
|---|---|---|---|---|---|---|---|---|
| ANG MO KIO | Mature | Period 1 (2017-2022) | 4,557 | 216 | -0.1161 | 0.0217 | [-0.1588, -0.0735] | -10.97% |
| ANG MO KIO | Mature | Period 2 (2023-Present) | 925 | 217 | -0.2743 | 0.024 | [-0.3214, -0.2273] | -23.99% |
| BEDOK | Mature | Period 1 (2017-2022) | 4,831 | 714 | -0.1163 | 0.0103 | [-0.1365, -0.0962] | -10.98% |
| BEDOK | Mature | Period 2 (2023-Present) | 1,496 | 397 | -0.1469 | 0.0121 | [-0.1705, -0.1232] | -13.66% |
| BUKIT BATOK | Non-Mature | Period 1 (2017-2022) | 1,597 | 675 | -0.0856 | 0.0093 | [-0.1039, -0.0674] | -8.21% |
| BUKIT BATOK | Non-Mature | Period 2 (2023-Present) | 2,201 | 473 | -0.1034 | 0.0077 | [-0.1184, -0.0884] | -9.83% |
| BUKIT MERAH | Mature | Period 1 (2017-2022) | 1,418 | 456 | -0.1526 | 0.0145 | [-0.181, -0.1242] | -14.15% |
| BUKIT MERAH | Mature | Period 2 (2023-Present) | 430 | 748 | -0.199 | 0.0234 | [-0.2449, -0.153] | -18.04% |
| CHOA CHU KANG | Non-Mature | Period 1 (2017-2022) | 275 | 3,093 | -0.0895 | 0.0114 | [-0.1119, -0.0671] | -8.56% |
| CHOA CHU KANG | Non-Mature | Period 2 (2023-Present) | 417 | 1,665 | -0.0159 | 0.0066 | [-0.0289, -0.0029] | -1.58% |
| GEYLANG | Mature | Period 1 (2017-2022) | 1,300 | 293 | -0.2053 | 0.0343 | [-0.2725, -0.1382] | -18.56% |
| GEYLANG | Mature | Period 2 (2023-Present) | 718 | 222 | -0.2674 | 0.0278 | [-0.322, -0.2129] | -23.47% |
| HOUGANG | Non-Mature | Period 1 (2017-2022) | 1,827 | 1,744 | -0.034 | 0.0087 | [-0.0511, -0.0168] | -3.34% |
| HOUGANG | Non-Mature | Period 2 (2023-Present) | 2,180 | 939 | -0.0289 | 0.0072 | [-0.043, -0.0149] | -2.85% |
| JURONG EAST | Non-Mature | Period 1 (2017-2022) | 1,655 | 476 | -0.1899 | 0.0138 | [-0.217, -0.1628] | -17.30% |
| JURONG EAST | Non-Mature | Period 2 (2023-Present) | 1,133 | 366 | -0.1438 | 0.0107 | [-0.1647, -0.1229] | -13.39% |
| JURONG WEST | Non-Mature | Period 1 (2017-2022) | 1,662 | 2,778 | -0.0417 | 0.0099 | [-0.0611, -0.0222] | -4.08% |
| JURONG WEST | Non-Mature | Period 2 (2023-Present) | 1,808 | 2,219 | -0.0835 | 0.0061 | [-0.0956, -0.0715] | -8.01% |
| KALLANG/WHAMPOA | Mature | Period 1 (2017-2022) | 1,291 | 319 | -0.0851 | 0.0163 | [-0.1171, -0.0531] | -8.16% |
| KALLANG/WHAMPOA | Mature | Period 2 (2023-Present) | 650 | 363 | -0.1715 | 0.0185 | [-0.2077, -0.1352] | -15.76% |
| TAMPINES | Mature | Period 1 (2017-2022) | 2,633 | 2,667 | 0.0123 | 0.0066 | [-0.0006, 0.0253] | +1.24% |
| TAMPINES | Mature | Period 2 (2023-Present) | 3,688 | 854 | -0.0197 | 0.0051 | [-0.0297, -0.0097] | -1.95% |
| TOA PAYOH | Mature | Period 1 (2017-2022) | 809 | 598 | -0.2377 | 0.0182 | [-0.2735, -0.202] | -21.16% |
| TOA PAYOH | Mature | Period 2 (2023-Present) | 554 | 321 | -0.2556 | 0.0203 | [-0.2954, -0.2157] | -22.55% |
| WOODLANDS | Non-Mature | Period 1 (2017-2022) | 927 | 5,381 | -0.1352 | 0.0089 | [-0.1526, -0.1177] | -12.64% |
| WOODLANDS | Non-Mature | Period 2 (2023-Present) | 670 | 3,861 | -0.0643 | 0.0066 | [-0.0773, -0.0513] | -6.23% |

### Kiểm tra độ nhạy Leave-One-Out cho hệ số Spearman thứ hạng Q2

*(Báo cáo độ nhạy bổ sung, không thay đổi kết quả kiểm định chính đã khóa)*

| Khu vực loại bỏ | Phân loại HDB | Spearman rho còn lại | p-value |
|---|---|---|---|
| ANG MO KIO | Mature | 0.6993 | 0.0114 |
| BEDOK | Mature | 0.6434 | 0.024 |
| BUKIT BATOK | Non-Mature | 0.6154 | 0.0332 |
| BUKIT MERAH | Mature | 0.5804 | 0.0479 |
| CHOA CHU KANG | Non-Mature | 0.6573 | 0.0202 |
| GEYLANG | Mature | 0.5664 | 0.0548 |
| HOUGANG | Non-Mature | 0.5524 | 0.0625 |
| JURONG EAST | Non-Mature | 0.6364 | 0.0261 |
| JURONG WEST | Non-Mature | 0.5944 | 0.0415 |
| KALLANG/WHAMPOA | Mature | 0.6783 | 0.0153 |
| TAMPINES | Mature | 0.5524 | 0.0625 |
| TOA PAYOH | Mature | 0.5664 | 0.0548 |
| WOODLANDS | Non-Mature | 0.6853 | 0.0139 |

- **Tóm tắt Leave-One-Out:** Min = 0.5524, Max = 0.6993, Trung bình = 0.6175. Thứ hạng mức chênh lệch giữa các khu vực giữ độ tương quan ổn định (rho trong khoảng 0.5524 đến 0.6993).

---

## Q3. Giá thật sự tăng bao nhiêu? (Price Index)

**Câu hỏi:** Mức tăng thô khác gì mức tăng đã kiểm soát thành phần căn qua các năm?

**Trạng thái nghiệm thu:** **PASS**

| Tiêu chí kiểm định | Ngưỡng yêu cầu | Đo lường thực tế | Kết quả |
|---|---|---|---|
| Đủ các năm 2017 đến gần nhất | 2017 to 2025+ | From 2017 to 2026 | ĐẠT |
| Số phân khúc loại căn phân tích | >= 3 flat types | 3 phân khúc | ĐẠT |
| Báo cáo khoảng tin cậy 95% | Must be reported | 95% cluster-robust CIs computed | ĐẠT |

### Bảng chỉ số giá theo năm (Năm gốc 2019 = 100.0)

| Phân khúc | Năm | Số giao dịch | Trung vị giá (SGD) | Chỉ số giá thô | Chỉ số Hedonic (đã kiểm soát) | 95% CI Hedonic | Chênh lệch thô vs hedonic | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| OVERALL | 2017 | 20,509 | 410,000 | 102.5 | 101.4 | [101.08, 101.72] | +1.10 | Năm đầy đủ |
| OVERALL | 2018 | 21,561 | 408,000 | 102.0 | 100.11 | [99.83, 100.4] | +1.89 | Năm đầy đủ |
| OVERALL | 2019 | 22,186 | 400,000 | 100.0 | 100.0 | [100.0, 100.0] | +0.00 | Năm gốc |
| OVERALL | 2020 | 23,333 | 425,000 | 106.25 | 103.11 | [102.78, 103.43] | +3.14 | Năm đầy đủ |
| OVERALL | 2021 | 29,087 | 483,000 | 120.75 | 115.32 | [114.96, 115.67] | +5.43 | Năm đầy đủ |
| OVERALL | 2022 | 26,720 | 525,000 | 131.25 | 128.64 | [128.24, 129.05] | +2.61 | Năm đầy đủ |
| OVERALL | 2023 | 25,754 | 550,000 | 137.5 | 137.64 | [137.2, 138.08] | -0.14 | Năm đầy đủ |
| OVERALL | 2024 | 27,832 | 590,000 | 147.5 | 148.38 | [147.9, 148.87] | -0.88 | Năm đầy đủ |
| OVERALL | 2025 | 25,084 | 628,000 | 157.0 | 158.87 | [158.34, 159.4] | -1.87 | Năm đầy đủ gần nhất |
| OVERALL | 2026 | 22,053 | 635,000 | 158.75 | 159.33 | [158.8, 159.86] | -0.58 | Dữ liệu đến hiện tại (11 tháng) |
| 3 ROOM | 2017 | 5,047 | 301,888 | 106.67 | 106.33 | [105.77, 106.89] | +0.34 | Năm đầy đủ |
| 3 ROOM | 2018 | 5,119 | 290,000 | 102.47 | 102.33 | [101.85, 102.82] | +0.14 | Năm đầy đủ |
| 3 ROOM | 2019 | 5,423 | 283,000 | 100.0 | 100.0 | [100.0, 100.0] | +0.00 | Năm gốc |
| 3 ROOM | 2020 | 5,384 | 295,000 | 104.24 | 102.78 | [102.22, 103.33] | +1.46 | Năm đầy đủ |
| 3 ROOM | 2021 | 6,266 | 335,000 | 118.37 | 116.53 | [115.91, 117.15] | +1.85 | Năm đầy đủ |
| 3 ROOM | 2022 | 6,335 | 370,000 | 130.74 | 130.0 | [129.3, 130.71] | +0.74 | Năm đầy đủ |
| 3 ROOM | 2023 | 6,355 | 390,000 | 137.81 | 138.26 | [137.5, 139.03] | -0.45 | Năm đầy đủ |
| 3 ROOM | 2024 | 6,793 | 418,000 | 147.7 | 148.83 | [147.96, 149.71] | -1.13 | Năm đầy đủ |
| 3 ROOM | 2025 | 6,149 | 445,000 | 157.24 | 160.4 | [159.47, 161.34] | -3.16 | Năm đầy đủ gần nhất |
| 3 ROOM | 2026 | 5,026 | 440,000 | 155.48 | 159.6 | [158.62, 160.58] | -4.12 | Dữ liệu đến hiện tại (11 tháng) |
| 4 ROOM | 2017 | 8,604 | 408,000 | 102.0 | 100.83 | [100.36, 101.29] | +1.17 | Năm đầy đủ |
| 4 ROOM | 2018 | 8,769 | 400,000 | 100.0 | 99.61 | [99.19, 100.03] | +0.39 | Năm đầy đủ |
| 4 ROOM | 2019 | 9,228 | 400,000 | 100.0 | 100.0 | [100.0, 100.0] | +0.00 | Năm gốc |
| 4 ROOM | 2020 | 9,647 | 420,000 | 105.0 | 103.16 | [102.72, 103.61] | +1.84 | Năm đầy đủ |
| 4 ROOM | 2021 | 12,346 | 470,000 | 117.5 | 114.63 | [114.14, 115.13] | +2.87 | Năm đầy đủ |
| 4 ROOM | 2022 | 11,309 | 515,000 | 128.75 | 127.9 | [127.3, 128.49] | +0.85 | Năm đầy đủ |
| 4 ROOM | 2023 | 11,357 | 550,000 | 137.5 | 137.57 | [136.94, 138.2] | -0.07 | Năm đầy đủ |
| 4 ROOM | 2024 | 11,988 | 590,000 | 147.5 | 148.66 | [147.97, 149.36] | -1.16 | Năm đầy đủ |
| 4 ROOM | 2025 | 10,843 | 630,000 | 157.5 | 159.0 | [158.27, 159.74] | -1.50 | Năm đầy đủ gần nhất |
| 4 ROOM | 2026 | 9,614 | 630,000 | 157.5 | 159.28 | [158.54, 160.02] | -1.78 | Dữ liệu đến hiện tại (11 tháng) |
| 5 ROOM | 2017 | 5,002 | 478,000 | 99.07 | 98.33 | [97.81, 98.86] | +0.73 | Năm đầy đủ |
| 5 ROOM | 2018 | 5,487 | 475,000 | 98.45 | 98.66 | [98.16, 99.17] | -0.22 | Năm đầy đủ |
| 5 ROOM | 2019 | 5,427 | 482,500 | 100.0 | 100.0 | [100.0, 100.0] | +0.00 | Năm gốc |
| 5 ROOM | 2020 | 5,984 | 508,844 | 105.46 | 103.4 | [102.89, 103.91] | +2.06 | Năm đầy đủ |
| 5 ROOM | 2021 | 7,804 | 570,000 | 118.13 | 114.84 | [114.24, 115.45] | +3.29 | Năm đầy đủ |
| 5 ROOM | 2022 | 6,713 | 620,000 | 128.5 | 127.91 | [127.26, 128.56] | +0.59 | Năm đầy đủ |
| 5 ROOM | 2023 | 5,842 | 650,000 | 134.72 | 136.54 | [135.82, 137.27] | -1.83 | Năm đầy đủ |
| 5 ROOM | 2024 | 6,469 | 690,000 | 143.01 | 147.11 | [146.32, 147.89] | -4.10 | Năm đầy đủ |
| 5 ROOM | 2025 | 5,781 | 736,000 | 152.54 | 156.39 | [155.56, 157.23] | -3.85 | Năm đầy đủ gần nhất |
| 5 ROOM | 2026 | 5,285 | 745,000 | 154.4 | 157.83 | [156.94, 158.72] | -3.43 | Dữ liệu đến hiện tại (11 tháng) |

**Kết luận Q3:**
- **Kết luận chính (giai đoạn năm đầy đủ 2019 đến 2025):** Chỉ số giá thô toàn thị trường tăng +57.00% (từ trung vị $400,000 SGD lên $628,000 SGD), trong khi chỉ số Hedonic đã kiểm soát đặc điểm tăng +58.87% (95% CI: [158.34, 159.40]). Chênh lệch giữa giá thô và giá Hedonic ở năm đầy đủ gần nhất (2025) là -1.87 điểm chỉ số.
- **Dữ liệu năm 2026:** Đây là dữ liệu tính đến thời điểm hiện tại (11 tháng đầu năm 2026, 22,053 giao dịch), chưa phải năm đầy đủ. Chỉ số thô đạt 158.75 (+58.75%), chỉ số Hedonic đạt 159.33 (+59.33%).
- **Giai đoạn 2020-2022:** Đo nhận chỉ số giá thô cao hơn chỉ số Hedonic từ 2.61 đến 5.43 điểm chỉ số (năm 2020 lệch +3.14 điểm, năm 2021 lệch +5.43 điểm, năm 2022 lệch +2.61 điểm). Báo cáo số đo thuần túy, không đưa ra giả định nguyên nhân ngoài phạm vi dữ liệu.

---

## Giới hạn phương pháp và Cảnh báo bắt buộc
1. **Không suy diễn nhân quả:** Các hệ số hồi quy phản ánh mối tương quan có điều kiện (conditional correlation) trong dữ liệu giao dịch đã ghi nhận, không chứng minh quan hệ nhân quả.
2. **Đặc tính căn hộ không quan sát được:** Mô hình kiểm soát diện tích, tầng, loại căn, khu vực và thời điểm, nhưng chưa kiểm soát được tình trạng nội thất, hướng nhà, số lần sửa chữa nâng cấp của từng căn cụ thể.
3. **Nhóm thời hạn 90+:** Căn hộ còn trên 90 năm thuê được báo cáo riêng trong bảng do có thể bị ảnh hưởng đồng thời bởi các yếu tố mới xây.