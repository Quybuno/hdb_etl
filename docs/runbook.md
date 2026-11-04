# Hướng dẫn Vận hành Hệ thống ELT HDB Singapore (Runbook)

> **Dự án:** Hệ thống ELT và Dashboard phân tích giá HDB Singapore theo thời hạn thuê  
> **Tác vụ tự động:** `HDB_ELT_Daily_Run` (Windows Task Scheduler)  
> **Lịch chạy:** Hằng ngày vào lúc **08:15 AM (UTC+7)**  
> **Tệp kịch bản:** `scripts/run_pipeline.ps1`  
> **Kho dữ liệu đích:** `data/warehouse/warehouse.duckdb`  

---

## 1. Kiến trúc và Cơ chế Vận hành

Hệ thống được thiết kế theo nguyên tắc Batch ELT tự động, bất biến và tự khôi phục:
1. **Lịch trình tự động:** Đăng ký trực tiếp với hệ điều hành Windows qua công cụ `schtasks.exe`, không phụ thuộc vào các dịch vụ orchestration nặng như Airflow, Docker hay MinIO.
2. **Nhật ký độc lập (Log per Run):** Mỗi lần thực thi tạo ra một tệp log riêng biệt theo dấu thời gian: `logs/scheduler/run_YYYYMMDD_HHMMSS.log`. Các tệp log cũ được bảo toàn tuyệt đối, không bao giờ bị ghi đè hay xóa.
3. **Theo dõi lần chạy lỡ (Missed Runs Tracking):** Kịch bản tự động kiểm tra thời gian kể từ lần chạy thành công gần nhất. Nếu khoảng cách vượt quá 26 giờ (do máy tính tắt hoặc lỗi lịch), hệ thống ghi nhận cảnh báo vào `logs/scheduler/schedule_history.json`.
4. **Bảo vệ khóa tệp trên Windows (File Lock Resilience):** Khi bảng điều khiển Streamlit đang kết nối đọc tới `warehouse.duckdb`, quy trình xuất bản áp dụng cơ chế thử lại (tối đa 5 lần, mỗi lần cách nhau 1.0 giây). Nếu sau 5 lần tệp vẫn bị khóa, hệ thống giữ nguyên tệp kho dữ liệu hiện tại, dọn dẹp tệp hoán đổi tạm, ghi trạng thái FAILED và kết thúc an toàn mà không đóng tiến trình dashboard.

---

## 2. Các Lệnh Vận hành Cơ bản

### 2.1. Kiểm tra trạng thái Task Scheduler
```powershell
schtasks.exe /query /tn "HDB_ELT_Daily_Run" /fo LIST /v
```
Các thông số cần quan sát:
- `Status`: Phải là **Ready** (hoặc **Running** khi đang chạy).
- `Next Run Time`: Thời điểm chạy kế tiếp (08:15 AM ngày mai).
- `Last Run Time` và `Last Result`: Thời điểm và mã kết quả lần chạy trước (mã `0` là thành công).

### 2.2. Kích hoạt chạy thử thủ công qua Task Scheduler
```powershell
schtasks.exe /run /tn "HDB_ELT_Daily_Run"
```

### 2.3. Chạy thủ công trực tiếp bằng PowerShell
```powershell
Set-Location "D:\video\hdb_elt"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\run_pipeline.ps1"
```

### 2.4. Xem lịch sử các phiên chạy theo lịch
```powershell
Get-Content "logs\scheduler\schedule_history.json" | ConvertFrom-Json | Format-Table run_id, start_time, duration_seconds, exit_code, status
```

---

## 3. Quy trình Ứng phó Sự cố (Incident Response)

| Sự cố | Biểu hiện | Nguyên nhân khả dĩ | Biện pháp xử lý |
|---|---|---|---|
| **Lỗi tải dữ liệu HDB** | Log ghi `Timeout` hoặc `Download failed` | Mạng gián đoạn hoặc API data.gov.sg bảo trì | Pipeline tự động thử lại 4 lần với lũy thừa thời gian chờ. Nếu vẫn lỗi, giữ nguyên dữ liệu cũ, không làm gián đoạn dashboard. |
| **Gặp mã lỗi HTTP 403** | Log ghi `HTTPForbiddenError` | Nguồn dữ liệu chặn truy cập | Dừng toàn bộ pipeline ngay lập tức theo đặc tả. Báo cáo quản trị viên kiểm tra quyền truy cập API. Không dùng proxy/VPN để vượt chặn. |
| **Quality Gate bị chặn** | Log ghi `Quality Gate passed: False` | File dữ liệu bị thiếu cột, rỗng hoặc số dòng sụt giảm > 1% | Pipeline tự động dừng trước bước xuất bản. Kho `warehouse.duckdb` giữ nguyên mã băm SHA-256 phiên bản tốt trước đó. Kiểm tra chi tiết tại `data/warehouse/warehouse_staging.duckdb` và log. |
| **Khóa file do Dashboard** | Log ghi `PermissionError: [WinError 5]` | Streamlit dashboard đang mở kết nối đọc lâu | Pipeline tự động thử lại 5 lần (1.0s). Nếu vẫn không được, pipeline kết thúc an toàn và giữ nguyên kho cũ. Khuyến nghị cấu hình lịch chạy vào khung giờ thấp điểm (08:15 sáng). |
| **Phát hiện lần chạy lỡ** | `schedule_history.json` có trường `missed_runs` | Máy trạm tắt nguồn hoặc chuyển chế độ Sleep qua mốc 08:15 | Kịch bản tự ghi nhận khoảng cách thời gian và số lần lỡ dự kiến. Chạy lệnh kích hoạt thủ công hoặc đợi phiên 08:15 tiếp theo. |

---

## 4. Kế hoạch Theo dõi 7 Lần Chạy Theo Lịch (Tiêu chí 13)

Để hoàn tất Tiêu chí 13 của Mục 15 đặc tả, hệ thống cần duy trì hoạt động trong tối thiểu 7 ngày liên tiếp để tích lũy 7 bản ghi tại `logs/scheduler/schedule_history.json` và các tệp log tương ứng.
- **Tình huống dữ liệu mới:** Pipeline nạp snapshot mới, chạy dbt build, phân tích lại và xuất bản.
- **Tình huống không đổi (`no_change`):** Pipeline kiểm tra mã băm SHA-256 từ API, xác nhận dữ liệu không đổi, tạo manifest `no_change` mà không sao chép thừa CSV raw, nạp lại kho dữ liệu staging và xuất bản ổn định.
