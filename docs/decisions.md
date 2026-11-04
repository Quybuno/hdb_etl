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
