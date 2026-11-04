# Báo cáo Nghiên cứu: Căn hộ có hạn dùng — Giá HDB Singapore thay đổi thế nào khi thời hạn thuê còn lại ngắn đi?

> **Tác giả:** [TÊN SINH VIÊN]  
> **Tuyên bố sử dụng AI:** Báo cáo và mã nguồn được hỗ trợ rà soát, viết mã và kiểm thử tự động bởi trợ lý trí tuệ nhân tạo (AI coding assistant). Toàn bộ dữ liệu, mô hình kinh tế lượng, kiểm thử dbt và pytest đều được thực thi trực tiếp trên môi trường máy trạm thực tế và chịu trách nhiệm bởi tác giả.  
> **Thời điểm lập:** 04/11/2026  
> **Kho lưu trữ:** `D:\video\hdb_elt`  
> **Công nghệ:** DuckDB, dbt (dbt-duckdb), Python 3.12 (statsmodels, pandas, scipy), Streamlit  

---

## 1. Mở đầu bằng Ví dụ Thực tế từ Thị trường

Trong thị trường nhà ở công cộng Singapore (HDB), người mua nhà nắm giữ hợp đồng thuê 99 năm do cơ quan nhà ở HDB cấp. Khi hợp đồng thuê trôi dần về cuối, giá trị giao dịch của căn hộ phản ánh sự suy giảm thời hạn thuê còn lại.

Dữ liệu giao dịch đăng ký chính thức trong kho dữ liệu `fct_resale_transaction` vào tháng **07/2024** tại cùng khu vực hành chính **QUEENSTOWN** ghi nhận hai căn hộ có các đặc tính cơ bản tương đồng nhưng có thời hạn thuê khác biệt lớn:

| Thuộc tính | Căn hộ 1 (Thuê ngắn) | Căn hộ 2 (Thuê dài) |
|---|---|---|
| **transaction_sk** | `6422b1795eabe983b98ee59eb120fa2b10dc0c446852ce9d5b9091f6f0255df5` | `bff535e26da9e95120bd78044e33f306d39c7da1902da444ce0cafa0fd701d83` |
| **Tháng giao dịch** | 2024-07 | 2024-07 |
| **Khu vực (Town)** | QUEENSTOWN | QUEENSTOWN |
| **Vị trí Block** | Block 95, C'WEALTH DR | Block 89, TANGLIN HALT RD |
| **Loại căn hộ** | 3 ROOM | 3 ROOM |
| **Khoảng tầng** | 04 TO 06 | 04 TO 06 |
| **Diện tích sàn** | 60.0 m² | 60.0 m² |
| **Thời hạn thuê còn lại** | **41 năm 7 tháng (41.58 năm)** | **83 năm 2 tháng (83.17 năm)** |
| **Giá bán lại (Resale Price)** | **322,000 SGD** | **592,000 SGD** |
| **Đơn giá trên mỗi m²** | **5,366.67 SGD/m²** | **9,866.67 SGD/m²** |
| **Mức chênh lệch đơn giá** | *Cơ sở đối chiếu* | **+83.85% (+4,500.00 SGD/m²)** |

> **Lưu ý phương pháp:** Đây là hai quan sát thực tế được chọn để minh họa sự khác biệt mức giá thô ghi nhận được giữa hai căn hộ có thời hạn thuê chênh lệch 41.58 năm. Cần chú ý rằng hai căn hộ đối chứng còn khác nhau về mẫu căn hộ (Căn 1: Standard; Căn 2: Model A), năm bắt đầu hợp đồng thuê (Căn 1: 1967; Căn 2: 2008) và khoảng cách đến ga MRT gần nhất (Căn 1: ~447 m; Căn 2: ~91 m). Đây **không phải là kết quả đã kiểm soát** bằng mô hình kinh tế lượng, bởi hai căn hộ còn khác nhau về vị trí cụ thể, cự ly đến các tiện ích giao thông và hiện trạng sửa chữa nội thất. Câu hỏi nghiên cứu đặt ra là: Sau khi kiểm soát đồng thời diện tích, tầng cao, loại căn hộ, khu vực hành chính và tháng giao dịch, mức chênh lệch giá theo thời hạn thuê còn lại được lượng hóa như thế nào?

---

## 2. Vấn đề và Người dùng

### 2.1. Vấn đề nghiên cứu
Nhà ở HDB tại Singapore được xây dựng và cấp quyền sử dụng đất có thời hạn 99 năm. Đối với các khu đô thị được phát triển từ những giai đoạn đầu, thời hạn thuê còn lại của nhiều khối nhà hiện đang rút ngắn dần. Người mua nhà đứng trước sự so sánh giữa các căn hộ có thời hạn thuê ngắn và các căn hộ có thời hạn thuê dài hơn tại các vị trí khác nhau. Việc lượng hóa mức độ chiết khấu giá gắn với số năm thuê còn lại cung cấp thông tin tham chiếu khách quan cho thị trường.

### 2.2. Nhóm người dùng mục tiêu
1. **Người mua nhà cá nhân:** Cần thông tin tham chiếu thực nghiệm về mức chênh lệch giá giữa các dải thời hạn thuê khác nhau để cân nhắc nhu cầu sử dụng thực tế.
2. **Chuyên viên nghiên cứu thị trường:** Cần chỉ số giá hedonic đã kiểm soát các đặc tính cơ bản của căn hộ qua các năm, đánh giá mức biến động giá trên cùng một rọ đặc tính căn hộ cố định để so sánh với sự thay đổi về cơ cấu giao dịch.
3. **Cơ quan quản lý dữ liệu:** Cần kiểm tra tính nhất quán và độ ổn định của các chỉ số đo lường kinh tế lượng theo chu kỳ thời gian.

---

## 3. Câu hỏi Phân tích

Nghiên cứu tập trung giải quyết 4 câu hỏi định lượng theo đặc tả:

- **Q1 (Đường cong thời hạn thuê):** Khi thời hạn thuê còn lại ngắn đi, giá căn hộ thay đổi theo hệ số nào sau khi kiểm soát diện tích sàn, tầng cao, loại căn, khu vực hành chính và tháng giao dịch? Hệ số này có ổn định giữa hai thời kỳ 2017–2022 và 2023–hiện tại không?
- **Q2 (Khác biệt theo khu vực):** Mức chênh lệch giá giữa nhóm căn hộ thời hạn 55–65 năm và nhóm tham chiếu 70–80 năm có khác nhau giữa các khu vực hành chính hay không? Thứ hạng chênh lệch giữa các khu vực có giữ được độ tương quan qua hai thời kỳ không?
- **Q3 (Chỉ số giá điều chỉnh - Hedonic vs Raw):** Tốc độ thay đổi của giá trung vị thô khác gì so với chỉ số giá hedonic đã kiểm soát thành phần căn hộ qua các năm từ năm gốc 2019?
- **Q4 (Hỗ trợ người mua):** Với các tiêu chí cụ thể về ngân sách, loại căn, thời hạn thuê tối thiểu và cự ly MRT, các khu vực nào có giao dịch đăng ký thực tế thỏa mãn trong 12 tháng gần nhất?

---

## 4. Nguồn Dữ liệu và Giấy phép

Hệ thống tích hợp dữ liệu từ 4 nguồn:

1. **HDB Resale Flat Prices (data.gov.sg):**
   - *Dataset ID:* `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
   - *Quy mô:* 244,119 dòng giao dịch đăng ký chính thức từ tháng 01/2017 đến tháng 11/2026.
   - *11 cột dữ liệu:* `month`, `town`, `flat_type`, `block`, `street_name`, `storey_range`, `floor_area_sqm`, `flat_model`, `lease_commence_date`, `remaining_lease`, `resale_price`.
   - *Giấy phép:* Singapore Open Data Licence.
2. **LTA MRT Station Exits (data.gov.sg):**
   - *Dataset ID:* `d_b39d3a0871985372d7e1637193335da5`
   - *Quy mô:* 613 cửa ga MRT/LRT kèm tọa độ WGS84.
   - *Giấy phép:* Singapore Open Data Licence.
3. **NUS 3D HDB Dataset (ualsg/hdb3d-data):**
   - *Kho dữ liệu:* Dữ liệu tọa độ địa lý các khối nhà HDB tại Singapore.
   - *Giấy phép:* MIT License.
4. **OneMap Search API (SLA):**
   - *Dịch vụ:* Tra cứu tọa độ cho các block mới xây dựng ngoài tập dữ liệu NUS 3D.
   - *Cơ chế gọi:* Giới hạn tần suất 1 request/giây kèm bộ nhớ đệm cục bộ.

---

## 5. Kiến trúc ELT

Hệ thống được tổ chức theo quy trình ELT sử dụng DuckDB làm kho dữ liệu cục bộ và dbt quản lý các tầng mô hình:

```
[ data.gov.sg API ]  -->  pipeline/extract_hdb.py  -->  data/raw/hdb_resale/.../hdb_resale.csv (Bất biến + Manifest)
[ LTA MRT GeoJSON ]  -->  pipeline/extract_mrt.py  -->  data/reference/mrt_station_exits.csv
[ NUS 3D + OneMap ]  -->  pipeline/extract_blocks.py--> data/reference/block_coordinates.csv
                                   │
                                   ▼
                         pipeline/load_raw.py
                                   │
                                   ▼ (Schema raw)
                 [ warehouse_staging.duckdb ]
                                   │
                                   ▼
                        dbt_hdb (16 Models, 24 Data Tests)
               ├── Staging: stg_hdb_resale, stg_mrt_exits, stg_block_location
               ├── Intermediate: int_resale_parsed, int_block_mrt_distance, int_resale_enriched
               ├── Marts: dim_month, dim_town, dim_block, dim_flat_type, fct_resale_transaction, mart_budget_search...
               └── Ops: ops_pipeline_run, ops_snapshot_delta, ops_source_freshness
                                   │
                                   ▼
                        analysis/run_analysis.py
                                   │
                                   ▼ (Schema analytics)
                         pipeline/quality_gate.py (12 Blocking Checks)
                                   │ (Nếu PASS)
                                   ▼
                         pipeline/publish.py (Atomic rename .tmp -> prod kèm retry)
                                   │
                                   ▼
                 [ data/warehouse/warehouse.duckdb ]
                                   │
                                   ▼
                 Streamlit Dashboard (app/Home.py - Read Only)
```

---

## 6. Kiểm soát Chất lượng Dữ liệu (Quality Control)

Hệ thống áp dụng chốt chặn chất lượng tại `pipeline/quality_gate.py` với 12 quy tắc bắt buộc:

| STT | Quy tắc kiểm tra | Ngưỡng bắt buộc | Đo lường thực tế | Kết quả |
|:---:|---|---|---|:---:|
| 1 | Cấu trúc cột file raw | Đúng 11 cột quy định | 11 cột hiện diện đầy đủ | **PASS** |
| 2 | File dữ liệu thô | Kích thước > 0 bytes | 24,149,037 bytes | **PASS** |
| 3 | Tỷ lệ giảm dòng snapshot | Giảm <= 1.0% | Giảm 0.00% (244,119 dòng) | **PASS** |
| 4 | Tỷ lệ Null các trường cốt lõi | Null <= 0.1% | 0 dòng null (0.00%) | **PASS** |
| 5 | Giá bán `resale_price` | Giá trị > 0 | 0 dòng <= 0 | **PASS** |
| 6 | Diện tích `floor_area_sqm` | Giá trị > 0 | 0 dòng <= 0 | **PASS** |
| 7 | Lỗi phân tích `remaining_lease` | Lỗi <= 0.1% | 0 dòng lỗi (0.00%) | **PASS** |
| 8 | Lỗi phân tích `storey_range` | Lỗi <= 0.1% | 0 dòng lỗi (0.00%) | **PASS** |
| 9 | Tính duy nhất `transaction_sk` | Duy nhất 100% | 244,119 khóa duy nhất | **PASS** |
| 10 | Khớp số dòng Raw và Fact | Chênh lệch 0 dòng | Raw: 244,119; Fact: 244,119 (lệch 0) | **PASS** |
| 11 | Tỷ lệ ghép nối tọa độ block | Khớp >= 98.0% | Khớp 100.00% (244,119/244,119 giao dịch) | **PASS** |
| 12 | Độ tươi dữ liệu (`max(month)`) | Không trễ quá 2 tháng | max(month) = 2026-11 (Trễ 0 tháng) | **PASS** |

- **Báo cáo dòng trùng:** Trong 244,119 dòng giao dịch thô, ghi nhận **318 dòng (0.13%)** có giá trị trùng nhau trên cả 11 thuộc tính gốc trong cùng một tháng. Hệ thống tính thứ tự xuất hiện bằng hàm cửa sổ `ROW_NUMBER() OVER (PARTITION BY business_hash ORDER BY source_row_number)` và gắn khóa `transaction_sk = sha256(business_hash || occurrence_no)`. Toàn bộ 318 dòng được giữ nguyên trong bảng fact để bảo toàn số dòng so với dữ liệu nguồn.
- **Cơ chế xuất bản an toàn:** Dữ liệu được xử lý trong `warehouse_staging.duckdb`. Khi Quality Gate đạt, module `publish.py` tiến hành sao chép sang file tạm `.tmp` và đổi tên thay thế vào `warehouse.duckdb` kèm cơ chế thử lại (retry) nếu gặp khóa đọc trên Windows.

---

## 7. Phân tích và Phương pháp Kinh tế lượng

Mô hình định giá Hedonic sử dụng phương pháp bình phương bé nhất (OLS) với sai số chuẩn gom cụm theo từng khối nhà (`block_id = block || '_' || street_name`):

$$\ln(\text{resale\_price}_i) = \alpha + \sum_{k} \beta_k \text{LeaseBand}_{ik} + \gamma \text{Area}_i + \delta \text{Storey}_i + \sum_f \theta_f \text{FlatType}_{if} + \sum_t \mu_t \text{Town}_{it} + \sum_m \lambda_m \text{Month}_{im} + \varepsilon_i$$

- **Quy tắc phân tích:** Được lưu tại `config/analysis_rules.yml` với mã băm SHA-256 `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`. Giữ nguyên ngưỡng khóa, không lọc lại mẫu.
- **Biến phụ thuộc:** $\ln(\text{resale\_price})$ (logarit tự nhiên của giá bán lại).
- **Hệ số hồi quy ($\beta_k$):** Đo lường bằng đơn vị **log points**.
- **Chênh lệch phần trăm:** Tính theo công thức $(\exp(\beta_k) - 1) \times 100\%$.
- **Biến kiểm soát:** Diện tích sàn (`floor_area_sqm`), trung vị khoảng tầng (`storey_mid`), loại căn hộ (`flat_type`), khu vực hành chính (`town`), và tháng giao dịch (`month`).
- **Nhóm tham chiếu:** Căn hộ có thời hạn thuê còn lại từ **70 đến 74 năm** ($\beta = 0.0$, chênh lệch $0.0\%$).

---

## 8. Dashboard Trực quan hóa

Dashboard được xây dựng bằng Streamlit, kết nối trực tiếp ở chế độ chỉ đọc với `warehouse.duckdb` gồm 6 trang chức năng:

1. **Trang chủ Tổng quan (`Home.py`):** Cung cấp các số đo vĩ mô, biểu đồ xu hướng theo quý và phân bố giao dịch theo dải thời hạn thuê.
2. **Đường cong Thuê (`1_Duong_cong_thue.py`):** Trực quan hóa đường cong hệ số log và mức chênh lệch giá theo nhóm 5 năm kèm khoảng tin cậy 95% gom cụm block, đối chiếu hai thời kỳ P1 và P2, trình bày bảng số liệu chi tiết và kết luận Q1 = FAIL.
3. **So sánh Khu vực (`2_So_sanh_khu.py`):** Biểu đồ thể hiện mức chênh lệch giữa nhóm căn hộ 55–65 năm so với nhóm 70–80 năm trên 13 khu vực đủ điều kiện, ghi nhận nhóm phân loại Mature / Non-Mature theo HDB và hệ số tương quan hạng Spearman (0.6209).
4. **Giá đã Điều chỉnh (`3_Gia_dieu_chinh.py`):** So sánh chuỗi chỉ số giá thô và chỉ số Hedonic (năm gốc 2019 = 100) kèm khoảng tin cậy 95% cho toàn thị trường và 3 loại căn (3-Room, 4-Room, 5-Room).
5. **Công cụ Tìm kiếm Khu vực (`4_Cong_cu_tim_khu.py`):** Cho phép người dùng lọc dữ liệu 12 tháng gần nhất theo ngân sách, loại căn, thời hạn tối thiểu và cự ly MRT. Bắt buộc hiển thị thông báo: *"Kết quả mô tả giao dịch đã đăng ký gần đây, không phải định giá."* Ẩn các khu vực dưới 10 giao dịch, không xếp hạng.
6. **Vận hành & Giám sát (`5_Van_hanh.py`):** Giám sát trạng thái pipeline, lịch sử nạp dữ liệu, độ tươi nguồn và chi tiết kết quả 12 quy tắc Quality Gate.

---

## 9. Kết quả Phân tích: Quan sát, Diễn giải và Đề xuất

### 9.1. Quan sát (Số đo Thực nghiệm Trực tiếp)

#### Q1. Đường cong Thời hạn thuê
- **Quy mô mẫu:** Giai đoạn 1 (2017–2022) có tối thiểu 5,879 giao dịch/nhóm (nhóm 85–89 năm). Giai đoạn 2 (2023–2026) có tối thiểu 2,591 giao dịch/nhóm (nhóm 80–84 năm). Cả hai đều đạt ngưỡng >= 1,000 giao dịch.
- **Thứ hạng hệ số:** Hệ số OLS tăng đơn điệu theo thời hạn thuê ở cả hai giai đoạn (Spearman rank correlation = **1.0000**).
- **Hệ số hồi quy và mức chênh lệch giá so với nhóm 70–74 năm:**
  - Nhóm `< 50 năm`: P1 = -0.3104 log points (-26.68%); P2 = -0.3327 log points (-28.30%).
  - Nhóm `50–54 năm`: P1 = -0.2009 log points (-18.20%); P2 = -0.2107 log points (-19.00%).
  - Nhóm `55–59 năm`: P1 = -0.1237 log points (-11.63%); P2 = -0.1017 log points (-9.67%).
  - Nhóm `60–64 năm`: P1 = -0.0350 log points (-3.44%); P2 = -0.0489 log points (-4.77%).
  - Nhóm `65–69 năm`: P1 = -0.0037 log points (-0.37%); P2 = -0.0448 log points (-4.38%).
  - Nhóm `75–79 năm`: P1 = +0.0490 log points (+5.02%); P2 = +0.0275 log points (+2.79%).
  - Nhóm `80–84 năm`: P1 = +0.0845 log points (+8.82%); P2 = +0.1673 log points (+18.21%).
  - Nhóm `85–89 năm`: P1 = +0.2026 log points (+22.46%); P2 = +0.1813 log points (+19.88%).
  - Nhóm `90+ năm`: P1 = +0.2603 log points (+29.74%); P2 = +0.2004 log points (+22.19%).
- **Độ chênh lệch giữa hai thời kỳ:**
  - Nhóm `80–84 năm`: Hệ số tăng từ +0.0845 lên +0.1673 log points. Độ chênh lệch đo được là **+0.0828 log points** (tương đương **+9.39 điểm phần trăm** theo chênh lệch phần trăm), vượt ngưỡng quy định 0.05 (5 điểm phần trăm).
  - Nhóm `65–69 năm`: Hệ số thay đổi từ -0.0037 xuống -0.0448 log points. Độ chênh lệch đo được là **-0.0411 log points** (tương đương **-4.01 điểm phần trăm**).
  - Nhóm `90+ năm`: Hệ số thay đổi từ +0.2603 xuống +0.2004 log points. Độ chênh lệch đo được là **-0.0600 log points** (tương đương **-7.55 điểm phần trăm**).
- **Kết luận:** **Q1 = FAIL**. Về xu hướng tổng thể, kết quả ước lượng cho thấy giá căn hộ nhìn chung thấp hơn khi thời hạn thuê còn lại ngắn hơn (hệ số giảm đơn điệu từ nhóm 90+ năm xuống nhóm < 50 năm, Spearman đạt 1.0000). Tuy nhiên, về tiêu chí độ ổn định cấu trúc theo thời gian, đường cong không đạt yêu cầu do biến động hệ số tại nhóm 80–84 năm vượt ngưỡng khóa 0.05. Báo cáo trung thực số đo thực tế, không suy đoán nguyên nhân khi không có dữ liệu chứng minh.

#### Q2. Mức Chênh lệch Thời hạn theo Khu vực (Town Lease Gap)
- **Số khu vực đủ điều kiện (>= 200 giao dịch mỗi nhóm cả 2 thời kỳ):** Đạt **13 khu vực** (ngưỡng >= 10 khu).
- **Hệ số tương quan hạng Spearman giữa hai thời kỳ:** Đạt **0.6209** (p = 0.0235, ngưỡng >= 0.60).
- **Số đo chi tiết từ bảng `analytics.town_lease_gap`:**
  - *Khu vực Mature (nhóm phân loại mô tả theo HDB, chưa kiểm định thống kê riêng biệt):*
    - TOA PAYOH: P1 = -0.2377 (-21.16%), P2 = -0.2556 (-22.55%)
    - GEYLANG: P1 = -0.2053 (-18.56%), P2 = -0.2674 (-23.47%)
    - BUKIT MERAH: P1 = -0.1526 (-14.15%), P2 = -0.1990 (-18.04%)
    - BEDOK: P1 = -0.1163 (-10.98%), P2 = -0.1469 (-13.66%)
    - ANG MO KIO: P1 = -0.1161 (-10.97%), P2 = -0.2743 (-23.99%)
    - KALLANG/WHAMPOA: P1 = -0.0851 (-8.16%), P2 = -0.1715 (-15.76%)
    - TAMPINES: P1 = +0.0123 (+1.24%), P2 = -0.0197 (-1.95%)
  - *Khu vực Non-Mature (nhóm phân loại mô tả theo HDB, chưa kiểm định thống kê riêng biệt):*
    - JURONG EAST: P1 = -0.1899 (-17.30%), P2 = -0.1438 (-13.39%)
    - WOODLANDS: P1 = -0.1352 (-12.64%), P2 = -0.0643 (-6.23%)
    - CHOA CHU KANG: P1 = -0.0895 (-8.56%), P2 = -0.0159 (-1.58%)
    - BUKIT BATOK: P1 = -0.0856 (-8.21%), P2 = -0.1034 (-9.83%)
    - JURONG WEST: P1 = -0.0417 (-4.08%), P2 = -0.0835 (-8.01%)
    - HOUGANG: P1 = -0.0340 (-3.34%), P2 = -0.0289 (-2.85%)
- **Kiểm tra độ nhạy Leave-One-Out Spearman:**
  - Giá trị rho dao động trong khoảng từ **0.5524 đến 0.6993** (trung bình 0.6192).
  - Trong 13 lần thử nghiệm, ghi nhận **6 lần hệ số rơi xuống dưới ngưỡng 0.60**: khi loại bỏ Bukit Merah (0.5804), Geylang (0.5664), Hougang (0.5524), Jurong West (0.5944), Tampines (0.5524), và Toa Payoh (0.5664).
- **Kết luận:** **Q2 = PASS**.

#### Q3. Chỉ số Giá Điều chỉnh (Hedonic vs Raw) và Cơ cấu Giao dịch
- **Chuỗi thời gian:** Đầy đủ 10 năm liên tục từ 2017 đến 2026.
- **So sánh năm gốc 2019 và năm đầy đủ gần nhất 2025:**
  - Giá trung vị thô toàn thị trường tăng từ 400,000 SGD lên 628,000 SGD (**+57.00%**, chỉ số 157.00).
  - Chỉ số Hedonic kiểm soát đặc điểm tăng từ 100.0 lên 158.87 (**+58.87%**, 95% CI: [158.34, 159.40]).
  - Chênh lệch giữa chỉ số thô và chỉ số Hedonic ở năm 2025 là **-1.87 điểm chỉ số**.
- **Dữ liệu năm 2026 (dữ liệu đến ngày 04/11/2026, 22,053 giao dịch):**
  - Chỉ số giá thô đạt 158.75 (+58.75%), chỉ số Hedonic đạt 159.33 (+59.33%). Độ lệch là -0.58 điểm.
- **Biến động cơ cấu giao dịch thực tế qua các năm (tính từ `fct_resale_transaction`):**

| Năm | Tổng số GD | Tỷ trọng 3-Room (%) | Tỷ trọng 4-Room (%) | Tỷ trọng 5-Room (%) | Loại căn khác (%) | Diện tích TB (m²) | Trung vị diện tích (m²) | Tầng TB | Thời hạn thuê TB (năm) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 2017 | 20,509 | 24.6% | 42.0% | 24.4% | 9.0% | 97.8 | 96.0 | 8.7 | 74.7 |
| 2018 | 21,561 | 23.7% | 40.7% | 25.4% | 10.1% | 98.4 | 97.0 | 8.7 | 74.5 |
| 2019 | 22,186 | 24.4% | 41.6% | 24.5% | 9.5% | 97.1 | 94.0 | 8.5 | 74.5 |
| 2020 | 23,333 | 23.1% | 41.3% | 25.6% | 9.9% | 97.6 | 93.0 | 8.6 | 75.3 |
| 2021 | 29,087 | 21.5% | 42.4% | 26.8% | 9.2% | 98.2 | 93.0 | 9.0 | 75.4 |
| 2022 | 26,720 | 23.7% | 42.3% | 25.1% | 8.8% | 96.9 | 93.0 | 8.9 | 74.3 |
| 2023 | 25,754 | 24.7% | 44.1% | 22.7% | 8.5% | 95.1 | 93.0 | 8.8 | 74.1 |
| 2024 | 27,832 | 24.4% | 43.1% | 23.2% | 9.3% | 95.4 | 93.0 | 8.7 | 73.3 |
| 2025 | 25,084 | 24.5% | 43.2% | 23.0% | 9.2% | 94.9 | 93.0 | 8.9 | 72.4 |
| 2026 | 22,053 | 22.8% | 43.6% | 24.0% | 9.6% | 96.2 | 93.0 | 9.0 | 71.9 |

- **Đo lường biến động cơ cấu và thời hạn thuê (2020–2026):**
  - Trong giai đoạn 2020–2021, thời hạn thuê trung bình của các căn hộ giao dịch tăng nhẹ từ 74.5 năm (năm 2019) lên 75.3–75.4 năm (do gia tăng tỷ lệ căn hộ có thời hạn dài giao dịch), đồng thời tỷ trọng căn hộ 5-Room tăng lên 25.6%–26.8% (so với 24.5% năm 2019), diện tích trung bình tăng lên 97.6–98.2 m² và tầng trung bình tăng lên 8.6–9.0. Sự dịch chuyển cơ cấu căn hộ này diễn ra cùng lúc với việc chỉ số giá thô tăng nhanh hơn chỉ số Hedonic (năm 2020 cao hơn +3.14 điểm; năm 2021 cao hơn +5.43 điểm; năm 2022 cao hơn +2.61 điểm).
  - Ngược lại, từ sau năm 2021 đến thời điểm 04/11/2026, thời hạn thuê trung bình của các căn hộ giao dịch có xu hướng suy giảm rõ rệt từ 75.4 năm xuống 71.9 năm (-3.5 năm), phản ánh lượng căn hộ có thời hạn thuê thấp hơn tham gia vào rọ giao dịch thực tế trên thị trường ngày càng tăng.
- **Kết luận:** **Q3 = PASS**.

#### Q4. Kết quả Thực tế từ Bộ lọc Tìm kiếm (Dữ liệu 12 Tháng Gần nhất)
Thực hiện truy vấn trên bảng `main_marts.mart_budget_search` với tiêu chí: Loại căn `4 ROOM`, Ngân sách từ `450,000` đến `650,000 SGD`, Thời hạn thuê tối thiểu `60 năm`, Cự ly ga MRT `< 800 mét`. Áp dụng điều kiện loại bỏ các khu vực có dưới 10 giao dịch thỏa mãn.

Kết quả ghi nhận **14 khu vực hành chính** thỏa mãn tiêu chí, trình bày theo thứ tự bảng chữ cái tên khu vực (không xếp hạng):

| Khu vực hành chính (Town) | Số giao dịch thỏa mãn | Số block thỏa mãn | Trung vị giá (SGD) | Thời hạn thuê TB (năm) | Cự ly MRT TB (mét) |
|---|:---:|:---:|:---:|:---:|:---:|
| **BEDOK** | 21 | 14 | 590,000 | 63.1 | 372 |
| **BUKIT BATOK** | 78 | 40 | 546,250 | 67.0 | 512 |
| **BUKIT PANJANG** | 287 | 134 | 545,000 | 71.5 | 274 |
| **CHOA CHU KANG** | 399 | 202 | 552,500 | 73.0 | 436 |
| **HOUGANG** | 106 | 51 | 600,000 | 68.0 | 542 |
| **JURONG EAST** | 12 | 7 | 575,000 | 71.1 | 697 |
| **JURONG WEST** | 205 | 106 | 550,250 | 73.0 | 449 |
| **PASIR RIS** | 21 | 13 | 602,500 | 63.9 | 689 |
| **PUNGGOL** | 258 | 141 | 620,000 | 83.4 | 256 |
| **SEMBAWANG** | 193 | 102 | 553,122 | 77.2 | 487 |
| **SENGKANG** | 466 | 229 | 588,000 | 78.6 | 286 |
| **TAMPINES** | 137 | 93 | 620,750 | 65.2 | 512 |
| **WOODLANDS** | 574 | 274 | 550,000 | 72.4 | 474 |
| **YISHUN** | 114 | 72 | 550,000 | 61.8 | 524 |

---

### 9.2. Diễn giải (Cách hiểu Có điều kiện)

1. **Về sự thay đổi ở Q1:** Đường cong chiết khấu thời hạn thuê không giữ được tính ổn định qua thời gian do sự thay đổi hệ số tại nhóm 80–84 năm (tăng 0.0828 log points giữa hai thời kỳ). Điều này cho thấy mức định giá của thị trường đối với nhóm thời hạn này có sự dịch chuyển giữa giai đoạn 2017–2022 và giai đoạn sau năm 2022.
2. **Về phân hóa theo khu vực (Q2):** Mức chênh lệch giá giữa nhóm 55–65 năm và nhóm 70–80 năm có sự khác nhau giữa 13 khu vực. Tại một số khu vực như Toa Payoh, Geylang, Bukit Merah, mức chênh lệch ghi nhận từ -14% đến -24%; trong khi tại Hougang, Jurong West, Tampines, mức chênh lệch ghi nhận dưới -8%.
3. **Về chênh lệch giữa giá thô và Hedonic (Q3):** Việc giá thô tăng nhanh hơn chỉ số Hedonic trong giai đoạn 2020–2021 diễn ra cùng lúc với thay đổi cơ cấu căn hộ giao dịch (gia tăng tỷ trọng căn hộ 5-Room, tăng diện tích trung bình và tăng nhẹ thời hạn thuê trung bình). Khi cơ cấu giao dịch dịch chuyển sang các căn hộ có quy mô lớn hơn, giá trung vị thô phản ánh đồng thời cả biến động giá lẫn sự thay đổi giỏ hàng giao dịch.

---

### 9.3. Đề xuất (Việc cần làm và Chỉ số Theo dõi)

1. **Đối với Phân tích Thị trường:**
   - Theo dõi đồng thời cả chuỗi giá trung vị thô và chuỗi chỉ số Hedonic đã kiểm soát đặc tính để nhận diện thời điểm có sự dịch chuyển cơ cấu giao dịch.
   - Theo dõi chỉ số chênh lệch thành phần (`gap_raw_vs_hedonic`).
2. **Đối với Kỹ thuật Vận hành Dữ liệu:**
   - Theo dõi tỷ lệ dòng trùng lặp `business_hash` qua từng lần nạp dữ liệu định kỳ.
   - Theo dõi độ trễ thời gian của dữ liệu nguồn `max(month)` so với tháng hiện tại.

---

## 10. Giới hạn Nghiên cứu (Bắt buộc theo Mục 14)

1. **Dữ liệu là giao dịch đã đăng ký:** Dữ liệu chỉ phản ánh các hợp đồng đã hoàn tất thủ tục đăng ký tại HDB, không phản ánh toàn bộ cung - cầu trên thị trường.
2. **Đơn vị thời gian theo tháng:** Dữ liệu được ghi nhận theo tháng (`month`), không có ngày giao dịch cụ thể.
3. **Không có mã giao dịch hoặc vị trí căn chính xác:** Dữ liệu công khai chỉ cung cấp số block và khoảng tầng, không có số căn hộ cụ thể.
4. **Giá bán không phải giá thuê:** Giá bán lại phản ánh quyền sử dụng đất có thời hạn, không đồng nhất với giá thuê nhà ngắn hạn.
5. **Chưa điều chỉnh lạm phát:** Số liệu là giá danh nghĩa bằng SGD tại thời điểm đăng ký, chưa điều chỉnh theo Chỉ số Giá tiêu dùng (CPI).
6. **Thành phần căn được bán thay đổi theo thời gian:** Tỷ trọng căn hộ theo loại phòng, độ tuổi và vị trí bán ra trong mỗi kỳ không cố định.
7. **Thời hạn thuê liên quan đến tuổi căn và chất lượng căn:** Các căn hộ có thời hạn thuê ngắn hơn đồng thời có năm xây dựng cũ hơn và tiêu chuẩn kỹ thuật ban đầu khác biệt.
8. **Khoảng cách là đường thẳng:** Cự ly đến ga MRT và CBD được tính bằng khoảng cách đường thẳng Haversine, chưa phản ánh khoảng cách mạng lưới đi bộ thực tế.
9. **Mạng MRT là hiện tại:** Mô hình tính khoảng cách dựa trên mạng lưới 613 cửa ga hiện hành, không phản ánh lịch sử thời điểm mở cửa của từng tuyến ga trong quá khứ.
10. **Kết quả là mối liên quan, không phải nhân quả:** Hệ số hồi quy chỉ mô tả tương quan thống kê có điều kiện, không chứng minh quan hệ nhân quả.
11. **Không phải tư vấn tài chính:** Kết quả nghiên cứu phục vụ mục đích phân tích học thuật, không phải khuyến nghị đầu tư tài chính.

---

## 11. Vận hành Thực tế

### 11.1. Chu kỳ thực thi
Hệ thống được thiết kế để thực thi định kỳ. Cơ chế so sánh mã băm SHA-256 đối với file dữ liệu tải về đảm bảo nếu dữ liệu nguồn không có thay đổi, hệ thống ghi nhận trạng thái `no_change` trong `manifest.json` và không ghi đè dữ liệu thừa.

### 11.2. Cơ chế khóa file trên hệ điều hành Windows
Trên môi trường Windows, khi có tiến trình đang mở kết nối đọc tới `warehouse.duckdb`, lệnh thay thế file nguyên tử sẽ gặp lỗi truy cập `PermissionError`.  
Quy trình xử lý được thiết kế như sau:
1. Module kết nối `app/db.py` của Streamlit tự động đóng kết nối ngay sau khi hoàn thành truy vấn.
2. Module `pipeline/publish.py` áp dụng cơ chế thử lại (tối đa 5 lần với khoảng chờ giữa các lần). Nếu file vẫn bị khóa sau toàn bộ số lần thử lại, hệ thống giữ nguyên tệp kho dữ liệu hiện tại, dọn dẹp file tạm `.tmp` và ghi nhận trạng thái xuất bản thất bại (FAILED), không làm gián đoạn tiến trình dashboard đang chạy.

### 11.3. Theo dõi số lần chạy theo lịch tự động
Hệ thống đã được thiết lập tác vụ tự động hóa qua Windows Task Scheduler (`HDB_ELT_Daily_Run`) chạy hằng ngày lúc 08:15 AM. Tính đến hiện tại, hệ thống đã ghi nhận 1 lần chạy thử nghiệm kỹ thuật thành công (lúc 17:08 ngày 04/11/2026, ExitCode: 0, lưu log tại `logs/scheduler/run_20261104_170831.log`). Số lần chạy tự động theo lịch hiện tại là **0/7 lần**, hệ thống đang trong giai đoạn tiếp tục theo dõi tích lũy đủ 7 ngày liên tiếp theo Tiêu chí 13.

---

## 12. Kết luận

Dự án đã thiết lập quy trình ELT từ khâu trích xuất dữ liệu trên data.gov.sg, chuyển đổi qua dbt, kiểm định chất lượng và phục vụ dashboard:

- **Q1 (FAIL):** Mô hình ghi nhận xu hướng giá căn hộ nhìn chung thấp hơn khi thời hạn thuê còn lại ngắn hơn (hệ số giảm đơn điệu với Spearman = 1.0 qua các dải từ 90+ năm đến 50–54 năm). Tuy nhiên, về tiêu chí độ ổn định cấu trúc giữa hai thời kỳ, độ chênh lệch ở nhóm 80–84 năm đo được là **0,0828 log points** (tương đương **9,39 điểm phần trăm**), vượt ngưỡng quy định 0.05 (5 điểm phần trăm). Giữ nguyên kết luận FAIL theo quy tắc đã khóa.
- **Q2 (PASS):** Mức chênh lệch giá giữa nhóm 55–65 năm và nhóm 70–80 năm có sự khác biệt giữa 13 khu vực đủ điều kiện (Spearman thứ hạng = 0.6209). Kiểm tra độ nhạy Leave-One-Out ghi nhận khoảng dao động từ 0.5524 đến 0.6993, trong đó có 6/13 lần rơi xuống dưới 0.60. Nhóm phân loại Mature / Non-Mature theo HDB là phân loại mô tả, chưa kiểm định thống kê riêng biệt.
- **Q3 (PASS):** Chuỗi chỉ số Hedonic đã kiểm soát thành phần căn hộ từ năm gốc 2019 đến năm đầy đủ 2025 (+58.87% so với mức tăng thô +57.00%), cho thấy sự khác biệt về tốc độ tăng giá so với giá thô khi cơ cấu giao dịch dịch chuyển sang các căn hộ diện tích lớn hơn và thời hạn thuê dài hơn trong giai đoạn 2020–2021.
- **Q4 (HOẠT ĐỘNG):** Công cụ tìm kiếm hỗ trợ lọc dữ liệu giao dịch 12 tháng gần nhất theo ngân sách, thời hạn thuê và cự ly MRT, hiển thị 14 khu vực thỏa mãn mà không xếp hạng.

---

## 13. Phụ lục

### 13.1. Từ điển Dữ liệu (Bảng Fact cốt lõi)
Chi tiết tại [docs/data_dictionary.md](file:///d:/video/hdb_elt/docs/data_dictionary.md).

| Tên cột | Kiểu dữ liệu | Diễn giải |
|---|---|---|
| `transaction_sk` | VARCHAR (SHA-256) | Khóa thay thế duy nhất của giao dịch |
| `business_hash` | VARCHAR (SHA-256) | Mã băm xác định từ 11 thuộc tính gốc đã chuẩn hóa |
| `occurrence_no` | INTEGER | Thứ tự xuất hiện của dòng giao dịch có cùng `business_hash` |
| `month` | VARCHAR | Tháng đăng ký giao dịch (`YYYY-MM`) |
| `town` | VARCHAR | Khu vực hành chính thị trấn HDB |
| `flat_type` | VARCHAR | Loại căn hộ |
| `block` | VARCHAR | Số hiệu block tòa nhà |
| `street_name` | VARCHAR | Tên đường |
| `storey_mid` | DOUBLE | Trung vị của khoảng tầng |
| `floor_area_sqm` | DOUBLE | Diện tích sàn căn hộ (m²) |
| `remaining_lease_years` | DOUBLE | Thời hạn thuê còn lại quy đổi ra năm số thực |
| `lease_band_5yr` | VARCHAR | Nhóm thời hạn thuê 5 năm |
| `resale_price` | DOUBLE | Giá bán lại căn hộ (SGD) |
| `price_per_sqm` | DOUBLE | Đơn giá trên mỗi m² sàn (SGD/m²) |
| `nearest_mrt_station` | VARCHAR | Tên ga MRT gần nhất |
| `mrt_distance_m` | DOUBLE | Khoảng cách đường thẳng Haversine đến ga MRT gần nhất (mét) |
| `cbd_distance_km` | DOUBLE | Khoảng cách đường thẳng đến CBD Raffles Place (km) |

### 13.2. Nguồn Dữ liệu Tham chiếu
- **HDB API:** `https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view`
- **LTA MRT API:** `https://data.gov.sg/datasets/d_b39d3a0871985372d7e1637193335da5/view`
- **NUS 3D Dataset:** `https://github.com/ualsg/hdb3d-data`
- **OneMap SLA:** `https://www.onemap.gov.sg/apidocs/`

### 13.3. Hướng dẫn Chạy lại
```powershell
Set-Location "D:\video\hdb_elt"
pip install -r requirements.txt
python pipeline/run_pipeline.py
Set-Location "dbt_hdb"
dbt test --profiles-dir .
Set-Location ".."
pytest -v
streamlit run app/Home.py
```
