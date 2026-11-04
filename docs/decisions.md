# Nhật ký Quyết định Kỹ thuật (Decisions Log)

File này ghi nhận các quyết định kiến trúc, lựa chọn kỹ thuật và xử lý tình huống phát sinh trong dự án `hdb_elt`.

---

## Quyết định 001: Quản lý môi trường và Python Dependencies
- **Ngày:** 04/11/2026
- **Bối cảnh:** Cần dbt-duckdb, DuckDB, pandas, numpy, statsmodels, streamlit, plotly, pytest.
- **Quyết định:** Sử dụng môi trường ảo Python 3.12 (`.venv` hoặc Python hiện tại có sẵn packages). Kiểm tra cài đặt `dbt-duckdb` để chạy transformation theo ELT chuẩn.
- **Lý do:** Đảm bảo tính cô lập và đúng đặc tả mục 5.

## Quyết định 002: Xử lý định danh dòng giao dịch (Transaction SK)
- **Ngày:** 04/11/2026
- **Bối cảnh:** Dữ liệu HDB gốc không có khóa chính duy nhất cho từng giao dịch. Có các dòng giống hệt nhau về cả 11 thuộc tính do có 2 giao dịch độc lập cùng khu, loại căn, tầng, diện tích và giá trong cùng tháng.
- **Quyết định:** Áp dụng công thức đặc tả mục 7.2:
  - `business_hash = sha256(11 cột gốc đã trim)`
  - `occurrence_no = row_number() over (partition by business_hash)`
  - `transaction_sk = sha256(business_hash || occurrence_no)`
  - Giữ toàn bộ giao dịch, không xóa dòng trùng, báo cáo tỷ lệ `occurrence_no > 1`.

## Quyết định 003: Chiến lược Lưu trữ Raw và Manifest
- **Ngày:** 04/11/2026
- **Bối cảnh:** Raw phải bất biến theo từng lần chạy, có manifest metadata đầy đủ.
- **Quyết định:** Cấu trúc lưu: `data/raw/hdb_resale/run_date=YYYY-MM-DD/run_id=<uuid>/` chứa `hdb_resale.csv` và `manifest.json`. Nếu chạy lại mà SHA-256 không đổi so với snapshot trước, ghi `status: "no_change"` và không nhân bản CSV thừa.

## Quyết định 004: Tọa độ Block và MRT Exits
- **Ngày:** 04/11/2026
- **Bối cảnh:** Cần tọa độ block để tính khoảng cách tới MRT và CBD.
- **Quyết định:** Tải GeoJSON MRT từ API công khai `d_b39d3a0871985372d7e1637193335da5`, trích xuất tọa độ cửa ga. Tọa độ block kết hợp giữa NUS 3D HDB (nền tảng) và OneMap Search API (cho các block mới), có cache local để tránh gọi lại API nhiều lần.

## Quyết định 005: Xuất bản Nguyên tử Cơ sở dữ liệu (Atomic Warehouse Publishing)
- **Ngày:** 04/11/2026
- **Bối cảnh:** Toàn bộ quá trình ELT, dbt transformation, phân tích kinh tế lượng và quality gate cần thực hiện trên môi trường tách biệt trước khi phục vụ ứng dụng Dashboard, tránh tình trạng Dashboard đọc phải dữ liệu dở dang hoặc cơ sở dữ liệu bị hỏng khi gặp lỗi.
- **Quyết định:**
  - Tách hai file cơ sở dữ liệu: `data/warehouse/warehouse_staging.duckdb` (dành riêng cho pipeline ELT ghi và chạy dbt) và `data/warehouse/warehouse.duckdb` (dành riêng cho Streamlit dashboard đọc).
  - Khi Quality Gate đạt (toàn bộ 12 blocking checks PASS), thực hiện copy sang file tạm thời `warehouse.duckdb.tmp` rồi đổi tên nguyên tử (`atomic rename` / `replace`) đè lên `warehouse.duckdb`.
  - Nếu Quality Gate thất bại, lập tức dừng và không ghi đè `warehouse.duckdb`.

## Quyết định 006: Khóa cứng quy tắc phân tích kinh tế lượng và giữ nguyên kết quả Q1 FAIL
- **Ngày:** 04/11/2026
- **Bối cảnh:** Quy tắc khóa cứng tại `config/analysis_rules.yml` có SHA-256 xác thực. Ở câu hỏi nghiên cứu Q1 (Đường cong thời hạn thuê theo nhóm 5 năm), sai khác giữa hai thời kỳ P1 (2017-2022) và P2 (2023-2026) ở nhóm 80-84 năm đạt 8.28%, vượt ngưỡng khóa 5.0%.
- **Quyết định:** Giữ nguyên 100% ngưỡng khóa, đánh dấu Q1 là FAIL, không nới lỏng ngưỡng thành 10% hay lọc bỏ nhóm để "ép" đạt chỉ tiêu.
- **Lý do:** Tuân thủ quy tắc bắt buộc số 2 ("Chỉ dùng dữ liệu thật"), số 8 ("Không tự sửa ngưỡng đã khóa") và số 11 ("Không kết luận nhân quả"). Phản ánh trung thực biến động đo lường được của thị trường HDB sau năm 2022 ở nhóm 80-84 năm.

## Quyết định 007: Kiến trúc Dashboard Streamlit và Tuân thủ Pháp lý/Khuyến nghị
- **Ngày:** 04/11/2026
- **Bối cảnh:** Cần xây dựng dashboard trực quan cho người dùng cuối nhưng phải tuân thủ nghiêm ngặt các quy định về cảnh báo rủi ro đầu tư và vận hành.
- **Quyết định:**
  - Dashboard kết nối trực tiếp đến `data/warehouse/warehouse.duckdb` ở chế độ read-only (`duckdb.connect(..., read_only=True)`).
  - Tất cả số liệu hiển thị được tính toán trực tiếp từ các bảng fact/marts/analytics trong database, không hardcode số liệu tĩnh vào code.
  - Tại trang tra cứu khu vực (`4_Cong_cu_tim_khu.py`), bắt buộc hiển thị thông điệp cảnh báo nổi bật: *"Công cụ chỉ hỗ trợ thu hẹp phạm vi tìm kiếm theo tiêu chí ngân sách và nhu cầu thời hạn; không cấu thành khuyến nghị đầu tư hoặc xếp hạng khu đáng mua."* Không tạo tính năng xếp hạng "khu đáng mua nhất" hay "điểm đầu tư".
  - Dashboard không tự nhận là "realtime", ghi rõ chu kỳ cập nhật dữ liệu theo snapshot HDB hàng tháng.

## Quyết định 008: Cơ chế Thử lại khi Xuất bản trên Windows (File Lock Resilience)
- **Ngày:** 04/11/2026
- **Bối cảnh:** Trên Windows, khi bảng điều khiển Streamlit đang mở kết nối đọc (`read_only=True`), lệnh `os.replace` của Python trả về ngoại lệ `PermissionError: [WinError 5] Access is denied` do cơ chế khóa tệp độc quyền của hệ điều hành.
- **Quyết định:**
  - Bổ sung vòng lặp thử lại tối đa 5 lần với khoảng trễ 1.0 giây trong `pipeline/publish.py`.
  - Nếu sau 5 lần tệp đích vẫn bị khóa, hàm xuất bản bảo toàn nguyên vẹn tệp kho dữ liệu hiện hành, dọn dẹp tệp hoán đổi tạm `.tmp`, ghi log FAILED và kết thúc an toàn mà không đóng/giết tiến trình của dashboard.
  - Viết test kiểm thử hồi quy `test_publish_behavior_when_read_connection_open_on_windows` xác nhận hành vi bảo toàn kho cũ khi bị khóa.

## Quyết định 009: Mở rộng bộ dbt Data Tests Toàn diện
- **Ngày:** 04/11/2026
- **Bối cảnh:** Cần kiểm soát chặt chẽ toàn vẹn tham chiếu giữa bảng fact và các bảng chiều, đồng thời kiểm tra miền giá trị vật lý của dữ liệu giao dịch.
- **Quyết định:**
  - Bổ sung 3 tests toàn vẹn quan hệ khóa ngoại (`relationships`): `fct_resale_transaction` tham chiếu tới `dim_month.month`, `dim_town.town`, và `dim_flat_type.flat_type`.
  - Bổ sung 2 tests kiểm tra danh mục giá trị hợp lệ (`accepted_values`) cho `flat_type` trên cả bảng dim và fact theo đúng 7 loại căn hộ thực tế xuất hiện trong dữ liệu HDB: `1 ROOM`, `2 ROOM`, `3 ROOM`, `4 ROOM`, `5 ROOM`, `EXECUTIVE`, `MULTI-GENERATION`.
  - Bổ sung 3 singular domain tests kiểm tra miền giá trị hợp lệ:
    - `assert_fct_resale_price_positive`: giá bán lại > 0.
    - `assert_fct_floor_area_positive`: diện tích căn hộ > 0 m².
    - `assert_fct_remaining_lease_range`: thời hạn thuê còn lại trong khoảng hợp lệ $(0, 99]$ năm.
  - Tổng số dbt tests nâng từ 16 lên 24 tests, toàn bộ đạt PASS 24/24.

## Quyết định 010: Triển khai Lịch chạy Tự động và Theo dõi Lần chạy lỡ qua Windows Task Scheduler
- **Ngày:** 04/11/2026
- **Bối cảnh:** Yêu cầu vận hành Giai đoạn 6 cần lịch chạy hằng ngày lúc 08:15 AM với nhật ký độc lập cho từng phiên chạy, phát hiện lần chạy lỡ, không xóa log cũ, và không thêm Airflow/Docker/MinIO.
- **Quyết định:**
  - Sử dụng công cụ chuẩn `schtasks.exe` của Windows để đăng ký tác vụ `HDB_ELT_Daily_Run` kích hoạt `scripts/run_pipeline.ps1` hằng ngày vào lúc 08:15 AM.
  - Kịch bản `run_pipeline.ps1` tạo tệp nhật ký riêng theo dấu thời gian: `logs/scheduler/run_YYYYMMDD_HHMMSS.log` (không bao giờ xóa log cũ).
  - Tự động theo dõi lần chạy lỡ: tính khoảng cách thời gian từ phiên chạy thành công trước đó; nếu vượt quá 26.0 giờ, hệ thống ghi nhận cảnh báo và số lần chạy dự kiến bị lỡ vào `logs/scheduler/schedule_history.json`.
  - Biên soạn `docs/runbook.md` hướng dẫn chi tiết lệnh kiểm tra trạng thái, kích hoạt thủ công và quy trình ứng phó 5 kịch bản sự cố thực tế.
