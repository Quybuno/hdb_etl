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
