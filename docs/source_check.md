# Báo cáo Kiểm tra Nguồn dữ liệu (Giai đoạn 0)

**Thời điểm kiểm tra:** 04/11/2026 15:52 UTC+7  
**Môi trường:** Máy thực thi local (Python 3.12.10, Windows 11)  
**User-Agent sử dụng:** `hdb-elt-student-project/1.0`  
**File log/kết quả thô:** `docs/source_check_raw.json`

---

## 1. Kết quả kiểm tra API HDB Resale Flat Prices

- **Dataset ID:** `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
- **Tên dataset:** Resale flat prices based on registration date from Jan-2017 onwards
- **Trình tự gọi thực tế:**
  1. `GET /v1/public/api/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/initiate-download`  
     - HTTP Status: `201 Created`  
     - Độ trễ: `0.25s`  
     - Phản hồi: `{"code":0,"data":{"message":"Download successfully initiated. Proceed to poll download","url":"https://s3.ap-southeast-1.amazonaws.com/table-downloads-ingest.data.gov.sg/..."}}`
  2. `GET /v1/public/api/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/poll-download`  
     - HTTP Status: `201 Created`  
     - Độ trễ: `0.29s`  
     - Phản hồi: `{"code":0,"data":{"status":"DOWNLOAD_SUCCESS","url":"https://s3.ap-southeast-1.amazonaws.com/table-downloads-ingest.data.gov.sg/..."}}`
  3. `GET <data.url>`  
     - HTTP Status: `200 OK`  
     - Thời gian tải: `4.17s`  
     - Dung lượng: `24,149,037 bytes (~23.03 MB)`
- **SHA-256 của file tải về:** `59115752e6b8430545ea0814557678df7fd0514bbaba828b379a33855cb533f6`
- **Số dòng dữ liệu:** `244,119` dòng (không kể dòng tiêu đề)
- **Danh sách 11 cột:**
  1. `month`
  2. `town`
  3. `flat_type`
  4. `block`
  5. `street_name`
  6. `storey_range`
  7. `floor_area_sqm`
  8. `flat_model`
  9. `lease_commence_date`
  10. `remaining_lease`
  11. `resale_price`
- **Khoảng thời gian giao dịch:**
  - `min(month)`: `2017-01`
  - `max(month)`: `2026-11` (Dữ liệu mới nhất trùng tháng hiện tại, độ trễ 0 tháng, đạt yêu cầu <= 2 tháng)

---

## 2. Kết quả kiểm tra API MRT Station Exits

- **Dataset ID:** `d_b39d3a0871985372d7e1637193335da5`
- **Tên dataset:** LTA MRT Station Exit (GEOJSON)
- **Trình tự gọi thực tế:**
  1. `GET /v1/public/api/datasets/d_b39d3a0871985372d7e1637193335da5/initiate-download` -> HTTP 201 (0.24s)
  2. `GET /v1/public/api/datasets/d_b39d3a0871985372d7e1637193335da5/poll-download` -> HTTP 201 (`data.url` trỏ về Amazon S3)
  3. `GET <data.url>` -> HTTP 200, kích thước 213,480 bytes (~208 KB)
- **SHA-256 của file tải về:** `7a57cb14cf7c621203938e944f99b41891284e5e67876c43d9f8f3ee3aa88ee6`
- **Đánh giá:** Nguồn sẵn sàng sử dụng.

---

## 3. Kết quả kiểm tra NUS 3D HDB

- **URL:** `https://raw.githubusercontent.com/ualsg/hdb3d-data/master/README.md`
- **HTTP Status:** `200 OK`
- **Độ trễ:** `0.46s`
- **Kích thước:** 5,758 bytes
- **Đánh giá:** Repository công khai, có thể truy cập để lấy tọa độ block ban đầu.

---

## 4. Kết quả kiểm tra OneMap Search API

- **Endpoint:** `https://www.onemap.gov.sg/api/common/elastic/search`
- **Tham số thử nghiệm tối thiểu:** `searchVal=101&returnGeom=Y&getAddrDetails=Y&pageNum=1` (1 request duy nhất)
- **HTTP Status:** `200 OK`
- **Độ trễ:** `0.19s`
- **Kết quả:** `found = 5` kết quả trả về hợp lệ
- **Đánh giá:** API công khai hoạt động tốt mà không cần API key bắt buộc (hỗ trợ thêm ONEMAP_TOKEN nếu có). Cần đảm bảo rate limit <= 1 req/giây và có cache.

---

## 5. Điều khoản và Giấy phép dữ liệu

1. **data.gov.sg (HDB Resale Flat Prices & LTA MRT Station Exits):**
   - Giấy phép: **Singapore Open Data Licence** (version 1.0).
   - Quyền: Được phép sao chép, phân phối, điều chỉnh, khai thác cho mục đích thương mại và phi thương mại.
   - Nghĩa vụ bắt buộc: Ghi nhận nguồn gốc đầy đủ (attribution statement).
2. **NUS 3D HDB Dataset:**
   - Giấy phép: **MIT License**.
   - Nghĩa vụ: Ghi nhận công trình của NUS Urban Analytics Lab (Biljecki, 2020), HDB Singapore, OpenStreetMap và OneMap.
3. **OneMap Search API:**
   - Điều khoản của Singapore Land Authority (SLA).
   - Được phép truy vấn cho mục đích hiển thị và định vị; cần tuân thủ giới hạn tần suất truy vấn.

---

## 6. Phần chưa xác định và Cần lưu ý

- **Mạng lưới MRT:** Dữ liệu MRT là mạng lưới ga/cửa hiện hành (tại thời điểm tải), không thể phản ánh chính xác ngày mở ga trong quá khứ đối với các giao dịch 2017-2022. Đây là một giới hạn phân tích đã được ghi rõ trong mục 7.5 và 14 của tài liệu đặc tả.
- **Tỷ lệ khớp OneMap:** Khoảng 90% block có sẵn từ NUS 3D HDB. 10% còn lại (chủ yếu các block xây mới sau 2019) cần geocode qua OneMap Search API. Cần lưu cache để không gọi lại.

---

## 7. Kết luận Giai đoạn 0

- [x] HDB tải thành công (HTTP 201/200, 244,119 dòng).
- [x] Đủ 11 cột dự kiến theo đặc tả.
- [x] `max(month) = 2026-11`, không cũ quá 2 tháng dương lịch (0 tháng trễ).
- [x] Có đầy đủ thông tin giấy phép (Singapore Open Data Licence, MIT, SLA Terms).
- [x] Các nguồn phụ (MRT, NUS 3D HDB, OneMap) đều phản hồi tốt.

**TRẠNG THÁI: GIAI ĐOẠN 0 ĐẠT. TIẾP TỤC GIAI ĐOẠN 1.**

