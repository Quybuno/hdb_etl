# Báo cáo Nghiên cứu: Căn hộ có hạn dùng — Giá HDB Singapore thay đổi thế nào khi thời hạn thuê còn lại ngắn đi?

> **Tác giả:** Kỹ sư Dữ liệu (Data Engineer)  
> **Thời điểm lập:** 04/11/2026  
> **Kho lưu trữ:** `D:\video\hdb_elt`  
> **Công nghệ:** DuckDB, dbt (dbt-duckdb), Python 3.12 (statsmodels, pandas, scipy), Streamlit  

---

## 1. Mở đầu bằng Ví dụ Thực tế từ Thị trường

Trong thị trường nhà ở công cộng Singapore (HDB), người mua nhà không sở hữu đất vĩnh viễn mà nắm giữ hợp đồng thuê 99 năm do HDB cấp. Khi hợp đồng thuê trôi dần về cuối, giá trị giao dịch của căn hộ chịu tác động trực tiếp của quy luật khấu hao thời hạn.

Dữ liệu giao dịch thực tế đã đăng ký trong tháng **05/2025** tại cùng khu vực hành chính **ANG MO KIO** cho thấy sự chênh lệch rõ rệt giữa hai căn hộ có diện tích và loại phòng tương đương:

| Thuộc tính | Căn hộ A (Thuê ngắn) | Căn hộ B (Thuê dài) |
|---|---|---|
| **Tháng giao dịch** | 2025-05 | 2025-05 |
| **Khu vực (Town)** | ANG MO KIO | ANG MO KIO |
| **Vị trí Block** | Block 214, Ang Mo Kio Ave 3 | Block 700C, Ang Mo Kio Ave 6 |
| **Loại căn hộ** | 4 ROOM | 4 ROOM |
| **Diện tích sàn** | 82.0 m² | 85.0 m² |
| **Khoảng tầng** | 04 TO 06 | 10 TO 12 |
| **Năm bắt đầu thuê** | 1978 | 2005 |
| **Thời hạn thuê còn lại** | **49 năm 9 tháng (49.75 năm)** | **77 năm 2 tháng (77.17 năm)** |
| **Giá bán lại (Resale Price)** | **530,000 SGD** | **798,000 SGD** |
| **Đơn giá trên m²** | **6,463.41 SGD/m²** | **9,388.24 SGD/m²** |
| **Mức chênh lệch đơn giá** | *Cơ sở tham chiếu* | **+45.25% (+2,924.83 SGD/m²)** |

Mặc dù có cùng công năng 4 phòng và giao dịch trong cùng một tháng tại cùng một thị trấn, căn hộ còn 77 năm thời hạn thuê có đơn giá trên mỗi mét vuông cao hơn 45.25% so với căn hộ chỉ còn dưới 50 năm thời hạn thuê. Câu hỏi đặt ra là: Sau khi kiểm soát một cách hệ thống các yếu tố cấu thành khác (vị trí khu vực, diện tích, tầng cao, cự ly MRT, cự ly trung tâm và thời điểm giao dịch), đường cong chiết khấu giá trị theo thời hạn thuê thực sự có hình dạng như thế nào và có giữ được tính ổn định qua các chu kỳ thị trường hay không?

---

## 2. Vấn đề và Người dùng

### 2.1. Vấn đề nghiên cứu
Hơn 80% công dân Singapore sinh sống trong các căn hộ HDB. Phần lớn các khu đô thị xây dựng từ thập niên 1970–1980 (như Toa Payoh, Ang Mo Kio, Bedok, Queenstown) hiện đã bước vào nửa sau của vòng đời 99 năm. Người mua nhà, đặc biệt là nhóm người trẻ và người mua nhà lần đầu, đứng trước sự đánh đổi phức tạp:
- Chọn căn hộ cũ ở vị trí trung tâm, tiện ích hoàn thiện nhưng thời hạn thuê còn ngắn, đối mặt với rủi ro khấu hao giá trị và hạn chế vay thế chấp theo quy định CPF/HDB khi thời hạn thuê còn dưới 60 năm.
- Chọn căn hộ mới ở các khu vực rìa đô thị với thời hạn thuê dài nhưng cách xa trung tâm việc làm.

### 2.2. Nhóm người dùng mục tiêu
1. **Người mua nhà cá nhân:** Cần công cụ khách quan để ước tính mức chiết khấu giá hợp lý khi mua căn hộ cũ, thu hẹp phạm vi tìm kiếm theo ngân sách thực tế mà không bị dẫn dắt bởi các xếp hạng quảng cáo thiên lệch.
2. **Chuyên viên phân tích và Định chế tài chính:** Cần theo dõi chuỗi chỉ số giá hedonic đã chuẩn hóa đặc tính căn hộ để đánh giá rủi ro tài sản thế chấp theo vòng đời hợp đồng thuê.
3. **Cơ quan quản lý và Nhà nghiên cứu chính sách:** Cần dữ liệu đo lường thực nghiệm về sự khác biệt chiết khấu giữa các khu vực trưởng thành (mature) và không trưởng thành (non-mature) nhằm xây dựng các chính sách tái thiết đô thị (như SERS hoặc VERS).

---

## 3. Câu hỏi Phân tích

Nghiên cứu tập trung giải quyết 4 câu hỏi định lượng cốt lõi theo đặc tả:

- **Q1 (Đường cong thời hạn thuê):** Khi thời hạn thuê còn lại ngắn đi, giá căn hộ giảm theo đường cong nào sau khi kiểm soát diện tích, tầng cao, loại căn, khu vực và tháng giao dịch? Đường cong này có giữ được tính ổn định giữa hai thời kỳ: 2017–2022 và 2023–hiện tại không?
- **Q2 (Khác biệt theo khu vực):** Mức chênh lệch giá giữa nhóm căn hộ thuê ngắn (55–65 năm) và nhóm tham chiếu (70–80 năm) có khác nhau giữa các khu vực hành chính hay không? Thứ hạng chiết khấu giữa các khu vực có nhất quán qua thời gian không?
- **Q3 (Chỉ số giá điều chỉnh - Hedonic vs Raw):** Tốc độ tăng giá thô (median price) khác gì so với tốc độ tăng giá thực tế sau khi đã kiểm soát sự thay đổi thành phần căn hộ qua các năm từ năm gốc 2019?
- **Q4 (Hỗ trợ người mua):** Với ngân sách, loại căn, thời hạn tối thiểu và cự ly MRT xác định, khu vực nào có giao dịch đăng ký thực tế phù hợp trong 12 tháng gần nhất?

---

## 4. Nguồn Dữ liệu và Giấy phép

Hệ thống tích hợp dữ liệu từ 4 nguồn mở chính thống:

1. **HDB Resale Flat Prices (data.gov.sg):**
   - *Dataset ID:* `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
   - *Quy mô:* 244,119 dòng giao dịch chính thức từ tháng 01/2017 đến tháng 11/2026.
   - *11 cột bắt buộc:* `month`, `town`, `flat_type`, `block`, `street_name`, `storey_range`, `floor_area_sqm`, `flat_model`, `lease_commence_date`, `remaining_lease`, `resale_price`.
   - *Giấy phép:* Singapore Open Data Licence.
2. **LTA MRT Station Exits (data.gov.sg):**
   - *Dataset ID:* `d_b39d3a0871985372d7e1637193335da5`
   - *Quy mô:* 613 cửa ga MRT/LRT trên toàn Singapore kèm tọa độ kinh vĩ độ WGS84.
   - *Giấy phép:* Singapore Open Data Licence.
3. **NUS 3D HDB Dataset (ualsg/hdb3d-data):**
   - *Kho dữ liệu:* Dữ liệu hình học và tọa độ địa lý của các tòa nhà HDB tại Singapore.
   - *Giấy phép:* Giấy phép mã nguồn mở MIT.
4. **OneMap Search API (SLA):**
   - *Dịch vụ:* Nền tảng bản đồ số quốc gia của Cục Quản lý Đất đai Singapore (SLA). Sử dụng tra cứu tọa độ cho các block mới xây dựng ngoài tập dữ liệu NUS 3D.
   - *Quy tắc gọi:* Rate limit 1 giây/request, có bộ nhớ đệm (cache) để tránh gọi lặp lại.

---

## 5. Kiến trúc ELT

Hệ thống được thiết kế theo mô hình ELT (Extract - Load - Transform) hiện đại với DuckDB đóng vai trò kho dữ liệu embedded cục bộ và dbt quản lý luồng biến đổi:

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
                        dbt_hdb (16 Models)
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
                         pipeline/publish.py (Atomic rename .tmp -> prod)
                                   │
                                   ▼
                 [ data/warehouse/warehouse.duckdb ]
                                   │
                                   ▼
                 Streamlit Dashboard (app/Home.py - Read Only)
```

---

## 6. Kiểm soát Chất lượng Dữ liệu (Quality Control)

Hệ thống áp dụng chốt chặn chất lượng (Quality Gate) tại `pipeline/quality_gate.py` với 12 quy tắc bắt buộc (Blocking Checks):

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
| 11 | Tỷ lệ ghép nối tọa độ block | Khớp >= 98.0% | Khớp 100.00% (9,769/9,769 block) | **PASS** |
| 12 | Độ tươi dữ liệu (`max(month)`) | Không trễ quá 2 tháng | max(month) = 2026-11 (Trễ 0 tháng) | **PASS** |

- **Báo cáo dòng trùng:** Trong 244,119 dòng giao dịch thô, phát hiện chính xác **318 dòng (0.13%)** có giá trị trùng lặp trên cả 11 thuộc tính gốc trong cùng một tháng. Hệ thống tính `occurrence_no` bằng hàm cửa sổ `ROW_NUMBER() OVER (PARTITION BY business_hash ORDER BY source_row_number)` và gắn khóa thay thế `transaction_sk = sha256(business_hash || occurrence_no)`. Giữ nguyên toàn bộ 318 dòng trong bảng fact, không xóa dòng, và ghi nhận tỷ lệ này tại trang vận hành.
- **Cơ chế xuất bản an toàn:** Dữ liệu được ghi vào `warehouse_staging.duckdb`. Chỉ khi Quality Gate đạt 12/12 chỉ tiêu, module `publish.py` mới sao chép sang file tạm `.tmp` và thay thế vào `warehouse.duckdb`.

---

## 7. Phân tích và Phương pháp Kinh tế lượng

Mô hình định giá Hedonic được xây dựng bằng phương pháp bình phương bé nhất (OLS) với sai số chuẩn vững gom cụm theo từng tòa nhà (`block_id = block || '_' || street_name`), nhằm khắc phục hiện tượng tự tương quan không gian giữa các căn hộ trong cùng một khối nhà:

$$\ln(\text{resale\_price}_i) = \alpha + \sum_{k} \beta_k \text{LeaseBand}_{ik} + \gamma \text{Area}_i + \delta \text{Storey}_i + \sum \mu_t \text{Town}_{it} + \sum \lambda_m \text{Month}_{im} + \varepsilon_i$$

- **Quy tắc phân tích:** Được mã hóa và khóa cứng tại `config/analysis_rules.yml` với mã băm SHA-256 `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`. Không thay đổi quy tắc, không điều chỉnh ngưỡng, không lọc lại mẫu.
- **Biến phụ thuộc:** $\ln(\text{resale\_price})$ (logarit tự nhiên của giá bán lại).
- **Hệ số OLS ($\beta$):** Đo lường bằng đơn vị **log points**.
- **Chênh lệch phần trăm:** Được tính theo công thức $(\exp(\beta) - 1) \times 100\%$.
- **Nhóm tham chiếu:** Căn hộ có thời hạn thuê còn lại từ **70 đến 74 năm** ($\beta = 0.0$, chênh lệch $0.0\%$).

---

## 8. Dashboard Trực quan hóa

Dashboard được xây dựng trên nền tảng Streamlit, đọc dữ liệu trực tiếp ở chế độ chỉ đọc từ `warehouse.duckdb`. Giao diện bao gồm 6 màn hình chức năng:

1. **Trang chủ Tổng quan (`Home.py`):** Cung cấp các chỉ số thị trường vĩ mô (tổng giao dịch, trung vị giá toàn kỳ, trung vị giá 12 tháng gần nhất, trung vị thời hạn còn lại, số khu vực và số block), xu hướng giá theo quý và cơ cấu loại căn.
2. **Đường cong Thuê (`1_Duong_cong_thue.py`):** Trực quan hóa đường cong hệ số log và mức chênh lệch giá theo nhóm 5 năm kèm khoảng tin cậy 95% gom cụm block, đối chiếu hai thời kỳ P1 và P2, trình bày bảng số liệu chi tiết và kết luận Q1 = FAIL.
3. **So sánh Khu vực (`2_So_sanh_khu.py`):** Biểu đồ cột thể hiện mức chiết khấu của nhóm căn hộ cũ (55–65 năm) so với nhóm tham chiếu (70–80 năm) trên 13 khu vực đủ điều kiện, phân loại theo tiêu chuẩn HDB Mature / Non-Mature, báo cáo hệ số tương quan hạng Spearman (0.6209).
4. **Giá đã Điều chỉnh (`3_Gia_dieu_chinh.py`):** So sánh chuỗi chỉ số giá thô và chỉ số Hedonic chuẩn hóa (năm gốc 2019 = 100) kèm dải tin cậy 95% cho toàn thị trường và 3 phân khúc loại căn chính (3-Room, 4-Room, 5-Room).
5. **Công cụ Tìm kiếm Khu vực (`4_Cong_cu_tim_khu.py`):** Cho phép người mua lọc dữ liệu 12 tháng gần nhất theo ngân sách, loại căn, thời hạn tối thiểu và cự ly MRT. Bắt buộc hiển thị thông báo: *"Kết quả mô tả giao dịch đã đăng ký gần đây, không phải định giá."* Ẩn các khu vực dưới 10 giao dịch thỏa mãn, không xếp hạng hay gắn nhãn "đáng mua nhất".
6. **Vận hành & Giám sát (`5_Van_hanh.py`):** Giám sát trạng thái pipeline, lịch sử nạp dữ liệu, độ tươi nguồn, biến động snapshot và chi tiết kết quả 12 quy tắc Quality Gate.

---

## 9. Kết quả Phân tích: Quan sát, Diễn giải và Đề xuất

Theo quy định mục 13, phần kết quả được phân tách rõ ràng thành 3 cấp độ:

### 9.1. Quan sát (Số đo Thực nghiệm Trực tiếp)

#### Q1. Đường cong Thời hạn thuê
- **Quy mô mẫu:** Trong giai đoạn 1 (2017–2022), số giao dịch tối thiểu ở một nhóm là 5,879 (nhóm 85–89 năm). Trong giai đoạn 2 (2023–2026), số giao dịch tối thiểu là 2,591 (nhóm 80–84 năm). Cả hai đều vượt ngưỡng >= 1,000 giao dịch.
- **Thứ hạng đơn điệu:** Hệ số OLS tăng đơn điệu theo thời hạn thuê ở cả hai giai đoạn (Spearman rank correlation giữa hệ số hai giai đoạn đạt **1.0000**).
- **Mức chiết khấu căn hộ cũ so với nhóm 70–74 năm:**
  - Nhóm `< 50 năm`: P1 là -0.3104 log points (-26.68%); P2 là -0.3327 log points (-28.30%).
  - Nhóm `50–54 năm`: P1 là -0.2009 log points (-18.20%); P2 là -0.2107 log points (-19.00%).
  - Nhóm `55–59 năm`: P1 là -0.1237 log points (-11.63%); P2 là -0.1017 log points (-9.67%).
  - Nhóm `60–64 năm`: P1 là -0.0350 log points (-3.44%); P2 là -0.0489 log points (-4.77%).
  - Nhóm `65–69 năm`: P1 là -0.0037 log points (-0.37%); P2 là -0.0448 log points (-4.38%).
- **Sai khác giữa hai thời kỳ:**
  - Tại nhóm `80–84 năm`: P1 ghi nhận hệ số +0.0845 log points (+8.82%); P2 ghi nhận hệ số +0.1673 log points (+18.21%). Chênh lệch là **0.0828 log points** (tương đương **9.39 điểm phần trăm**).
  - Ngưỡng khóa quy định: độ chênh lệch <= 0.05 (5 điểm phần trăm).
  - **Kết luận:** **Q1 = FAIL**.

#### Q2. Mức Chênh lệch Thời hạn theo Khu vực (Town Lease Gap)
- **Số khu vực đủ điều kiện (>= 200 giao dịch mỗi nhóm ở cả 2 thời kỳ):** Đạt **13 khu vực** (vượt ngưỡng >= 10 khu).
- **Hệ số tương quan hạng Spearman giữa hai thời kỳ:** Đạt **0.6209** (p = 0.0235, vượt ngưỡng >= 0.60).
- **Phân loại theo chuẩn HDB (Số đo khớp 100% với `analytics.town_lease_gap`):**
  - *Khu vực Mature (7 khu):*
    - TOA PAYOH: P1 = -0.2377 (-21.16%), P2 = -0.2556 (-22.55%).
    - GEYLANG: P1 = -0.2053 (-18.56%), P2 = -0.2674 (-23.47%).
    - BUKIT MERAH: P1 = -0.1526 (-14.15%), P2 = -0.1990 (-18.04%).
    - BEDOK: P1 = -0.1163 (-10.98%), P2 = -0.1469 (-13.66%).
    - ANG MO KIO: P1 = -0.1161 (-10.97%), P2 = -0.2743 (-23.99%).
    - KALLANG/WHAMPOA: P1 = -0.0851 (-8.16%), P2 = -0.1715 (-15.76%).
    - TAMPINES: P1 = +0.0123 (+1.24%), P2 = -0.0197 (-1.95%).
  - *Khu vực Non-Mature (6 khu):*
    - JURONG EAST: P1 = -0.1899 (-17.30%), P2 = -0.1438 (-13.39%).
    - WOODLANDS: P1 = -0.1352 (-12.64%), P2 = -0.0643 (-6.23%).
    - CHOA CHU KANG: P1 = -0.0895 (-8.56%), P2 = -0.0159 (-1.58%).
    - BUKIT BATOK: P1 = -0.0856 (-8.21%), P2 = -0.1034 (-9.83%).
    - JURONG WEST: P1 = -0.0417 (-4.08%), P2 = -0.0835 (-8.01%).
    - HOUGANG: P1 = -0.0340 (-3.34%), P2 = -0.0289 (-2.85%).
- **Kiểm tra độ nhạy Leave-One-Out Spearman:** Khoảng dao động từ **0.5524** (khi bỏ Hougang hoặc Tampines) đến **0.6993** (khi bỏ Ang Mo Kio), giá trị trung bình là **0.6192**.
- **Kết luận:** **Q2 = PASS**.

#### Q3. Chỉ số Giá Điều chỉnh (Hedonic vs Raw)
- **Chuỗi thời gian bao phủ:** Đầy đủ từ năm 2017 đến năm 2026 (10 năm liên tục).
- **Giai đoạn năm đầy đủ (2019 đến 2025):**
  - Giá trung vị thô toàn thị trường tăng từ 400,000 SGD lên 628,000 SGD (**+57.00%**, chỉ số 157.00).
  - Chỉ số Hedonic đã kiểm soát đặc điểm căn hộ tăng từ 100.0 lên 158.87 (**+58.87%**, 95% CI: [158.34, 159.40]).
  - Độ chênh lệch giữa chỉ số thô và chỉ số Hedonic ở năm 2025 là **-1.87 điểm chỉ số**.
- **Dữ liệu năm 2026 (11 tháng đầu năm 2026, 22,053 giao dịch):**
  - Chỉ số giá thô đạt 158.75 (+58.75%), chỉ số Hedonic đạt 159.33 (+59.33%).
- **Giai đoạn 2020–2022:**
  - Chỉ số giá thô ghi nhận mức tăng cao hơn chỉ số Hedonic: năm 2020 cao hơn +3.14 điểm; năm 2021 cao hơn +5.43 điểm; năm 2022 cao hơn +2.61 điểm.
- **Kết luận:** **Q3 = PASS**.

---

### 9.2. Diễn giải (Cách hiểu Có điều kiện)

1. **Về sự không ổn định của Q1:** Đường cong chiết khấu thời hạn thuê không giữ được tính bất biến thời gian, chủ yếu do biến động mạnh tại nhóm 80–84 năm giữa hai thời kỳ (hệ số tăng từ 0.0845 lên 0.1673 log points). Việc trượt tiêu chí 5% cho thấy mức định giá của người mua đối với các căn hộ cận mới (80–84 năm) đã thay đổi đáng kể sau năm 2022 so với giai đoạn trước dịch.
2. **Về phân hóa theo khu vực (Q2):** Phần lớn các khu vực trưởng thành (Toa Payoh, Geylang, Bukit Merah, Ang Mo Kio) có mức chiết khấu sâu (-14% đến -24%) đối với nhóm căn hộ cũ 55–65 năm. Ngược lại, tại một số khu vực như Hougang, Jurong West, hoặc Tampines, khoảng cách giá giữa hai nhóm thời hạn hẹp hơn đáng kể (dưới 8%). Điều này cho thấy tại các khu vực trung tâm lâu đời, người mua phân biệt rất rõ rệt giá trị giữa căn hộ sắp chạm ngưỡng hạn chế CPF/thế chấp so với căn hộ còn dài hạn.
3. **Về sai lệch thành phần (Q3):** Hiện tượng chỉ số thô tăng nhanh hơn chỉ số Hedonic trong các năm 2020–2022 (chênh lệch đỉnh điểm +5.43 điểm vào năm 2021) phản ánh sự dịch chuyển trong cơ cấu giao dịch thực tế: tỷ trọng giao dịch của các căn hộ diện tích lớn hơn hoặc tầng cao hơn đã tăng lên trong giỏ hàng thị trường, khiến giá trung vị thô tăng nhanh hơn mức tăng giá thuần túy của một căn hộ tiêu chuẩn. Đến giai đoạn 2024–2025, hai chỉ số đã tiệm cận nhau trở lại.

---

### 9.3. Đề xuất (Việc cần làm và Chỉ số Theo dõi)

1. **Đối với Người mua nhà:**
   - Khi cân nhắc căn hộ có thời hạn thuê dưới 60 năm tại các khu vực trưởng thành (Toa Payoh, Geylang, Ang Mo Kio), cần dự liệu biên chiết khấu từ 18% đến 24% so với mặt bằng căn hộ 70–80 năm để tránh mua ở mức định giá chưa phản ánh khấu hao thời hạn.
   - Theo dõi chỉ số: Đơn giá trên m² điều chỉnh theo tuổi thuê (`price_per_sqm / remaining_lease_years`) thay vì chỉ nhìn vào mức giá danh nghĩa.
2. **Đối với Tổ chức Tín dụng và Định giá:**
   - Áp dụng hệ số chiết khấu phi tuyến theo từng khu vực thay vì dùng một tỷ lệ khấu hao chung cho toàn bộ thị trường Singapore.
   - Theo dõi chỉ số: Khoảng cách giữa chỉ số giá thô và chỉ số Hedonic (`gap_raw_vs_hedonic`) để nhận diện thời điểm cơ cấu giao dịch bị méo mó bởi các phân khúc cục bộ.
3. **Đối với Kỹ sư Vận hành Hệ thống:**
   - Thiết lập ngưỡng cảnh báo tự động khi số lượng giao dịch ở nhóm thời hạn ngắn (< 50 năm) có biến động trung vị tháng vượt quá 30%.
   - Theo dõi chỉ số: Tỷ lệ dòng trùng lặp `business_hash` (duy trì dưới 0.2%) và độ trễ dữ liệu nguồn không vượt quá 2 tháng lịch dương.

---

## 10. Giới hạn Nghiên cứu (Bắt buộc theo Mục 14)

Để đảm bảo tính trung thực khoa học và tránh việc người đọc suy diễn sai, nghiên cứu nêu rõ 11 giới hạn bắt buộc sau:

1. **Dữ liệu là giao dịch đã đăng ký:** Bộ dữ liệu chỉ ghi nhận các giao dịch mua bán lại đã hoàn tất thủ tục pháp lý tại HDB, không phản ánh toàn bộ cung - cầu tiềm năng hoặc các giao dịch bị hủy bỏ.
2. **Đơn vị thời gian theo tháng:** Dữ liệu được ghi nhận theo tháng (`month`), không có ngày giao dịch cụ thể, do đó không phản ánh được biến động giá trong nội bộ tháng.
3. **Không có vị trí căn hộ chính xác:** Dữ liệu công khai chỉ cung cấp số block và khoảng tầng (ví dụ "04 TO 06"), không có số căn hộ cụ thể (unit number). Các yếu tố vi mô như căn góc, hướng nắng, hướng gió không thể kiểm soát.
4. **Giá bán không phải giá thuê:** Giá bán lại phản ánh quyền sở hữu có thời hạn của người mua, hoàn toàn khác biệt với giá thuê nhà ở ngắn hạn trên thị trường cho thuê.
5. **Chưa điều chỉnh lạm phát:** Tất cả số liệu giá trị trong nghiên cứu là giá danh nghĩa bằng Đô-la Singapore (SGD) tại thời điểm đăng ký, chưa điều chỉnh theo Chỉ số Giá tiêu dùng (CPI).
6. **Thành phần căn hộ thay đổi theo thời gian:** Tỷ trọng căn hộ theo loại phòng, độ tuổi và vị trí bán ra trong mỗi tháng không đồng nhất.
7. **Thời hạn thuê gắn liền với tuổi thọ và chất lượng công trình:** Các căn hộ có thời hạn thuê ngắn cũng đồng thời là các căn hộ xây dựng từ thập niên 1970–1980 với tiêu chuẩn vật liệu, thiết kế thang máy và tiện ích cũ hơn các căn hộ mới.
8. **Khoảng cách địa lý là đường thẳng:** Cự ly đến ga MRT gần nhất và khu trung tâm thương mại (CBD Raffles Place) được tính bằng khoảng cách đường thẳng Haversine trên tọa độ kinh vĩ độ, chưa phản ánh khoảng cách đi bộ thực tế trên mạng lưới đường phố.
9. **Hạ tầng MRT cố định theo thời điểm hiện tại:** Mô hình tính khoảng cách dựa trên mạng lưới 613 cửa ga MRT/LRT hiện hành, không phản ánh lịch sử mở cửa của các tuyến ga mới trong quá khứ.
10. **Kết quả phản ánh mối liên quan, không phải quan hệ nhân quả:** Các hệ số hồi quy chỉ mô tả tương quan thống kê có điều kiện giữa thời hạn thuê và giá bán lại trong tập dữ liệu quan sát, không chứng minh mối quan hệ nhân quả.
11. **Không phải tư vấn tài chính:** Các phân tích và công cụ tìm kiếm trong dự án phục vụ mục đích nghiên cứu học thuật, không cấu thành lời khuyên đầu tư hoặc khuyến nghị tài chính cá nhân.

---

## 11. Vận hành Thực tế

### 11.1. Chu kỳ thực thi
Hệ thống được thiết kế để thực thi định kỳ hàng tháng (khi data.gov.sg phát hành snapshot giao dịch mới) hoặc hằng ngày. Quá trình kiểm tra SHA-256 đối với file CSV tải về đảm bảo nếu dữ liệu nguồn không thay đổi, hệ thống ghi nhận trạng thái `no_change` trong `manifest.json` và không ghi đè dữ liệu thừa.

### 11.2. Cơ chế khóa file trên hệ điều hành Windows
Trên môi trường Windows, khi tiến trình Streamlit Dashboard hoặc một kết nối DuckDB đang mở ở chế độ đọc (`read_only=True`), hệ điều hành sẽ thiết lập khóa file. Lệnh `os.replace` khi thực hiện xuất bản nguyên tử từ `warehouse_staging.duckdb` sang `warehouse.duckdb` sẽ gặp lỗi `PermissionError: [WinError 5] Access is denied`.  
Để khắc phục, quy trình vận hành quy định rõ:
1. Module kết nối `app/db.py` của Streamlit tự động đóng kết nối ngay sau khi hoàn thành truy vấn (`finally: con.close()`).
2. Khi thực hiện quy trình nạp và xuất bản toàn trình (`pipeline/run_pipeline.py`), hệ thống dọn dẹp các tệp tạm `.tmp` và bảo toàn nguyên vẹn tệp kho dữ liệu đang phục vụ nếu phát hiện khóa file.

---

## 12. Kết luận

Dự án đã xây dựng thành công một hệ thống ELT hoàn chỉnh, khép kín và tự động hóa cao từ khâu trích xuất dữ liệu gốc trên data.gov.sg đến khâu chuyển đổi dbt, kiểm định chất lượng nghiêm ngặt và phục vụ dashboard tương tác.

Về mặt học thuật và thực nghiệm:
- **Q1 (FAIL):** Đường cong chiết khấu thời hạn thuê giảm đơn điệu theo số năm còn lại (Spearman = 1.0), nhưng mức chênh lệch giữa hai thời kỳ ở nhóm 80–84 năm đạt 8.28% (vượt ngưỡng khóa 5%), cho thấy sự thiếu ổn định thời gian ở phân khúc căn hộ cận mới sau dịch. Dự án ghi nhận trung thực kết quả này thay vì nới lỏng ngưỡng khóa.
- **Q2 (PASS):** Mức chiết khấu thời hạn thuê có sự phân hóa sâu sắc và có tính hệ thống giữa các khu vực hành chính (Spearman thứ hạng = 0.6209 trên 13 khu vực đủ điều kiện). Các khu vực trưởng thành (Mature Towns) chịu mức chiết khấu sâu hơn rõ rệt đối với căn hộ cũ 55–65 năm.
- **Q3 (PASS):** Chỉ số Hedonic đã kiểm soát thành công sự dịch chuyển cơ cấu căn hộ từ năm gốc 2019 đến năm 2025 (+58.87% so với mức tăng thô +57.00%), bóc tách được mức sai lệch thành phần trong các năm 2020–2022.

---

## 13. Phụ lục

### 13.1. Từ điển Dữ liệu (Bảng Fact cốt lõi)
Tài liệu chi tiết tại [docs/data_dictionary.md](file:///d:/video/hdb_elt/docs/data_dictionary.md).

| Tên cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `transaction_sk` | VARCHAR (SHA-256) | Khóa thay thế duy nhất của giao dịch (`sha256(business_hash \|\| occurrence_no)`) |
| `business_hash` | VARCHAR (SHA-256) | Mã băm xác định từ 11 thuộc tính gốc đã chuẩn hóa |
| `occurrence_no` | INTEGER | Thứ tự xuất hiện của dòng giao dịch có cùng `business_hash` |
| `month` | VARCHAR | Tháng đăng ký giao dịch (định dạng `YYYY-MM`) |
| `town` | VARCHAR | Khu vực hành chính thị trấn HDB |
| `flat_type` | VARCHAR | Loại căn hộ (ví dụ: `3 ROOM`, `4 ROOM`, `5 ROOM`) |
| `block` | VARCHAR | Số hiệu block tòa nhà |
| `street_name` | VARCHAR | Tên đường |
| `storey_mid` | DOUBLE | Trung vị của khoảng tầng giao dịch |
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

### 13.3. Hướng dẫn Tái lập Môi trường và Thực thi
```powershell
# 1. Di chuyển vào thư mục dự án
Set-Location "D:\video\hdb_elt"

# 2. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 3. Chạy toàn bộ pipeline tích hợp (Extract, Load, dbt, Analysis, Quality Gate, Publish)
python pipeline/run_pipeline.py

# 4. Kiểm thử chất lượng bằng dbt và pytest
Set-Location "dbt_hdb"
dbt test --profiles-dir .
Set-Location ".."
pytest -v

# 5. Khởi chạy giao diện Dashboard
streamlit run app/Home.py
```
