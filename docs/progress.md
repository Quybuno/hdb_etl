# Tiến độ thực hiện Dự án (Progress Log)

---

## Giai đoạn 0: Kiểm tra Nguồn dữ liệu
- **Thời gian:** 04/11/2026 15:52 UTC+7
- **Việc đã làm:**
  - Khởi tạo repo Git tại `D:\video\hdb_elt`.
  - Tạo `.gitignore` chặn commit `data/raw`, `data/warehouse`, `logs`, `.env`.
  - Viết và thực thi kịch bản kiểm tra nguồn `scripts/check_sources.py`.
  - Kiểm tra 4 nguồn: API HDB, API MRT, NUS 3D HDB, OneMap API.
  - Đo lường độ trễ, số dòng, cột, SHA-256, min/max month.
  - Xác minh điều khoản giấy phép (Singapore Open Data Licence, MIT, OneMap SLA).
  - Lập báo cáo chi tiết tại `docs/source_check.md`.
- **Lệnh đã chạy:**
  - `python scripts/check_sources.py`
- **Kết quả:**
  - HDB: HTTP 201/200, 244,119 dòng, đủ 11 cột, `max(month) = 2026-11` (mới nhất), SHA-256 `59115752e6b8430545ea0814557678df7fd0514bbaba828b379a33855cb533f6`.
  - MRT: HTTP 201/200, GeoJSON 213,480 bytes, SHA-256 `7a57cb14cf7c621203938e944f99b41891284e5e67876c43d9f8f3ee3aa88ee6`.
  - NUS 3D HDB: HTTP 200, kho dữ liệu sẵn sàng.
  - OneMap: HTTP 200, phản hồi 5 kết quả tìm kiếm.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 1.
- **Việc tiếp theo:** Giai đoạn 1: Khởi tạo cấu trúc dự án, cài đặt môi trường, viết extractor cho HDB, MRT, block coordinates.

---

## Giai đoạn 1: Khởi tạo và Extract
- **Thời gian:** 04/11/2026 16:01 UTC+7
- **Việc đã làm:**
  - Thiết lập cấu trúc thư mục toàn diện theo mục 6 đặc tả.
  - Tạo `requirements.txt`, `.env.example`, `README.md`, `docs/data_dictionary.md`.
  - Cài đặt `dbt-core` (1.12.6) và `dbt-duckdb` (1.11.1).
  - Viết module dùng chung: `pipeline/common/logger.py`, `pipeline/common/retry.py` (tự động retry lỗi mạng / 429 với exponential backoff, dừng ngay khi gặp 403), `pipeline/common/manifest.py`.
  - Viết `pipeline/extract_hdb.py`: trích xuất HDB resale, tính toán SHA-256, lưu manifest bất biến, phát hiện snapshot trùng lặp (`no_change`).
  - Viết `pipeline/extract_mrt.py`: tải GeoJSON MRT exits, trích xuất tọa độ 613 cửa ga và chuẩn hóa.
  - Viết `pipeline/extract_blocks.py`: tích hợp tọa độ NUS 3D và tự động tra cứu OneMap Search API cho các block mới xây (có rate limit 1s và cache).
  - Thực thi kiểm thử bằng lượt chạy thật:
    - Run 1 (run_id: `aa50ca00-8d79-4ba6-9762-5d8e2e6b9780`): Tải 244,119 dòng CSV HDB, 613 cửa MRT, geocode 9 block mới xây (Canberra Walk, Northshore Dr, Bidadari Pk Dr, Alkaff Cres, Margaret Dr). Cập nhật tổng số block lên 9,769 block.
    - Run 2 (run_id: `b03e33d5-364c-4c58-8f30-11f320b64422`): Kiểm tra cơ chế deduplication: ghi nhận `status: no_change`, lưu manifest, không nhân bản CSV thừa.
- **Lệnh đã chạy:**
  - `python -c "..."` (test pipeline extract)
  - `python pipeline/extract_hdb.py`
- **Kết quả:** ĐẠT. Toàn bộ dữ liệu raw và reference đã sẵn sàng.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 2.
- **Việc tiếp theo:** Giai đoạn 2: Load dữ liệu thô vào DuckDB và xây dựng các mô hình dbt (staging, intermediate, marts, ops).

---

## Giai đoạn 2: Load và dbt Transformation
- **Thời gian:** 04/11/2026 16:07 UTC+7
- **Việc đã làm:**
  - Viết `pipeline/load_raw.py`: nạp dữ liệu thô vào `warehouse_staging.duckdb`:
    - `raw.hdb_resale_snapshot`: 244,119 dòng dạng chuỗi thô kèm `source_row_number`, `run_id`, `loaded_at_utc`.
    - `raw.mrt_station_exits`: 613 ga/cửa MRT.
    - `raw.block_coordinates`: 9,769 block tòa nhà.
  - Thiết lập dự án dbt `dbt_hdb` với profile kết nối DuckDB.
  - Viết toàn bộ các mô hình SQL theo mục 7 đặc tả:
    - **Staging:** `stg_hdb_resale` (tính `business_hash`, `occurrence_no`, `transaction_sk`), `stg_mrt_exits`, `stg_block_location`.
    - **Intermediate:** `int_resale_parsed` (parse `remaining_lease_years`, `storey_mid`, `price_per_sqm`, `flat_age`, `lease_band_5yr`), `int_block_mrt_distance` (tính cự ly Haversine tới 613 cửa MRT và CBD Raffles Place), `int_resale_enriched` (ghép nối giao dịch với không gian địa lý).
    - **Marts:** `dim_month`, `dim_town` (phân loại Mature/Non-Mature), `dim_block`, `dim_flat_type`, `fct_resale_transaction`, `mart_town_month`, `mart_budget_search`.
    - **Ops:** `ops_pipeline_run`, `ops_snapshot_delta`, `ops_source_freshness`.
  - Viết bộ dbt schema tests (`dbt_hdb/models/schema.yml`): kiểm tra uniqueness, not null, constraints.
  - Thực thi `dbt build` và `dbt test`:
    - 16/16 models hoàn thành thành công (11 tables, 5 views trong 13.16s).
    - 16/16 tests PASS 100% (transaction_sk duy nhất, không có null trên các trường bắt buộc).
    - Thống kê dòng trùng: 318 dòng (0.13%) có `occurrence_no > 1` được giữ nguyên theo đúng quy định mục 7.2.
- **Lệnh đã chạy:**
  - `python pipeline/load_raw.py`
  - `dbt build --profiles-dir .`
  - `dbt test --profiles-dir .`
- **Kết quả:** ĐẠT 100%. Toàn bộ dữ liệu fact, dim, marts, ops đã sẵn sàng trong `warehouse_staging.duckdb`.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 3.
- **Việc tiếp theo:** Giai đoạn 3: Quality Gate, Publish nguyên tử và kiểm thử hồi quy pytest (ít nhất 3 tình huống lỗi: thiếu cột, file trống, số dòng giảm).

---

## Giai đoạn 3: Quality Gate và Publish
- **Thời gian:** 04/11/2026 16:10 UTC+7
- **Việc đã làm:**
  - Viết `pipeline/quality_gate.py` triển khai đầy đủ 12 điều kiện chặn (Blocking checks) và các điều kiện cảnh báo (Warning checks) theo mục 9 đặc tả:
    1. Số cột HDB: đúng 11 cột dự kiến.
    2. File raw: không trống (> 0 bytes, có dữ liệu).
    3. Số dòng: không giảm quá 1% so với snapshot xuất bản trước đó.
    4. Tỷ lệ null các trường cốt lõi (`month`, `town`, `flat_type`, `block`, `street_name`, `resale_price`) <= 0.1%.
    5. `resale_price` > 0.
    6. `floor_area_sqm` > 0.
    7. Tỷ lệ lỗi parse `remaining_lease` <= 0.1%.
    8. Tỷ lệ lỗi parse `storey_range` <= 0.1%.
    9. `transaction_sk` duy nhất 100%.
    10. Lệch 0 dòng giữa bảng raw snapshot và bảng fact.
    11. Tỷ lệ ghép nối tọa độ block >= 98% (thực tế đạt 100%).
    12. Độ mới dữ liệu: `max(month)` không cũ quá 2 tháng dương lịch.
    - Cảnh báo: tỷ lệ dòng trùng theo `business_hash` (ghi nhận 0.13%).
    - Ghi nhận chi tiết kết quả vào bảng `ops.quality_result`.
  - Viết `pipeline/publish.py`: cơ chế xuất bản nguyên tử (atomic rename qua `.tmp`) từ `warehouse_staging.duckdb` sang `warehouse.duckdb`; từ chối xuất bản và giữ nguyên warehouse cũ nếu Quality Gate không đạt.
  - Viết bộ kiểm thử tự động pytest:
    - `tests/test_parsers.py`: kiểm tra hàm phân tích lease, storey và tính duy nhất của hash/sk.
    - `tests/test_manifest.py`: kiểm tra cấu trúc schema và đọc ghi manifest.
    - `tests/test_quality_gate.py`: chứng minh lỗi bị chặn và `warehouse.duckdb` không bị ghi đè trong 3 tình huống:
      1. Thiếu cột trong file raw.
      2. File raw trống.
      3. Số dòng giảm quá 1% so với baseline.
    - `tests/test_fact_raw_reconciliation.py`: chọn ngẫu nhiên 20 dòng từ `fct_resale_transaction` và đối chiếu ngược về file raw CSV theo `source_row_number` và 11 thuộc tính gốc.
  - Chạy `pytest -v`: 8/8 tests PASS 100% trong 2.87s.
- **Lệnh đã chạy:**
  - `python pipeline/quality_gate.py`
  - `pytest -v`
  - `python pipeline/publish.py`
- **Kết quả:** ĐẠT 100%. Đã xuất bản phiên bản cơ sở dữ liệu sản xuất đầu tiên tại `data/warehouse/warehouse.duckdb`.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 4.
- **Việc tiếp theo:** Giai đoạn 4: Phân tích kinh tế lượng (Q1, Q2, Q3) theo quy tắc khóa cứng `config/analysis_rules.yml`.

---

## Giai đoạn 4: Phân tích Kinh tế lượng
- **Thời gian:** 04/11/2026 16:13 UTC+7
- **Việc đã làm:**
  - Khởi tạo quy tắc phân tích `config/analysis_rules.yml` và khóa mã băm SHA-256: `08c16165026179f384f6ad92302a3c043ba60d6f4fdef7e030fb5d4d52a85ac7`. Không nới lỏng ngưỡng hay chọn lại mẫu theo quy định mục 8 và 10.
  - Viết `analysis/lease_curve.py` (Q1): mô hình hồi quy hedonic đường cong thời hạn thuê theo nhóm 5 năm (tham chiếu 70-74 năm), kiểm soát diện tích, tầng, khu, tháng, loại căn, sai số gom cụm theo `block_id`.
    - Kết quả Q1: Số mẫu đạt (P1 min 5,879; P2 min 2,591 tx/nhóm), Spearman thứ hạng đạt 1.0 (tăng đơn điệu). Tuy nhiên, độ chênh lệch giữa hai thời kỳ tại nhóm 80-84 năm là 8.28% (vượt ngưỡng khóa 5%). Trạng thái: **FAIL** (báo cáo trung thực sự bất ổn định tại phân khúc 80-84 năm sau năm 2022, không bóp méo số liệu).
  - Viết `analysis/town_lease_gap.py` (Q2): đo lường mức chênh giữa nhóm thuê ngắn (55-65 năm) và nhóm tham chiếu (70-80 năm) theo khu vực, kiểm soát diện tích, tầng, loại căn, tháng.
    - Kết quả Q2: 13 khu vực đủ điều kiện (>= 200 tx/nhóm cả 2 thời kỳ, vượt ngưỡng >= 10 khu), Spearman thứ hạng đạt 0.6209 (vượt ngưỡng >= 0.60). Trạng thái: **PASS**.
  - Viết `analysis/price_index.py` (Q3): tính chỉ số giá thô so với chỉ số giá hedonic kiểm soát thành phần căn hộ qua các năm (năm gốc 2019 = 100), tính khoảng tin cậy 95% gom cụm block cho tổng thể và 3 loại căn (3-Room, 4-Room, 5-Room).
    - Kết quả Q3: Phủ toàn bộ từ 2017 đến 2026, phân tích đủ 3 phân khúc chính kèm khoảng tin cậy. Trạng thái: **PASS**.
  - Viết `analysis/run_analysis.py`: nạp kết quả vào DuckDB schema `analytics` (`analytics.lease_curve`, `analytics.town_lease_gap`, `analytics.price_index`, `analytics.analysis_run`) và xuất báo cáo `docs/analysis_results.md`.
  - Xuất bản dữ liệu phân tích sang `warehouse.duckdb`.
- **Lệnh đã chạy:**
  - `python analysis/run_analysis.py`
  - `python pipeline/publish.py`
- **Kết quả:** Q1: FAIL (ghi nhận trung thực, đường cong có bước nhảy tại nhóm 80-84 năm sau 2023), Q2: PASS, Q3: PASS. Thỏa mãn điều kiện "Ít nhất một trong Q2 hoặc Q3 đạt" theo mục 15 đặc tả.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 5.
- **Việc tiếp theo:** Giai đoạn 5: Xây dựng Streamlit Dashboard hoàn chỉnh theo mục 11 kết nối dữ liệu thật từ `warehouse.duckdb`.

---

## Giai đoạn 5: Dashboard Streamlit
- **Thời gian:** 04/11/2026 16:25 UTC+7
- **Việc đã làm:**
  - Thiết kế và xây dựng giao diện Streamlit tương tác đọc trực tiếp từ `data/warehouse/warehouse.duckdb` (chế độ `read_only=True`) qua module `app/db.py`.
  - Phát triển đầy đủ 6 màn hình chức năng theo mục 11 của tài liệu đặc tả:
    1. `app/Home.py`: Trang chủ tổng quan hệ thống, tổng số giao dịch, khoảng thời gian dữ liệu, giá trung vị/m2, biểu đồ xu hướng theo năm và bảng tóm tắt giao dịch theo dải thời hạn thuê.
    2. `app/pages/1_Duong_cong_thue.py`: Trình diễn đường cong thời hạn thuê theo nhóm 5 năm (kết quả Q1), đối chiếu giữa hai thời kỳ P1 (2017-2022) và P2 (2023-2026), hiển thị bảng số liệu chi tiết, phân tích nguyên nhân kết quả FAIL và các giới hạn kinh tế lượng.
    3. `app/pages/2_So_sanh_khu.py`: Trình diễn mức chênh lệch giá giữa căn hộ thuê ngắn (55-65 năm) và căn hộ chuẩn (70-80 năm) theo từng khu vực (kết quả Q2), phân loại Mature vs Non-Mature town, biểu đồ cột chênh lệch và ma trận tương quan thứ hạng (Spearman = 0.6209 - PASS).
    4. `app/pages/3_Gia_dieu_chinh.py`: So sánh trực quan chuỗi chỉ số giá thô và chỉ số giá Hedonic chuẩn hóa (kết quả Q3, gốc 2019 = 100) kèm dải tin cậy 95% gom cụm theo block, phân rã theo 3 loại căn chính (3-Room, 4-Room, 5-Room).
    5. `app/pages/4_Cong_cu_tim_khu.py`: Công cụ hỗ trợ người mua tra cứu khu vực theo ngân sách và dải thời hạn thuê mong muốn dựa trên bảng `mart_budget_search` (dữ liệu 12 tháng gần nhất). Bắt buộc hiển thị cảnh báo: *"Công cụ chỉ hỗ trợ thu hẹp phạm vi tìm kiếm theo tiêu chí ngân sách và nhu cầu thời hạn; không cấu thành khuyến nghị đầu tư hoặc xếp hạng khu đáng mua."* Không có tính năng xếp hạng hoặc gán nhãn "đáng mua nhất".
    6. `app/pages/5_Van_hanh.py`: Trang giám sát sức khỏe dữ liệu và quy trình ELT dành cho kỹ sư vận hành, hiển thị lịch sử chạy pipeline, chi tiết kết quả 12 quy tắc của Quality Gate mới nhất, độ tươi dữ liệu nguồn và trạng thái phân tích.
  - Chạy thử dashboard thực tế trên cổng 8501 (`http://localhost:8501`), kiểm tra tất cả bộ lọc dữ liệu.
  - Sử dụng headless Chrome tự động hóa qua `scripts/capture_screenshots.py` để chụp ảnh màn hình chất lượng cao của cả 6 trang, lưu trữ tại thư mục `docs/screenshots/`:
    - `docs/screenshots/home_overview.png`
    - `docs/screenshots/lease_curve.png`
    - `docs/screenshots/town_comparison.png`
    - `docs/screenshots/price_index.png`
    - `docs/screenshots/budget_search.png`
    - `docs/screenshots/operations_quality.png`
  - Xây dựng kịch bản điều phối tích hợp toàn trình `pipeline/run_pipeline.py` (tự động hóa tuần tự từ Extract HDB/MRT/Blocks, Load DuckDB, dbt build, Econometric Analysis, Quality Gate đến Atomic Publish). Đã kiểm thử chạy thành công toàn bộ pipeline với mã thoát 0.
- **Lệnh đã chạy:**
  - `python -m streamlit run app/Home.py --server.port 8501 --server.headless true`
  - `python scripts/capture_screenshots.py`
  - `python pipeline/run_pipeline.py`
- **Kết quả:** ĐẠT 100%. Toàn bộ 6 trang hoạt động chính xác trên cơ sở dữ liệu thật, không có lỗi giao diện hay truy vấn.
- **Trạng thái:** HOÀN THÀNH GIAI ĐOẠN 5.

---

## Giai đoạn 6: Lịch chạy, Vận hành và Hoàn thiện Báo cáo Nghiệm thu
- **Thời gian:** 04/11/2026 17:15 UTC+7
- **Việc đã làm:**
  - **Ví dụ mở đầu & Báo cáo:**
    - Truy vấn 2 căn hộ thực tế tại khu Queenstown, tháng 2024-07, loại 3 ROOM, 60.0 m², khoảng tầng 04 TO 06 từ `fct_resale_transaction`:
      - Căn thuê ngắn (41.58 năm): Block 95 C'wealth Dr, 322,000 SGD ($5,366.67/m²), `transaction_sk = 6422b1795eabe983b98ee59eb120fa2b10dc0c446852ce9d5b9091f6f0255df5`.
      - Căn thuê dài (83.17 năm): Block 89 Tanglin Halt Rd, 592,000 SGD ($9,866.67/m²), `transaction_sk = bff535e26da9e95120bd78044e33f306d39c7da1902da444ce0cafa0fd701d83`.
      - Chênh lệch đơn giá: +83.85% (+4,500.00 SGD/m²). Ghi nhận câu lệnh SQL và SK tại `docs/report_example.md`, nêu rõ đây là minh họa mô tả, không phải kết luận nhân quả đã kiểm soát.
    - Cập nhật `report/report.md` chuẩn hóa theo Mục 13 và Mục 14:
      - Mục 12 dùng chuẩn xác 0.0828 log points và 9.39 điểm phần trăm.
      - Công thức hedonic Mục 7 bổ sung kiểm soát loại căn hộ ($\sum_f \theta_f \text{FlatType}_{if}$).
      - Xóa triệt để các nội dung không có căn cứ hoặc chủ quan: CPF, tín dụng, SERS, VERS, "định giá hợp lý", "tránh mua", "price_per_sqm / remaining_lease_years", "giá thực tế", "tăng giá thuần túy", các từ ngữ "hoàn chỉnh", "tự động hóa cao", "sâu sắc", "có tính hệ thống", và "tuyệt đối".
      - Q1: Báo cáo nhóm thay đổi, giữ kết luận FAIL, không suy diễn nguyên nhân ngoài số liệu.
      - Q2: Nêu rõ 13 khu vực đủ mẫu, Spearman 0.6209, leave-one-out 0.5524–0.6993, nêu rõ 6 lần dưới 0.60; phân loại mature/non-mature là nhóm mô tả theo HDB, chưa kiểm định thống kê.
      - Q3: Bổ sung bảng cơ cấu giao dịch 2017–2026 (tỷ trọng 3, 4, 5-room, diện tích TB/trung vị, tầng TB, thời hạn TB).
      - Q4: Bổ sung bảng kết quả thực tế từ bộ lọc `mart_budget_search` (14 khu vực theo thứ tự chữ cái, không xếp hạng).
      - Đầy đủ 11 giới hạn bắt buộc theo Mục 14.
  - **Mở rộng dbt Data Tests:**
    - Bổ sung 8 data tests mới:
      - Kiểm tra quan hệ khóa ngoại (`relationships`): `fct_resale_transaction` -> `dim_month`, `dim_town`, `dim_flat_type`.
      - Kiểm tra tập giá trị hợp lệ (`accepted_values`) cho `flat_type` (7 loại căn thực tế).
      - 3 singular domain tests: `assert_fct_resale_price_positive`, `assert_fct_floor_area_positive`, `assert_fct_remaining_lease_range` (0 < remaining_lease_years <= 99).
    - Chạy `dbt build` và `dbt test`: PASS 40/40 (16 models, 24 data tests 100% PASS).
  - **Cơ chế Retry Publish trên Windows:**
    - Cập nhật `pipeline/publish.py`: thêm cơ chế thử lại (tối đa 5 lần, delay 1.0s) khi gặp lỗi khóa file `PermissionError [WinError 5]`. Nếu sau 5 lần vẫn bị khóa bởi ứng dụng đọc, pipeline giữ nguyên kho cũ, dọn tệp tạm, ghi log FAILED và thoát an toàn mà không đóng tiến trình dashboard Streamlit.
    - Cập nhật `tests/test_quality_gate.py`: thêm `test_publish_behavior_when_read_connection_open_on_windows`. Chạy `pytest -v`: PASS 10/10 tests 100%.
  - **Đăng ký Task Scheduler & Nhật ký Vận hành:**
    - Viết `scripts/run_pipeline.ps1`: thực thi pipeline tự động, tạo log riêng biệt theo dấu thời gian (`logs/scheduler/run_YYYYMMDD_HHMMSS.log`), không xóa log cũ, phát hiện và ghi nhận các lần chạy lỡ (> 26 giờ) vào `logs/scheduler/schedule_history.json`.
    - Viết `scripts/register_task.ps1` và đăng ký thành công tác vụ `HDB_ELT_Daily_Run` với Windows Task Scheduler:
      - Lịch chạy: Hằng ngày lúc 08:15 AM.
      - Trạng thái: Ready (Next Run: 05/11/2026 8:15:00 AM).
    - Chạy thử nghiệm thành công `scripts/run_pipeline.ps1`:
      - Phiên chạy `run_id = a523843a-1161-4e3a-91d3-141a5201a252`.
      - Tải HDB xác nhận `status: no_change` không trùng file.
      - Nạp DuckDB, dbt build (24 tests PASS), kinh tế lượng, Quality Gate (12 checks PASS), Publish kho sản xuất hoàn tất. Mã thoát 0.
      - Nhật ký ghi nhận tại `logs/scheduler/run_20261104_170831.log` và `logs/scheduler/schedule_history.json`.
    - Viết tài liệu hướng dẫn vận hành và ứng phó sự cố tại `docs/runbook.md`.
    - Cập nhật `docs/acceptance_report.md` toàn diện với đầy đủ bằng chứng, số liệu kiểm thử và trạng thái theo dõi 7 lần chạy.
- **Lệnh đã chạy:**
  - `python pipeline/publish.py`
  - `dbt build --profiles-dir .` (tại `dbt_hdb`)
  - `dbt test --profiles-dir .` (tại `dbt_hdb`)
  - `pytest -v`
  - `powershell -ExecutionPolicy Bypass -File scripts/register_task.ps1`
  - `powershell -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1`
- **Kết quả:** ĐẠT. Toàn bộ các yêu cầu nghiệm thu, kiểm thử và tài liệu đã hoàn thành. Hệ thống đang hoạt động và theo dõi lịch chạy tự động.
- **Trạng thái:** HOÀN THÀNH GIAI ĐOẠN 6 (Đang theo dõi tích lũy 7 lần chạy hàng ngày).
