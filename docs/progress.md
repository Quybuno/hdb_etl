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
    - 16/16 tests PASS 100% (transaction_sk duy nhất tuyệt đối, không có null trên các trường bắt buộc).
    - Thống kê dòng trùng: 318 dòng (0.13%) có `occurrence_no > 1` được giữ nguyên theo đúng quy định mục 7.2.
- **Lệnh đã chạy:**
  - `python pipeline/load_raw.py`
  - `dbt build --profiles-dir .`
  - `dbt test --profiles-dir .`
- **Kết quả:** ĐẠT 100%. Toàn bộ dữ liệu fact, dim, marts, ops đã sẵn sàng trong `warehouse_staging.duckdb`.
- **Trạng thái:** ĐẠT. Đủ điều kiện chuyển sang Giai đoạn 3.
- **Việc tiếp theo:** Giai đoạn 3: Quality Gate, Publish nguyên tử và kiểm thử hồi quy pytest (ít nhất 3 tình huống lỗi: thiếu cột, file trống, số dòng giảm).
