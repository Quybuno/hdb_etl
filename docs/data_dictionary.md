# Từ điển Dữ liệu (Data Dictionary)

Tài liệu mô tả chi tiết các bảng dữ liệu, trường thông tin, kiểu dữ liệu và ý nghĩa nghiệp vụ trong hệ thống ELT `hdb_elt`.

---

## 1. Lớp Dữ liệu Thô (Raw Layer)

### Bảng: `raw.hdb_resale_snapshot`
Chứa toàn bộ dữ liệu thô tải về từ data.gov.sg theo từng lần chạy pipeline (`run_id`).
- `run_id` (VARCHAR): Định danh duy nhất của phiên chạy (UUID).
- `run_date` (VARCHAR): Ngày chạy theo định dạng `YYYY-MM-DD`.
- `loaded_at_utc` (TIMESTAMP): Thời điểm nạp dữ liệu vào cơ sở dữ liệu DuckDB.
- `source_row_number` (BIGINT): Thứ tự dòng trong file CSV gốc.
- `month` (VARCHAR): Tháng giao dịch theo định dạng `YYYY-MM`.
- `town` (VARCHAR): Tên khu vực hành chính (ví dụ: `BEDOK`, `TAMPINES`).
- `flat_type` (VARCHAR): Loại căn hộ (ví dụ: `3 ROOM`, `4 ROOM`, `EXECUTIVE`).
- `block` (VARCHAR): Số hiệu block tòa nhà (ví dụ: `101`, `353A`).
- `street_name` (VARCHAR): Tên đường (ví dụ: `ADMIRALTY DR`).
- `storey_range` (VARCHAR): Khoảng tầng giao dịch (ví dụ: `04 TO 06`, `10 TO 12`).
- `floor_area_sqm` (VARCHAR): Diện tích sàn căn hộ tính bằng mét vuông.
- `flat_model` (VARCHAR): Kiểu kiến trúc căn hộ (ví dụ: `Model A`, `Improved`).
- `lease_commence_date` (VARCHAR): Năm bắt đầu thời hạn thuê 99 năm (ví dụ: `1985`).
- `remaining_lease` (VARCHAR): Thời hạn thuê còn lại dạng chuỗi (ví dụ: `61 years 04 months` hoặc `61`).
- `resale_price` (VARCHAR): Giá bán lại ghi nhận bằng đô la Singapore (SGD).

---

## 2. Lớp Dữ liệu Chuẩn hóa (Staging Layer)

### Mô hình: `stg_hdb_resale`
Lấy snapshot mới nhất, ép kiểu dữ liệu chuẩn, trim khoảng trắng và tính toán các mã băm nhận diện giao dịch.
- `transaction_sk` (VARCHAR): Khóa đại diện giao dịch duy nhất = `sha256(business_hash || occurrence_no)`.
- `business_hash` (VARCHAR): Mã băm nghiệp vụ = `sha256(11 cột gốc đã trim)`.
- `occurrence_no` (INTEGER): Thứ tự xuất hiện của cùng một business_hash trong snapshot.
- `month` (VARCHAR): Tháng giao dịch (`YYYY-MM`).
- `transaction_year` (INTEGER): Năm giao dịch trích xuất từ `month`.
- `transaction_month_num` (INTEGER): Tháng giao dịch (1-12).
- `town` (VARCHAR): Tên khu vực (đã UPPER và TRIM).
- `flat_type` (VARCHAR): Loại căn hộ chuẩn hóa.
- `block` (VARCHAR): Số block tòa nhà.
- `street_name` (VARCHAR): Tên đường chuẩn hóa.
- `storey_range` (VARCHAR): Khoảng tầng gốc.
- `floor_area_sqm` (DOUBLE): Diện tích sàn căn hộ ($m^2$).
- `flat_model` (VARCHAR): Kiểu thiết kế căn hộ.
- `lease_commence_year` (INTEGER): Năm bắt đầu hợp đồng thuê.
- `remaining_lease_raw` (VARCHAR): Chuỗi thời hạn thuê còn lại gốc.
- `resale_price` (DOUBLE): Giá bán lại căn hộ (SGD).

### Mô hình: `stg_mrt_exits`
- `station` (VARCHAR): Tên ga MRT/LRT chuẩn hóa viết hoa.
- `exit_code` (VARCHAR): Mã cửa ra (ví dụ: `A`, `B`, `1`, `2`).
- `latitude` (DOUBLE): Vĩ độ WGS84.
- `longitude` (DOUBLE): Kinh độ WGS84.

### Mô hình: `stg_block_location`
- `block` (VARCHAR): Số block.
- `street_name` (VARCHAR): Tên đường.
- `latitude` (DOUBLE): Vĩ độ WGS84 của block.
- `longitude` (DOUBLE): Kinh độ WGS84 của block.
- `source` (VARCHAR): Nguồn tọa độ (`nus3d` hoặc `onemap`).
- `match_type` (VARCHAR): Độ tin cậy khớp nối (`exact`, `expanded`, `street_approx`, `not_found`).

---

## 3. Lớp Trung gian (Intermediate Layer)

### Mô hình: `int_resale_parsed`
Xử lý các trường phái sinh:
- `remaining_lease_years` (DOUBLE): Thời hạn thuê còn lại tính theo năm số thực (ví dụ: `61 years 04 months` = $61 + 4/12 = 61.33$ năm).
- `lease_band_5yr` (VARCHAR): Nhóm thời hạn thuê 5 năm (ví dụ: `50-54`, `55-59`, `60-64`, `65-69`, `70-74`, `75-79`, `80-84`, `85-89`, `90+`).
- `storey_mid` (DOUBLE): Giá trị trung vị khoảng tầng (ví dụ: `04 TO 06` -> 5.0).
- `price_per_sqm` (DOUBLE): Giá bán trên mỗi mét vuông = `resale_price / floor_area_sqm`.
- `flat_age` (INTEGER): Tuổi căn hộ tại thời điểm bán = `transaction_year - lease_commence_year`.

### Mô hình: `int_block_mrt_distance`
Tính toán khoảng cách đường thẳng Haversine từ mỗi block đến cửa ga MRT gần nhất:
- `nearest_mrt_station` (VARCHAR): Tên ga MRT gần nhất.
- `nearest_mrt_exit` (VARCHAR): Cửa ga MRT gần nhất.
- `mrt_distance_m` (DOUBLE): Khoảng cách đường thẳng đến cửa ga gần nhất (mét).
- `mrt_band` (VARCHAR): Nhóm cự ly MRT (`< 400m`, `400-799m`, `800-1199m`, `>= 1200m`).
- `cbd_distance_km` (DOUBLE): Khoảng cách đường thẳng đến Raffles Place MRT (km).

### Mô hình: `int_resale_enriched`
Kết hợp giao dịch `int_resale_parsed` với vị trí địa lý và khoảng cách `int_block_mrt_distance`.

---

## 4. Lớp Dữ liệu Phục vụ (Marts Layer)

### Kích thước (Dimensions)
- `dim_month`: Danh mục tháng, năm, quý, chỉ số chuỗi thời gian.
- `dim_town`: Danh mục khu vực, phân loại khu vực trưởng thành (mature vs non-mature).
- `dim_block`: Danh mục block, tên đường, tọa độ, cự ly MRT, cự ly CBD.
- `dim_flat_type`: Danh mục loại căn hộ (1 Room đến Executive/Multi-Generation).

### Bảng Sự kiện (Fact Table)
- `fct_resale_transaction`: Bảng giao dịch chính thức cấp độ 1 dòng / 1 giao dịch. Chứa `transaction_sk`, các khóa ngoại liên kết tới dimensions, các chỉ số đo lường (`resale_price`, `price_per_sqm`, `floor_area_sqm`, `storey_mid`, `remaining_lease_years`, `mrt_distance_m`, `cbd_distance_km`).

### Bảng Tổng hợp Marts
- `mart_town_month`: Tổng hợp theo `town`, `month`, `flat_type`, `lease_band_5yr`: số giao dịch, trung vị giá, trung bình giá, trung vị giá/$m^2$.
- `mart_budget_search`: Bảng tra cứu 12 tháng gần nhất phục vụ trang tìm kiếm căn hộ theo ngân sách, cự ly MRT và thời hạn thuê tối thiểu.

---

## 5. Lớp Phân tích Thống kê (Analytics Tables)

- `analytics.lease_curve`: Hệ số hồi quy hedonic theo nhóm thời hạn thuê 5 năm (nhóm tham chiếu 70-75 năm), kèm sai số chuẩn gom cụm theo block và khoảng tin cậy 95% cho 2 thời kỳ (2017-2022 và 2023-nay).
- `analytics.town_lease_gap`: Mức chênh lệch giá giữa nhóm thời hạn thuê ngắn (55-65 năm) và nhóm tham chiếu (70-80 năm) theo từng khu vực.
- `analytics.price_index`: Chỉ số giá hedonic đã kiểm soát thành phần căn hộ qua các năm so với mức tăng trung vị thô (năm gốc 2019 = 100).
- `analytics.analysis_run`: Nhật ký các lần chạy mô hình phân tích, tham số và trạng thái.

---

## 6. Lớp Vận hành (Operations Layer)

- `ops.pipeline_run`: Nhật ký thực thi pipeline (run_id, thời gian bắt đầu/kết thúc, trạng thái, thời gian chạy).
- `ops.snapshot_delta`: Biến động số dòng giữa hai snapshot liên tiếp.
- `ops.quality_result`: Kết quả kiểm tra của bộ kiểm soát chất lượng (Quality Gate).
- `ops.source_freshness`: Độ trễ của dữ liệu nguồn so với ngày chạy hiện tại.

