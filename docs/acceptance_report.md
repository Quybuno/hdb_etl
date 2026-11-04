# Báo cáo Nghiệm thu Kỹ thuật (Technical Acceptance Report)

> **Dự án:** Hệ thống ELT và Dashboard phân tích giá căn hộ HDB Singapore theo thời hạn thuê còn lại  
> **Thời điểm cập nhật:** 04/11/2026  
> **Trạng thái:** DỪNG TRƯỚC GIAI ĐOẠN 6 (Đã hoàn thành Giai đoạn 0 đến Giai đoạn 5)  
> **Môi trường thực thi:** Windows 10/11, PowerShell, Python 3.12, DuckDB, dbt-duckdb, Streamlit  
> **Người thực hiện:** Kỹ sư Dữ liệu (Data Engineer)  

---

## 1. Bảng Đánh giá Tiêu chí Nghiệm thu (Theo Mục 15 Đặc tả)

| STT | Tiêu chí nghiệm thu (Mục 15) | Trạng thái | Bằng chứng / Đường dẫn file / Số test | Ghi chú kỹ thuật |
|:---:|---|:---:|---|---|
| 1 | **Giai đoạn 0 đạt** | **ĐẠT** | Báo cáo: [docs/source_check.md](file:///d:/video/hdb_elt/docs/source_check.md)<br>Dữ liệu đo: [docs/source_check_raw.json](file:///d:/video/hdb_elt/docs/source_check_raw.json) | 244,119 dòng HDB, đủ 11 cột, max(month)=2026-11, SHA-256 xác thực. Đủ thông tin giấy phép Open Data Licence. |
| 2 | **`python pipeline/run_pipeline.py` chạy từ đầu đến cuối** | **ĐẠT** | File thực thi: [pipeline/run_pipeline.py](file:///d:/video/hdb_elt/pipeline/run_pipeline.py)<br>Phiên chạy: `run_id=d6848d4e-8039-4ecf-9470-6975e372c3a2` | Hoàn tất 8 bước liên hoàn từ trích xuất, nạp dữ liệu, dbt build, phân tích, quality gate đến xuất bản. Mã thoát 0. |
| 3 | **Raw được lưu theo từng lần chạy và có manifest** | **ĐẠT** | Thư mục: `data/raw/hdb_resale/run_date=2026-11-04/`<br>Metadata: [manifest.json](file:///d:/video/hdb_elt/data/raw/hdb_resale/run_date=2026-11-04/run_id=aa50ca00-8d79-4ba6-9762-5d8e2e6b9780/manifest.json) | Lưu trữ bất biến kèm đầy đủ trường metadata: run_id, timestamp, SHA-256, row_count, byte_size, columns, status. |
| 4 | **Chạy lại không tạo dữ liệu trùng** | **ĐẠT** | Kịch bản: [pipeline/extract_hdb.py](file:///d:/video/hdb_elt/pipeline/extract_hdb.py)<br>Manifest Run 2: `status: no_change` | So sánh SHA-256 với snapshot trước; bảng fact sử dụng `occurrence_no` và `transaction_sk` định danh riêng cho từng dòng. |
| 5 | **`dbt build` thành công** | **ĐẠT** | Thư mục mô hình: [dbt_hdb/models/](file:///d:/video/hdb_elt/dbt_hdb/models/)<br>Kết quả: 16 models, 16 data tests | PASS 16/16 models (11 bảng, 5 view) trong 13.16s; PASS 16/16 data tests (uniqueness, not null) trong 1.87s. |
| 6 | **pytest thành công** | **ĐẠT** | Thư mục kiểm thử: [tests/](file:///d:/video/hdb_elt/tests/)<br>Kết quả: **10/10 tests PASS** | PASS 100% trong 3.74s (kiểm thử parser, manifest, quality gate, đối chiếu raw-fact, kiểm tra tính bất biến hash). |
| 7 | **Quality Gate chặn được file lỗi trong kiểm thử** | **ĐẠT** | File test: [tests/test_quality_gate.py](file:///d:/video/hdb_elt/tests/test_quality_gate.py) | Kiểm thử thành công 3 tình huống lỗi: (1) Thiếu cột, (2) File rỗng 0 byte, (3) Số dòng giảm > 1%. |
| 8 | **Publish giữ dashboard ở phiên bản tốt gần nhất khi lỗi** | **ĐẠT** | Module: [pipeline/publish.py](file:///d:/video/hdb_elt/pipeline/publish.py)<br>File test: `tests/test_quality_gate.py` | Kiểm thử xác nhận file `warehouse.duckdb` có mã hash SHA-256 trước và sau lần xuất bản lỗi trùng khớp hoàn toàn. |
| 9 | **Q1 đạt (Đường cong thời hạn thuê ổn định)** | **CHƯA ĐẠT**<br>*(FAIL)* | Kết quả: [docs/analysis_results.md](file:///d:/video/hdb_elt/docs/analysis_results.md)<br>Quy tắc: [config/analysis_rules.yml](file:///d:/video/hdb_elt/config/analysis_rules.yml) | Mẫu đạt, Spearman đạt 1.0, nhưng sai khác giữa 2 thời kỳ ở nhóm 80-84 năm là 0.0828 log points (9.39 điểm phần trăm) > ngưỡng khóa 0.05. Báo cáo trung thực Q1 = FAIL. |
| 10 | **Ít nhất một trong Q2 hoặc Q3 đạt** | **ĐẠT**<br>*(Cả 2 đều ĐẠT)* | Bảng dữ liệu: `analytics.town_lease_gap`<br>Bảng dữ liệu: `analytics.price_index` | **Q2 ĐẠT:** 13 khu vực đủ điều kiện (ngưỡng >= 10), Spearman thứ hạng 0.6209 (ngưỡng >= 0.60).<br>**Q3 ĐẠT:** Đủ 10 năm liên tục từ 2017 đến 2026 cho 3 loại căn kèm 95% CI cụm block. |
| 11 | **Q4 hoạt động với bộ lọc và không có điểm "đáng mua"** | **ĐẠT** | Trang mã nguồn: [app/pages/4_Cong_cu_tim_khu.py](file:///d:/video/hdb_elt/app/pages/4_Cong_cu_tim_khu.py)<br>Ảnh màn hình: [docs/screenshots/budget_search.png](file:///d:/video/hdb_elt/docs/screenshots/budget_search.png) | Lọc theo Ngân sách, Loại căn, Thời hạn tối thiểu, Cự ly MRT. Có cảnh báo bắt buộc, ẩn khu vực dưới 10 giao dịch, không tạo điểm số hay xếp hạng "đáng mua". |
| 12 | **Dashboard đọc dữ liệu thật và có trang vận hành** | **ĐẠT** | Ứng dụng: [app/Home.py](file:///d:/video/hdb_elt/app/Home.py)<br>Trang vận hành: [app/pages/5_Van_hanh.py](file:///d:/video/hdb_elt/app/pages/5_Van_hanh.py) | Đọc trực tiếp từ kho `warehouse.duckdb` (244,119 dòng fact). Trang vận hành hiển thị lịch sử nạp dữ liệu và chi tiết 12 quy tắc Quality Gate. |
| 13 | **Có ít nhất 7 lần chạy theo lịch, kể cả lần `no_change`** | **CHƯA KIỂM THỬ** | Kế hoạch Giai đoạn 6 | Thuộc phạm vi Giai đoạn 6 (Task Scheduler / Cron). Hệ thống hiện đang dừng trước Giai đoạn 6 theo chỉ thị chờ phê duyệt. |
| 14 | **README cho phép người khác chạy lại** | **ĐẠT** | Hướng dẫn: [README.md](file:///d:/video/hdb_elt/README.md) | Cung cấp đầy đủ hướng dẫn thiết lập môi trường ảo, cài đặt package, thực thi pipeline, chạy dbt test, pytest và chạy Streamlit. |
| 15 | **Báo cáo có giới hạn và nguồn dữ liệu** | **ĐẠT** | Báo cáo hoàn chỉnh: [report/report.md](file:///d:/video/hdb_elt/report/report.md) | Cấu trúc đầy đủ 13 phần theo mục 13 đặc tả, bao gồm đầy đủ 11 giới hạn bắt buộc theo mục 14. |
| 16 | **Không có token hoặc dữ liệu raw lớn trong Git** | **ĐẠT** | Cấu hình: [.gitignore](file:///d:/video/hdb_elt/.gitignore)<br>Kiểm tra `git status` | Git đã bỏ qua: `data/raw/`, `data/warehouse/`, `logs/`, `.env`. Không chứa bất kỳ token, secret, API key hay thông tin cá nhân nào. |

---

## 2. Danh sách Lệnh Thực tế Đã Chạy

```powershell
# Giai đoạn 0: Kiểm tra 4 nguồn dữ liệu
python scripts/check_sources.py

# Giai đoạn 1: Trích xuất dữ liệu gốc và geocoding
python pipeline/extract_hdb.py
python pipeline/extract_mrt.py
python pipeline/extract_blocks.py

# Giai đoạn 2: Nạp dữ liệu vào DuckDB và chạy dbt
python pipeline/load_raw.py
Set-Location "dbt_hdb"
& "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts\dbt.exe" build --profiles-dir .
& "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts\dbt.exe" test --profiles-dir .
Set-Location ".."

# Giai đoạn 3: Chạy Quality Gate và Pytest
python pipeline/quality_gate.py
python pipeline/publish.py
pytest -v

# Giai đoạn 4: Phân tích kinh tế lượng (Q1, Q2, Q3)
$env:PYTHONPATH="."
python analysis/run_analysis.py
python pipeline/publish.py

# Giai đoạn 5: Khởi chạy Streamlit Dashboard và Chụp ảnh màn hình
python -m streamlit run app/Home.py --server.port 8501 --server.headless true
python scripts/capture_screenshots.py

# Toàn trình tích hợp (End-to-End Pipeline)
python pipeline/run_pipeline.py
```

---

## 3. Danh sách Chi tiết Kiểm thử dbt Thực tế và Kết quả

Kết quả thực thi lệnh `dbt test --profiles-dir .` tại thư mục `dbt_hdb`:
- **Tổng số data tests:** 16
- **Kết quả chung:** **PASS = 16, WARN = 0, ERROR = 0, SKIP = 0 (100% PASS)**
- **Thời gian thực thi:** 1.87 giây

| STT | Tên dbt Data Test | Đối tượng kiểm tra | Loại kiểm tra | Thời gian | Trạng thái |
|:---:|---|---|---|:---:|:---:|
| 1 | `not_null_dim_flat_type_flat_type` | `dim_flat_type.flat_type` | Not Null | 0.48s | **PASS** |
| 2 | `not_null_dim_month_month` | `dim_month.month` | Not Null | 0.48s | **PASS** |
| 3 | `not_null_dim_town_town` | `dim_town.town` | Not Null | 0.47s | **PASS** |
| 4 | `not_null_fct_resale_transaction_block` | `fct_resale_transaction.block` | Not Null | 0.47s | **PASS** |
| 5 | `not_null_fct_resale_transaction_flat_type` | `fct_resale_transaction.flat_type` | Not Null | 0.14s | **PASS** |
| 6 | `not_null_fct_resale_transaction_floor_area_sqm` | `fct_resale_transaction.floor_area_sqm` | Not Null | 0.16s | **PASS** |
| 7 | `not_null_fct_resale_transaction_month` | `fct_resale_transaction.month` | Not Null | 0.15s | **PASS** |
| 8 | `not_null_fct_resale_transaction_remaining_lease_years` | `fct_resale_transaction.remaining_lease_years` | Not Null | 0.12s | **PASS** |
| 9 | `not_null_fct_resale_transaction_resale_price` | `fct_resale_transaction.resale_price` | Not Null | 0.13s | **PASS** |
| 10 | `not_null_fct_resale_transaction_street_name` | `fct_resale_transaction.street_name` | Not Null | 0.16s | **PASS** |
| 11 | `not_null_fct_resale_transaction_town` | `fct_resale_transaction.town` | Not Null | 0.13s | **PASS** |
| 12 | `not_null_fct_resale_transaction_transaction_sk` | `fct_resale_transaction.transaction_sk` | Not Null | 0.12s | **PASS** |
| 13 | `unique_dim_flat_type_flat_type` | `dim_flat_type.flat_type` | Unique | 0.16s | **PASS** |
| 14 | `unique_dim_month_month` | `dim_month.month` | Unique | 0.14s | **PASS** |
| 15 | `unique_dim_town_town` | `dim_town.town` | Unique | 0.14s | **PASS** |
| 16 | `unique_fct_resale_transaction_transaction_sk` | `fct_resale_transaction.transaction_sk` | Unique | 0.19s | **PASS** |

---

## 4. Danh sách Chi tiết Kiểm thử Pytest

Kết quả thực thi lệnh `pytest -v` tại thư mục gốc:
- **Tổng số tests:** 10
- **Kết quả chung:** **10/10 PASS (100%)**
- **Thời gian thực thi:** 3.74 giây

| STT | Tên bài kiểm thử Pytest | Tệp kiểm thử | Mục đích kiểm tra | Kết quả |
|:---:|---|---|---|:---:|
| 1 | `test_fact_to_raw_20_rows_reconciliation` | `test_fact_raw_reconciliation.py` | Rút ngẫu nhiên 20 dòng từ bảng fact và đối chiếu khớp từng trường về CSV raw | **PASS** |
| 2 | `test_manifest_write_and_read` | `test_manifest.py` | Kiểm tra cấu trúc ghi và đọc schema manifest JSON | **PASS** |
| 3 | `test_remaining_lease_parsing` | `test_parsers.py` | Kiểm tra độ chính xác khi phân tích chuỗi thời hạn thuê | **PASS** |
| 4 | `test_storey_range_parsing` | `test_parsers.py` | Kiểm tra hàm tính trung vị khoảng tầng | **PASS** |
| 5 | `test_transaction_sk_uniqueness` | `test_parsers.py` | Kiểm tra tính đơn nhất của mã băm `transaction_sk` khi phân biệt dòng trùng | **PASS** |
| 6 | `test_quality_gate_failure_on_missing_column` | `test_quality_gate.py` | Chứng minh Quality Gate chặn xuất bản khi file CSV thiếu cột | **PASS** |
| 7 | `test_quality_gate_failure_on_empty_file` | `test_quality_gate.py` | Chứng minh Quality Gate chặn xuất bản khi file dữ liệu trống 0 byte | **PASS** |
| 8 | `test_quality_gate_failure_on_row_count_drop` | `test_quality_gate.py` | Chứng minh Quality Gate chặn xuất bản khi số dòng giảm quá 1% | **PASS** |
| 9 | `test_quality_gate_failure_preserves_file_hash` | `test_quality_gate.py` | Chứng minh mã hash SHA-256 của `prod.duckdb` không thay đổi trước và sau lần xuất bản bị chặn | **PASS** |
| 10 | `test_publish_behavior_when_read_connection_open_on_windows` | `test_quality_gate.py` | Kiểm tra hành vi khóa file trên Windows: bắt PermissionError khi có kết nối đọc mở, bảo toàn file, và xuất bản thành công sau khi đóng kết nối | **PASS** |

---

## 5. Kết quả Phân tích Kinh tế lượng Thực tế (Q1, Q2, Q3)

Quy tắc phân tích tại `config/analysis_rules.yml` có mã băm SHA-256 xác thực: `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`. Giữ nguyên ngưỡng khóa, không lọc lại mẫu.

### 5.1. Q1. Đường cong thời hạn thuê — Kết luận: FAIL
- **Số lượng mẫu:** P1 tối thiểu 5,879 giao dịch/nhóm; P2 tối thiểu 2,591 giao dịch/nhóm (Đạt yêu cầu >= 1,000).
- **Thứ hạng Spearman giữa hệ số hai giai đoạn:** **1.0000** (Đạt yêu cầu >= 0.90, giá giảm đơn điệu theo thời hạn thuê).
- **Độ ổn định hệ số giữa hai thời kỳ (P1 vs P2):**
  - Nhóm `80-84 năm`: P1 = +0.0845 log points (+8.82%); P2 = +0.1673 log points (+18.21%).
  - Chênh lệch đo được: **0.0828 log points** (tương đương **9.39 điểm phần trăm** theo chênh lệch phần trăm).
  - Ngưỡng quy định: sai khác <= 0.05 (5 điểm phần trăm).
  - **Trạng thái: FAIL.** Báo cáo trung thực sự thiếu ổn định của đường cong sau năm 2022 ở phân khúc căn hộ cận mới. Không đưa ra giả định nguyên nhân khi không có dữ liệu chứng minh.

### 5.2. Q2. Mức chênh lệch theo khu vực — Kết luận: PASS
- **Số khu vực đủ điều kiện (>= 200 giao dịch mỗi nhóm cả 2 thời kỳ):** **13 khu vực** (Đạt yêu cầu >= 10 khu).
- **Spearman thứ hạng mức chênh lệch giữa hai thời kỳ:** **0.6209** (p = 0.0235, Đạt yêu cầu >= 0.60).
- **Số đo chi tiết khớp 100% với bảng `analytics.town_lease_gap`:**
  - *Khu vực Mature (theo chuẩn HDB):*
    - TOA PAYOH: P1 = -0.2377 (-21.16%), P2 = -0.2556 (-22.55%)
    - GEYLANG: P1 = -0.2053 (-18.56%), P2 = -0.2674 (-23.47%)
    - BUKIT MERAH: P1 = -0.1526 (-14.15%), P2 = -0.1990 (-18.04%)
    - BEDOK: P1 = -0.1163 (-10.98%), P2 = -0.1469 (-13.66%)
    - ANG MO KIO: P1 = -0.1161 (-10.97%), P2 = -0.2743 (-23.99%)
    - KALLANG/WHAMPOA: P1 = -0.0851 (-8.16%), P2 = -0.1715 (-15.76%)
    - TAMPINES: P1 = +0.0123 (+1.24%), P2 = -0.0197 (-1.95%)
  - *Khu vực Non-Mature (theo chuẩn HDB):*
    - JURONG EAST: P1 = -0.1899 (-17.30%), P2 = -0.1438 (-13.39%)
    - WOODLANDS: P1 = -0.1352 (-12.64%), P2 = -0.0643 (-6.23%)
    - CHOA CHU KANG: P1 = -0.0895 (-8.56%), P2 = -0.0159 (-1.58%)
    - BUKIT BATOK: P1 = -0.0856 (-8.21%), P2 = -0.1034 (-9.83%)
    - JURONG WEST: P1 = -0.0417 (-4.08%), P2 = -0.0835 (-8.01%)
    - HOUGANG: P1 = -0.0340 (-3.34%), P2 = -0.0289 (-2.85%)
- **Kiểm tra độ nhạy Leave-One-Out Spearman:** Dao động từ 0.5524 đến 0.6993, giá trị trung bình 0.6192. Thứ hạng mức chiết khấu có độ ổn định thống kê tốt.

### 5.3. Q3. Chỉ số giá điều chỉnh — Kết luận: PASS
- **Bao phủ thời gian:** Đủ 10 năm liên tục từ 2017 đến 2026.
- **Kết luận chính (giai đoạn năm đầy đủ 2019 đến 2025):**
  - Giá trung vị thô toàn thị trường tăng từ 400,000 SGD lên 628,000 SGD (**+57.00%**, chỉ số đạt 157.00).
  - Chỉ số Hedonic kiểm soát đặc điểm căn hộ tăng từ 100.0 lên 158.87 (**+58.87%**, 95% CI: [158.34, 159.40]).
  - Độ lệch giữa chỉ số thô và chỉ số Hedonic ở năm 2025 là **-1.87 điểm chỉ số**.
- **Dữ liệu năm 2026:** Ghi nhận là dữ liệu đến thời điểm hiện tại (11 tháng đầu năm 2026, 22,053 giao dịch), chỉ số thô đạt 158.75 (+58.75%), chỉ số Hedonic đạt 159.33 (+59.33%).
- **Giai đoạn 2020–2022:** Đo nhận mức tăng chỉ số giá thô cao hơn chỉ số Hedonic (năm 2020: +3.14 điểm; năm 2021: +5.43 điểm; năm 2022: +2.61 điểm), phản ánh sự dịch chuyển cơ cấu căn hộ giao dịch. Báo cáo số đo thuần túy, không đưa ra giả định nguyên nhân ngoài phạm vi dữ liệu.

---

## 6. Báo cáo Dòng Trùng và Cảnh báo Dữ liệu

1. **Báo cáo dòng trùng lặp:**
   - **Số lượng:** Phát hiện chính xác **318 dòng (0.13%)** trong tổng số 244,119 dòng dữ liệu gốc.
   - **Cách tính:** Sử dụng hàm mã băm 11 thuộc tính gốc `business_hash = sha256(concat_ws('||', trim(c1), ..., trim(c11)))` và đếm số dòng có `COUNT(*) OVER (PARTITION BY business_hash) > 1`.
   - **Xử lý:** Đánh số thứ tự `occurrence_no` bằng hàm cửa sổ và gán khóa duy nhất `transaction_sk = sha256(business_hash || occurrence_no)`. Giữ nguyên toàn bộ 318 dòng trong bảng fact, không xóa dòng, và ghi nhận tỷ lệ này tại trang vận hành. Không đưa ra nhận định chủ quan rằng đây là hiện tượng tự nhiên của thị trường.
2. **Căn hộ nhóm thời hạn 90+ năm:** Báo cáo riêng biệt trong bảng hệ số do chịu tác động đồng thời của các yếu tố công trình mới xây.

---

## 7. Các Tồn tại Kỹ thuật Còn lại (Technical Debt)

1. **Chưa triển khai Giai đoạn 6:** Hệ thống đang dừng trước Giai đoạn 6 theo chỉ thị chờ phê duyệt. Kịch bản `scripts/register_task.ps1` chưa được đăng ký vào Windows Task Scheduler và chưa tích lũy 7 lần chạy theo lịch.
2. **Đường cong Q1 trượt tiêu chí ổn định:** Sai khác tại nhóm 80-84 năm vượt ngưỡng 0.05 (5 điểm phần trăm), vi phạm giả định về tính bất biến thời gian của đường cong chiết khấu thời hạn thuê ở phân khúc cận mới.
3. **Cự ly MRT và CBD:** Hiện tính theo đường thẳng Haversine, chưa tính theo khoảng cách đi bộ thực tế trên mạng lưới đường phố.
4. **Hành vi khóa file trên Windows:** Khi có kết nối đọc đang mở tới `warehouse.duckdb`, lệnh xuất bản sẽ bị chặn bởi hệ điều hành Windows. Cần đảm bảo các kết nối đọc được giải phóng trước khi xuất bản bản cập nhật mới.

---

## 8. Các Việc Cần Chủ Dự án / Giảng viên Hướng dẫn Quyết định (Mục 17)

1. **Hình thức cập nhật dữ liệu:** Xác nhận môn học có chấp nhận dữ liệu cập nhật theo batch định kỳ (hàng ngày hoặc hàng tháng theo snapshot data.gov.sg) hay yêu cầu streaming realtime.
2. **Xử lý kết quả Q1 = FAIL:** Xác nhận chấp nhận giữ nguyên báo cáo trung thực hiện tượng thị trường (như hiện tại) hay muốn thu hẹp phạm vi mẫu thời gian để đánh giá lại.
3. **Phê duyệt chuyển sang Giai đoạn 6:** Xác nhận có cho phép đăng ký kịch bản chạy hằng ngày qua Windows Task Scheduler (`scripts/register_task.ps1`) để tích lũy 7 lần chạy theo dõi hay không.
4. **Yêu cầu hạ tầng nâng cao (Giai đoạn 7):** Xác nhận đồ án có yêu cầu bắt buộc phải bổ sung Apache Airflow, MinIO hoặc Docker Compose để chấm điểm tối đa hay hệ sinh thái DuckDB + dbt hiện tại đã đủ đáp ứng yêu cầu.
