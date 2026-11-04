# Báo cáo Nghiệm thu Kỹ thuật (Acceptance Report)

> **Dự án:** Hệ thống ELT và Dashboard phân tích giá căn hộ HDB Singapore theo thời hạn thuê còn lại  
> **Thời điểm lập:** 04/11/2026 16:30 UTC+7  
> **Trạng thái:** DỪNG TRƯỚC GIAI ĐOẠN 6 (Đã hoàn thành toàn bộ Giai đoạn 0 đến Giai đoạn 5)  
> **Môi trường thực thi:** Windows 10/11, PowerShell, Python 3.12, DuckDB, dbt-duckdb, Streamlit  
> **Người thực hiện:** Data Engineer  

---

## 1. Bảng Đánh giá Tiêu chí Nghiệm thu (Theo Mục 15 Đặc tả)

| STT | Tiêu chí nghiệm thu (Mục 15) | Trạng thái | Bằng chứng / File kết quả | Ghi chú |
|:---:|---|:---:|---|---|
| 1 | **Giai đoạn 0 đạt** (Kiểm tra nguồn API HDB, MRT, NUS 3D, OneMap, giấy phép, độ tươi) | **ĐẠT** | [docs/source_check.md](file:///d:/video/hdb_elt/docs/source_check.md)<br>[docs/source_check_raw.json](file:///d:/video/hdb_elt/docs/source_check_raw.json) | 244,119 dòng HDB, đủ 11 cột, max(month)=2026-11, SHA-256 xác thực. |
| 2 | **`python pipeline/run_pipeline.py` chạy từ đầu đến cuối** | **ĐẠT** | [pipeline/run_pipeline.py](file:///d:/video/hdb_elt/pipeline/run_pipeline.py)<br>Pipeline log: `run_id=d6848d4e-8039-4ecf-9470-6975e372c3a2` | Chạy thành công toàn bộ 8 bước: Extract -> Load -> dbt -> Analysis -> Quality Gate -> Atomic Publish. Mã thoát 0. |
| 3 | **Raw được lưu theo từng lần chạy và có manifest** | **ĐẠT** | Thư mục `data/raw/hdb_resale/run_date=2026-11-04/`<br>[manifest.json](file:///d:/video/hdb_elt/data/raw/hdb_resale/run_date=2026-11-04/run_id=aa50ca00-8d79-4ba6-9762-5d8e2e6b9780/manifest.json) | Cấu trúc bất biến kèm đầy đủ metadata: run_id, timestamp, SHA-256, row_count, byte_size, columns, status. |
| 4 | **Chạy lại không tạo dữ liệu trùng** | **ĐẠT** | `pipeline/extract_hdb.py`<br>Log Run 2: `status: no_change` | Cơ chế so sánh SHA-256 với snapshot trước; bảng fact sử dụng `occurrence_no` và `transaction_sk` định danh duy nhất. |
| 5 | **`dbt build` thành công** | **ĐẠT** | Thư mục [dbt_hdb/](file:///d:/video/hdb_elt/dbt_hdb/)<br>16 models, 16 tests | PASS 16/16 models (11 tables, 5 views); PASS 16/16 data tests (uniqueness, not null, constraints). |
| 6 | **pytest thành công** | **ĐẠT** | [tests/](file:///d:/video/hdb_elt/tests/)<br>8/8 unit & integration tests | PASS 100% trong 2.87s (kiểm thử parser, manifest, quality gate, đối chiếu raw-fact). |
| 7 | **Quality Gate chặn được file lỗi trong kiểm thử** | **ĐẠT** | [tests/test_quality_gate.py](file:///d:/video/hdb_elt/tests/test_quality_gate.py) | Chứng minh chặn xuất bản thành công ở 3 tình huống lỗi: (1) Thiếu cột, (2) File trống, (3) Số dòng giảm > 1%. |
| 8 | **Publish giữ dashboard ở phiên bản tốt gần nhất khi lỗi** | **ĐẠT** | [pipeline/publish.py](file:///d:/video/hdb_elt/pipeline/publish.py)<br>[tests/test_quality_gate.py](file:///d:/video/hdb_elt/tests/test_quality_gate.py) | Xuất bản nguyên tử qua file `.tmp`. Nếu Quality Gate thất bại, `warehouse.duckdb` giữ nguyên trạng thái cũ. |
| 9 | **Q1 đạt (Đường cong thời hạn thuê ổn định)** | **CHƯA ĐẠT**<br>*(FAIL)* | [docs/analysis_results.md](file:///d:/video/hdb_elt/docs/analysis_results.md)<br>[config/analysis_rules.yml](file:///d:/video/hdb_elt/config/analysis_rules.yml) | Mẫu đạt (min 2,591 tx/nhóm), Spearman đạt 1.0 (tăng đơn điệu), nhưng chênh lệch tuyệt đối nhóm 80-84 năm là 8.28% > ngưỡng khóa 5.0%. Báo cáo trung thực theo mục 15: *đường cong không ổn định sau đại dịch*. |
| 10 | **Ít nhất một trong Q2 hoặc Q3 đạt** | **ĐẠT**<br>*(Cả 2 đều ĐẠT)* | [analysis/town_lease_gap.py](file:///d:/video/hdb_elt/analysis/town_lease_gap.py)<br>[analysis/price_index.py](file:///d:/video/hdb_elt/analysis/price_index.py) | **Q2 ĐẠT:** 13 khu vực đủ điều kiện (ngưỡng >= 10), Spearman thứ hạng 0.6209 (ngưỡng >= 0.60).<br>**Q3 ĐẠT:** Đủ các năm 2017-2026 cho 3 loại căn kèm 95% CI gom cụm block. |
| 11 | **Q4 hoạt động với bộ lọc và không có điểm "đáng mua"** | **ĐẠT** | [app/pages/4_Cong_cu_tim_khu.py](file:///d:/video/hdb_elt/app/pages/4_Cong_cu_tim_khu.py)<br>[docs/screenshots/budget_search.png](file:///d:/video/hdb_elt/docs/screenshots/budget_search.png) | Lọc động theo Ngân sách, Loại căn, Thời hạn tối thiểu, MRT. Có câu cảnh báo bắt buộc, ẩn khu < 10 tx, tuyệt đối không chấm điểm hay gán nhãn "đáng mua". |
| 12 | **Dashboard đọc dữ liệu thật và có trang vận hành** | **ĐẠT** | [app/Home.py](file:///d:/video/hdb_elt/app/Home.py)<br>[app/pages/5_Van_hanh.py](file:///d:/video/hdb_elt/app/pages/5_Van_hanh.py)<br>[docs/screenshots/](file:///d:/video/hdb_elt/docs/screenshots/) | Kết nối `warehouse.duckdb` (244,119 dòng fact), không có số liệu hardcode. Trang Vận hành hiển thị đủ lịch sử run và 12 điều kiện Quality Gate. |
| 13 | **Có ít nhất 7 lần chạy theo lịch, kể cả lần `no_change`** | **CHƯA KIỂM THỬ** | Mục tiêu Giai đoạn 6 | Hiện tại hệ thống đang dừng trước Giai đoạn 6 theo đúng chỉ thị (chưa cấu hình Task Scheduler khi chưa có phê duyệt). |
| 14 | **README cho phép người khác chạy lại** | **ĐẠT** | [README.md](file:///d:/video/hdb_elt/README.md) | Cung cấp đầy đủ hướng dẫn thiết lập môi trường, cài đặt package, thực thi pipeline, chạy dbt, pytest và khởi chạy Streamlit. |
| 15 | **Báo cáo có giới hạn và nguồn dữ liệu** | **ĐẠT** | [docs/analysis_results.md](file:///d:/video/hdb_elt/docs/analysis_results.md)<br>[docs/source_check.md](file:///d:/video/hdb_elt/docs/source_check.md)<br>Các trang Dashboard | Đầy đủ 11 giới hạn bắt buộc theo mục 14 đặc tả; trích dẫn rõ giấy phép Singapore Open Data Licence và nguồn dữ liệu. |
| 16 | **Không có token hoặc dữ liệu raw lớn trong Git** | **ĐẠT** | [.gitignore](file:///d:/video/hdb_elt/.gitignore) | Git đã bỏ qua: `data/raw/`, `data/warehouse/`, `logs/`, `.env`. Không chứa bất kỳ API key, secret, token hay dữ liệu cá nhân nào. |

---

## 2. Danh sách Lệnh Thực tế Đã Chạy

```powershell
# Giai đoạn 0: Kiểm tra nguồn dữ liệu
python scripts/check_sources.py

# Giai đoạn 1: Trích xuất và geocoding
python pipeline/extract_hdb.py
python pipeline/extract_mrt.py
python pipeline/extract_blocks.py

# Giai đoạn 2: Nạp dữ liệu thô và dbt transformations
python pipeline/load_raw.py
Set-Location "dbt_hdb"
dbt build --profiles-dir .
dbt test --profiles-dir .
Set-Location ".."

# Giai đoạn 3: Quality Gate, Publish và Pytest
python pipeline/quality_gate.py
python pipeline/publish.py
pytest -v

# Giai đoạn 4: Phân tích kinh tế lượng
python analysis/run_analysis.py
python pipeline/publish.py

# Giai đoạn 5: Khởi chạy Dashboard và Chụp ảnh màn hình
python -m streamlit run app/Home.py --server.port 8501 --server.headless true
python scripts/capture_screenshots.py

# Toàn trình tích hợp (End-to-End Pipeline)
python pipeline/run_pipeline.py
```

---

## 3. Kết quả Chi tiết Pytest và dbt

### 3.1. Kết quả Pytest (`pytest -v`)
- **Tổng số bài kiểm thử:** 8
- **Kết quả:** **8/8 PASS (100%)**
- **Thời gian thực thi:** 2.87 giây
- **Chi tiết từng test case:**
  1. `tests/test_parsers.py::test_parse_remaining_lease`: PASS (Phân tích chuẩn xác cả 2 định dạng: "61 years 04 months" -> 61.33 năm và "60 years" -> 60.00 năm).
  2. `tests/test_parsers.py::test_parse_storey_range`: PASS (Trích xuất trung vị tầng chính xác, ví dụ "04 TO 06" -> 5).
  3. `tests/test_parsers.py::test_business_hash_deterministic`: PASS (Mã băm SHA-256 xác định, phân biệt chính xác dòng khác nhau).
  4. `tests/test_manifest.py::test_manifest_schema_validation`: PASS (Xác thực cấu trúc JSON manifest đúng chuẩn schema).
  5. `tests/test_quality_gate.py::test_quality_gate_blocks_missing_columns`: PASS (Chặn xuất bản khi file thiếu cột, Quality Gate trả về FAIL).
  6. `tests/test_quality_gate.py::test_quality_gate_blocks_empty_file`: PASS (Chặn xuất bản khi file dữ liệu trống 0 byte).
  7. `tests/test_quality_gate.py::test_quality_gate_blocks_row_count_drop`: PASS (Chặn xuất bản khi số lượng dòng giảm quá 1% so với snapshot trước).
  8. `tests/test_fact_raw_reconciliation.py::test_fact_raw_random_sample_reconciliation`: PASS (Rút ngẫu nhiên 20 dòng từ bảng fact và đối chiếu khớp 100% từng trường về dòng tương ứng trong file raw CSV theo `source_row_number`).

### 3.2. Kết quả dbt Build (`dbt build --profiles-dir .`)
- **Tổng số mô hình:** 16 (11 tables, 5 views)
- **Tổng số data tests:** 16
- **Kết quả:** **16/16 models PASS, 16/16 tests PASS (100%)**
- **Thời gian thực thi:** 13.16 giây
- **Danh sách mô hình đã build:**
  - *Staging:* `stg_hdb_resale` (tính `business_hash`, `occurrence_no`, `transaction_sk`), `stg_mrt_exits`, `stg_block_location`.
  - *Intermediate:* `int_resale_parsed`, `int_block_mrt_distance` (Haversine MRT & CBD), `int_resale_enriched`.
  - *Marts:* `dim_month`, `dim_town`, `dim_block`, `dim_flat_type`, `fct_resale_transaction` (244,119 dòng), `mart_town_month` (46,044 dòng), `mart_budget_search` (11,286 dòng).
  - *Operations:* `ops_pipeline_run`, `ops_snapshot_delta`, `ops_source_freshness`.

---

## 4. Kết quả Phân tích Kinh tế lượng (Q1, Q2, Q3)

Quy tắc phân tích được cố định tại `config/analysis_rules.yml` với mã băm SHA-256: `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`. Tuyệt đối không thay đổi ngưỡng hoặc lọc mẫu theo mục 8 đặc tả.

### 4.1. Câu hỏi Q1: Đường cong Thời hạn thuê (Lease Curve)
- **Phương pháp:** Hồi quy OLS Hedonic $\log(\text{resale\_price})$ theo nhóm thời hạn 5 năm (tham chiếu 70-74 năm), kiểm soát diện tích, tầng, loại căn, khu vực, tháng; sai số gom cụm theo `block_id`. Phân tích trên hai thời kỳ: P1 (2017–2022) và P2 (2023–2026).
- **Kết quả tiêu chí:**
  - Quy mô mẫu: ĐẠT (P1 tối thiểu 5,879 tx/nhóm; P2 tối thiểu 2,591 tx/nhóm; vượt xa ngưỡng >= 1,000).
  - Spearman rank correlation: **1.0000** (ĐẠT, vượt ngưỡng >= 0.90; đường cong tăng đơn điệu tuyệt đối theo số năm còn lại).
  - Độ ổn định (Sai khác tuyệt đối P1 vs P2): **8.28%** ở nhóm 80-84 năm (**CHƯA ĐẠT**, vượt ngưỡng khóa <= 5.0%).
- **Trạng thái:** **FAIL** (Không đạt điều kiện ổn định).
- **Phân tích hiện tượng thực tế:**
  - Nhóm căn hộ dưới 50 năm chiết khấu sâu: -26.7% (P1) và -28.3% (P2).
  - Nhóm 50-54 năm chiết khấu -18.2% (P1) và -19.0% (P2).
  - Nhóm 60-64 năm chiết khấu -3.4% (P1) và -4.8% (P2).
  - **Lý do trượt:** Nhóm 80-84 năm ở P1 chỉ cao hơn nhóm tham chiếu +8.80%, nhưng sang P2 sau đại dịch tăng vọt lên +18.22% (+9.42 điểm phần trăm theo log-points, tương đương 8.28% sai khác tuyệt đối). Đây là giai đoạn các dự án BTO xây dựng giai đoạn 2013-2017 đạt hạn MOP 5 năm ồ ạt bước vào thị trường chuyển nhượng với mức giá kỷ lục, tạo nên bước nhảy thị trường. Dự án báo cáo trung thực hiện tượng này thay vì điều chỉnh ngưỡng để "làm đẹp" kết quả.

### 4.2. Câu hỏi Q2: Khác biệt Mức chênh lệch Thời hạn theo Khu vực (Town Lease Gap)
- **Phương pháp:** So sánh nhóm căn hộ cũ (55-65 năm) với nhóm tham chiếu (70-80 năm) trong từng khu vực, kiểm soát diện tích, tầng, loại căn, tháng; sai số gom cụm theo `block_id`.
- **Kết quả tiêu chí:**
  - Số khu vực đủ điều kiện (>= 200 giao dịch mỗi nhóm ở cả 2 thời kỳ): **13 khu vực** (ĐẠT, vượt ngưỡng >= 10 khu).
  - Spearman thứ hạng mức chênh lệch giữa P1 và P2: **0.6209** (ĐẠT, vượt ngưỡng >= 0.60).
- **Trạng thái:** **PASS**.
- **Quan sát nổi bật:**
  - Các khu trưởng thành (Mature Towns) chịu mức phạt thời hạn thuê sâu nhất: Toa Payoh (-24.1% ở P1, -21.4% ở P2), Ang Mo Kio (-20.9% ở P1, -19.8% ở P2), Geylang (-19.2% ở P1, -18.7% ở P2).
  - Các khu không trưởng thành (Non-mature Towns) có mức chênh lệch nhẹ hơn: Tampines (-7.8% ở P1, -8.4% ở P2), Hougang (-4.9% ở P1, -5.2% ở P2), Jurong West (-1.9% ở P1, -2.1% ở P2).

### 4.3. Câu hỏi Q3: Giá Thực sự Tăng bao nhiêu? (Price Index Hedonic vs Raw)
- **Phương pháp:** Xây dựng chuỗi chỉ số giá thô (median price) và chuỗi chỉ số giá Hedonic chuẩn hóa kiểm soát đặc điểm căn hộ (diện tích, tầng, khu vực, loại căn, thời hạn thuê) lấy năm gốc 2019 = 100, kèm dải tin cậy 95% gom cụm block.
- **Kết quả tiêu chí:**
  - Đủ các năm 2017 đến 2026: **ĐẠT** (10 năm liên tục).
  - Phân rã cho toàn bộ thị trường và 3 loại căn chính (3-Room, 4-Room, 5-Room): **ĐẠT**.
  - Có dải tin cậy 95% gom cụm block: **ĐẠT**.
- **Trạng thái:** **PASS**.
- **Quan sát nổi bật:**
  - Đến năm 2026, giá thô tăng +58.8% trong khi giá Hedonic chuẩn hóa tăng +59.3%.
  - Giai đoạn 2020-2022, tốc độ tăng giá thô cao hơn giá Hedonic từ 2.6 - 5.4 điểm phần trăm do người mua săn lùng các căn hộ lớn (4-Room, 5-Room) mới hoàn thành để đáp ứng nhu cầu làm việc tại nhà trong đại dịch COVID-19.

---

## 5. Cảnh báo Dữ liệu (Data Warnings)

Hệ thống ghi nhận 2 cảnh báo dữ liệu không chặn xuất bản nhưng cần lưu ý:
1. **Dữ liệu trùng cả 11 thuộc tính gốc:** Phát hiện **318 giao dịch (0.13%)** trong tổng số 244,119 dòng có thông tin hoàn toàn trùng nhau trong cùng một tháng đăng ký. Đây là hiện tượng thật của thị trường (ví dụ cùng một tầng của cùng một block có 2 căn hộ diện tích giống nhau bán cùng mức giá trong tháng). Hệ thống đã đánh số `occurrence_no` và giữ nguyên 100% trong bảng fact, không xóa dòng.
2. **Căn hộ nhóm thời hạn 90+ năm:** Số lượng căn hộ thuộc nhóm thời hạn trên 90 năm chịu hiệu ứng "căn hộ mới đạt hạn chuyển nhượng tối thiểu MOP 5 năm", mức giá phản ánh cả giá trị mới xây lẫn vị trí quy hoạch mới, do đó được tách riêng trong phân tích để tránh làm nhiễu đường cong suy giảm giá trị theo tuổi thuê.

---

## 6. Các Tồn tại Kỹ thuật Còn lại (Technical Debt & Limitations)

1. **Chưa triển khai Giai đoạn 6 (Lịch chạy Task Scheduler / Cron):** Theo đúng chỉ thị của tài liệu đặc tả, hệ thống DỪNG TRƯỚC GIAI ĐOẠN 6 để chờ phê duyệt của chủ dự án. Chưa có 7 lần chạy theo lịch tự động.
2. **Q1 không đạt chỉ tiêu ổn định:** Do biến động thị trường sau đại dịch tại nhóm 80-84 năm vượt ngưỡng 5%, giả định về tính bất biến thời gian của đường cong chiết khấu thời hạn thuê bị vi phạm ở phân khúc căn hộ cận mới.
3. **Khoảng cách MRT và CBD:** Hiện tính theo đường thẳng (Haversine) dựa trên tọa độ WGS84, chưa tính theo mạng lưới đi bộ thực tế (network walking distance).

---

## 7. Các Việc Chủ Dự án Cần Quyết định (Mục 17 Đặc tả)

Căn cứ theo mục 17 của tài liệu đặc tả, Data Engineer kính đề xuất Chủ dự án / Giảng viên hướng dẫn xem xét và cho ý kiến quyết định về 4 nội dung sau:

1. **Hình thức cập nhật dữ liệu:** Xác nhận môn học / đồ án có chấp nhận mô hình cập nhật theo batch định kỳ (hàng ngày hoặc hàng tháng khi data.gov.sg ra snapshot mới) hay bắt buộc phải có streaming/realtime.
2. **Xử lý kết quả Q1:** Q1 trượt tiêu chí ổn định tuyệt đối (8.28% so với ngưỡng 5%) do nguyên nhân khách quan từ thị trường. Xác nhận chấp nhận giữ nguyên báo cáo phân tích trung thực hiện tượng thị trường (như hiện tại) hay muốn thu hẹp phạm vi mẫu (loại trừ giai đoạn biến động sau 2023).
3. **Phê duyệt chuyển sang Giai đoạn 6:** Xác nhận có cho phép đăng ký kịch bản chạy tự động hằng ngày qua Windows Task Scheduler (`scripts/register_task.ps1`) để tích lũy 7 lần chạy theo dõi hay không.
4. **Yêu cầu hạ tầng nâng cao (Giai đoạn 7):** Xác nhận đồ án có yêu cầu bắt buộc phải bổ sung Apache Airflow, MinIO (S3-compatible Object Storage) hoặc Docker Compose để chấm điểm tối đa hay hệ thống ELT DuckDB + dbt hiện tại đã đủ đáp ứng yêu cầu.

---

## 8. Ảnh chụp Màn hình Dashboard (Giai đoạn 5)

Toàn bộ 6 ảnh màn hình được chụp tự động ở độ phân giải máy tính để bàn (1920x1080) lưu tại `docs/screenshots/`:
- **Trang chủ Tổng quan:** `docs/screenshots/home_overview.png`
- **Đường cong Thuê (Q1):** `docs/screenshots/lease_curve.png`
- **So sánh Khu vực (Q2):** `docs/screenshots/town_comparison.png`
- **Chỉ số Giá Điều chỉnh (Q3):** `docs/screenshots/price_index.png`
- **Công cụ Tìm Khu vực (Q4):** `docs/screenshots/budget_search.png`
- **Giám sát Vận hành & Quality Gate:** `docs/screenshots/operations_quality.png`

