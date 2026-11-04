# Đặc tả dự án: Căn hộ có hạn dùng

**Tên đầy đủ:** Căn hộ có hạn dùng: giá HDB Singapore thay đổi thế nào khi thời hạn thuê còn lại ngắn đi?

**Loại dự án:** Tiểu luận môn Trực quan hóa dữ liệu, gồm hệ thống ELT cơ bản và dashboard cập nhật định kỳ.

**Thư mục triển khai đề xuất:** `D:\video\hdb_elt`

---

## 0. Hướng dẫn bắt buộc cho agent

Đọc toàn bộ file này trước khi viết code.

1. Làm đúng thứ tự các giai đoạn ở mục 12. Không bỏ qua Giai đoạn 0.
2. Chỉ dùng dữ liệu thật. Không giả lập, nội suy hoặc tự điền số liệu.
3. Không dùng VPN, proxy, giả trình duyệt hoặc cách khác để vượt chặn truy cập. Nếu nguồn bị chặn: ghi lại, dừng lại, báo cáo.
4. Không ghi "đã xong", "đạt" hoặc số liệu nếu chưa chạy thật và chưa có log.
5. Mọi số liệu trên dashboard và trong báo cáo phải đọc từ mart hoặc file kết quả. Không viết cứng số.
6. Không sao chép code, câu chữ hoặc biểu đồ từ `tianjiaoma2026-lab/hdb-resale-dashboard`. Repo đó không có file LICENSE được tìm thấy khi đánh giá; chỉ dùng để tham khảo ý tưởng.
7. Không in, ghi log, commit token hoặc email. Dùng User-Agent chung, ví dụ `hdb-elt-student-project/1.0`.
8. Không kết luận nguyên nhân từ tương quan. Dùng các từ "liên quan", "đi cùng", "chênh lệch".
9. Không dự báo giá tương lai.
10. Sau mỗi giai đoạn, cập nhật `docs/progress.md`: việc đã làm, lệnh đã chạy, kết quả, lỗi, việc tiếp theo.

Nếu một yêu cầu trong file này mâu thuẫn với dữ liệu thực tế, không tự ý nới ngưỡng. Ghi vấn đề vào `docs/decisions.md` và dừng ở mục bị ảnh hưởng.

---

## 1. Bối cảnh và vấn đề

Căn hộ HDB được bán lại với thời hạn thuê còn lại khác nhau. Người mua không chỉ mua diện tích và vị trí, mà còn mua số năm còn lại của hợp đồng thuê. Hai căn cùng khu và cùng loại có thể khác giá vì thời hạn còn lại khác nhau.

**Vấn đề cần giải quyết:** người mua khó đọc giá bán lại vì giá bị ảnh hưởng đồng thời bởi khu, loại căn, diện tích, tầng và thời hạn còn lại. Trung vị thô dễ gây hiểu nhầm khi thành phần căn được bán thay đổi theo thời gian.

**Sản phẩm mong muốn:** một hệ thống lấy dữ liệu chính thức theo lịch, kiểm tra chất lượng, tạo bảng phân tích và dashboard giúp người dùng:

- Xem đường cong giá theo thời hạn thuê còn lại.
- Phân biệt mức giá thô và mức giá đã kiểm soát đặc điểm căn.
- Thu hẹp khu phù hợp với ngân sách và yêu cầu thời hạn thuê.

---

## 2. Người dùng và quyết định hỗ trợ

| Người dùng | Câu hỏi cần trả lời | Quyết định |
|---|---|---|
| Người mua nhà | Với ngân sách này, nên xem khu nào và thời hạn nào? | Thu hẹp danh sách khu và block |
| Nhà phân tích thị trường | Giá tăng thật hay chỉ do thành phần giao dịch thay đổi? | Chọn chỉ số theo dõi phù hợp |
| Quản lý sản phẩm bất động sản hoặc cố vấn tài chính | Mức chênh theo thời hạn thuê khác nhau thế nào giữa các khu? | Xác định phân khúc cần giải thích kỹ cho khách hàng |

Dự án không tư vấn đầu tư, không định giá một căn cụ thể và không thay thế thẩm định giá.

---

## 3. Phạm vi

### Có làm

- ELT từ nguồn công khai.
- Lưu raw bất biến theo từng lần chạy.
- dbt models, dbt tests, tài liệu dbt.
- Phân tích bằng Python.
- Dashboard Streamlit gồm trang vận hành pipeline.
- Lịch chạy cục bộ.
- Báo cáo kết quả.

### Không làm

- Realtime hoặc streaming.
- Dự báo giá.
- Thẩm định giá.
- Xếp hạng khu "đáng mua nhất".
- Kết luận nhân quả.
- Dữ liệu cá nhân.
- Tư vấn vay, CPF hoặc pháp lý.

---

## 4. Nguồn dữ liệu

### 4.1. Nguồn chính bắt buộc

**HDB Resale Flat Prices**

- Dataset: `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
- Trang dữ liệu: `https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view`
- API cơ sở: `https://api-open.data.gov.sg/v1/public/api/datasets`
- Quy trình tải:
  1. GET `/{dataset_id}/initiate-download`
  2. GET `/{dataset_id}/poll-download`
  3. Chờ `data.status == DOWNLOAD_SUCCESS` hoặc có `data.url`
  4. Tải CSV từ `data.url`
- Các cột dự kiến: `month`, `town`, `flat_type`, `block`, `street_name`, `storey_range`, `floor_area_sqm`, `flat_model`, `lease_commence_date`, `remaining_lease`, `resale_price`
- Giấy phép: Singapore Open Data Licence. Agent phải xác minh và ghi điều khoản ghi nguồn.

Tính đến khi viết đặc tả, trang dữ liệu mô tả phạm vi 01/2017 đến 11/2026 và "Updated daily". Agent phải đo lại từ nguồn thật.

### 4.2. Nguồn hỗ trợ

| Nguồn | ID hoặc URL | Dùng để làm gì | Tần suất |
|---|---|---|---|
| LTA MRT Station Exit | Dataset `d_b39d3a0871985372d7e1637193335da5` | Tính khoảng cách MRT | Tải lại khi cần, tối thiểu mỗi tháng |
| NUS 3D HDB | `https://github.com/ualsg/hdb3d-data` | Tọa độ block ban đầu | Một lần |
| OneMap Search API | `https://www.onemap.gov.sg/api/common/elastic/search` | Tọa độ block mới | Chỉ gọi cho địa chỉ chưa có |

Với OneMap:

- Tốc độ tối đa 1 request/giây nếu không có token.
- Token tùy chọn lưu trong `.env` với tên `ONEMAP_TOKEN`.
- Cache kết quả.
- Không tra lại địa chỉ đã có.

### 4.3. Nguồn không bắt buộc

Không thêm nguồn khác trong phiên bản đầu. Lãi suất, lạm phát hoặc giá thuê chỉ được thêm sau khi hoàn thành nghiệm thu và có câu hỏi phân tích riêng.

---

## 5. Kiến trúc

```text
data.gov.sg / LTA / NUS / OneMap
        |
        v
Extract bằng Python
        |
        v
data/raw/<source>/run_date=YYYY-MM-DD/run_id=<id>/
        |
        v
Load vào DuckDB raw schema
        |
        v
dbt: staging -> intermediate -> marts
        |
        v
analysis Python ghi bảng kết quả
        |
        v
Kiểm tra chất lượng
        |
        v
Publish warehouse.duckdb
        |
        v
Streamlit
```

### Công nghệ

| Lớp | Lựa chọn |
|---|---|
| Ngôn ngữ | Python 3.11 trở lên |
| Lưu raw | Thư mục local |
| Warehouse | DuckDB |
| Transform | dbt-core và dbt-duckdb |
| Phân tích | pandas, numpy, statsmodels |
| Dashboard | Streamlit, Plotly |
| Kiểm thử | pytest, dbt tests |
| Lịch chạy | Windows Task Scheduler |
| Cấu hình | `.env`, `config/settings.yml` |
| Quản lý mã | Git |

Airflow và MinIO không bắt buộc. Chỉ thêm ở Giai đoạn 7 nếu hệ thống cốt lõi đã nghiệm thu.

---

## 6. Cấu trúc thư mục

```text
hdb_elt/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── settings.yml
│   └── analysis_rules.yml
├── data/
│   ├── raw/
│   ├── reference/
│   └── warehouse/
│       ├── warehouse_staging.duckdb
│       └── warehouse.duckdb
├── pipeline/
│   ├── extract_hdb.py
│   ├── extract_mrt.py
│   ├── extract_blocks.py
│   ├── load_raw.py
│   ├── quality_gate.py
│   ├── publish.py
│   ├── run_pipeline.py
│   └── common/
├── dbt_hdb/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   ├── marts/
│   │   └── ops/
│   └── tests/
├── analysis/
│   ├── lease_curve.py
│   ├── town_lease_gap.py
│   ├── price_index.py
│   └── run_analysis.py
├── app/
│   ├── Home.py
│   ├── pages/
│   └── db.py
├── tests/
├── scripts/
│   ├── run_pipeline.ps1
│   └── register_task.ps1
├── logs/
├── docs/
│   ├── progress.md
│   ├── decisions.md
│   ├── data_dictionary.md
│   ├── source_check.md
│   ├── analysis_results.md
│   └── runbook.md
└── report/
    └── report.md
```

`data/raw`, `data/warehouse`, `.env` và `logs` không commit.

---

## 7. Thiết kế dữ liệu

### 7.1. Raw

Mỗi lần chạy lưu:

```text
data/raw/hdb_resale/run_date=YYYY-MM-DD/run_id=<uuid>/hdb_resale.csv
data/raw/hdb_resale/run_date=YYYY-MM-DD/run_id=<uuid>/manifest.json
```

`manifest.json` tối thiểu gồm:

```json
{
  "run_id": "",
  "source": "hdb_resale",
  "dataset_id": "",
  "started_at_utc": "",
  "finished_at_utc": "",
  "http_status": 200,
  "row_count": 0,
  "columns": [],
  "sha256": "",
  "status": "success",
  "error": null
}
```

Không sửa hoặc ghi đè file raw. Nếu SHA-256 giống snapshot gần nhất, ghi trạng thái `no_change`; vẫn lưu `manifest.json`, không cần tạo bản sao CSV.

### 7.2. Định danh dòng

Nguồn không có mã giao dịch. Tạo hai trường:

```text
business_hash = sha256(11 cột gốc đã trim)
occurrence_no = thứ tự xuất hiện của cùng business_hash trong snapshot
transaction_sk = sha256(business_hash || occurrence_no)
```

Không tự xóa các dòng giống nhau. Báo cáo số dòng có `occurrence_no > 1` như một giới hạn.

### 7.3. Bảng raw trong DuckDB

`raw.hdb_resale_snapshot`:

- `run_id`
- `run_date`
- `loaded_at_utc`
- `source_row_number`
- `month`, `town`, `flat_type`, `block`, `street_name`, `storey_range`, `floor_area_sqm`, `flat_model`, `lease_commence_date`, `remaining_lease`, `resale_price` dạng text

### 7.4. Các mô hình dbt

**Staging**

| Mô hình | Yêu cầu |
|---|---|
| `stg_hdb_resale` | Lấy snapshot thành công mới nhất, đổi kiểu dữ liệu, chuẩn hóa chữ, tạo hash |
| `stg_mrt_exits` | Chuẩn hóa ga, cửa, tọa độ |
| `stg_block_location` | Chuẩn hóa block, đường, tọa độ, nguồn tọa độ |

**Intermediate**

| Mô hình | Yêu cầu |
|---|---|
| `int_resale_parsed` | Tính `remaining_lease_years`, `storey_mid`, `price_per_sqm`, `flat_age`, nhóm thuê 5 năm |
| `int_block_mrt_distance` | Tính khoảng cách Haversine đến cửa MRT gần nhất |
| `int_resale_enriched` | Ghép giao dịch với tọa độ block, MRT, CBD |

**Marts**

| Mô hình | Hạt dữ liệu | Công dụng |
|---|---|---|
| `dim_month` | 1 tháng | Lịch |
| `dim_town` | 1 khu | Thông tin khu |
| `dim_block` | 1 block + đường | Block, tọa độ, MRT, CBD |
| `dim_flat_type` | 1 loại căn | Danh mục loại căn |
| `fct_resale_transaction` | 1 giao dịch | Bảng sự kiện chính |
| `mart_town_month` | Khu-tháng-loại căn | Xu hướng |
| `mart_budget_search` | Block-loại căn | Lọc theo ngân sách |

**Bảng từ Python analysis**

| Bảng | Công dụng |
|---|---|
| `analytics.lease_curve` | Đường cong giá theo nhóm thuê |
| `analytics.town_lease_gap` | Chênh lệch theo khu |
| `analytics.price_index` | Chỉ số giá đã kiểm soát thành phần |
| `analytics.analysis_run` | Tham số, thời điểm, trạng thái |

**Vận hành**

| Bảng | Công dụng |
|---|---|
| `ops.pipeline_run` | Lịch sử chạy |
| `ops.snapshot_delta` | Số dòng mới và mất đi giữa hai snapshot |
| `ops.quality_result` | Kết quả kiểm tra |
| `ops.source_freshness` | Độ mới dữ liệu |

### 7.5. Khoảng cách

- MRT: Haversine đến cửa gần nhất.
- CBD: Raffles Place MRT, tọa độ `1.28393, 103.85144`.
- Đây là khoảng cách đường thẳng, không phải đi bộ.
- Mạng MRT là hiện tại, nên không dùng để kết luận tác động của ga mới.

---

## 8. Pipeline và độ tin cậy

Lệnh chính:

```powershell
python pipeline/run_pipeline.py
```

Trình tự:

1. Tạo `run_id`.
2. Tải HDB và lưu raw.
3. Cập nhật nguồn phụ nếu đến hạn.
4. Tra tọa độ block mới.
5. Nạp raw vào `warehouse_staging.duckdb`.
6. Chạy dbt.
7. Chạy analysis.
8. Chạy quality gate.
9. Nếu đạt, publish sang `warehouse.duckdb` bằng cách thay file nguyên tử.
10. Nếu trượt, giữ nguyên `warehouse.duckdb`, ghi lỗi và trả exit code khác 0.
11. Ghi `ops.pipeline_run`.

Yêu cầu:

- Chạy lại cùng một `run_id` không tạo trùng dữ liệu.
- Tối đa 3 lần retry khi lỗi mạng, có backoff.
- Không retry khi bị 403.
- Timeout mọi request.
- Không chạy chồng hai pipeline.
- Dashboard chỉ đọc `warehouse.duckdb`.

---

## 9. Chất lượng dữ liệu

### 9.1. Điều kiện chặn publish

| Kiểm tra | Ngưỡng |
|---|---|
| Số cột HDB | Đúng 11 cột dự kiến |
| File | Không trống |
| Số dòng | Không giảm quá 1% so với snapshot publish gần nhất |
| `month`, `town`, `flat_type`, `block`, `street_name`, `resale_price` | Null ≤ 0,1% |
| `resale_price` | Lớn hơn 0 |
| `floor_area_sqm` | Lớn hơn 0 |
| Parse `remaining_lease` | Lỗi ≤ 0,1% |
| Parse `storey_range` | Lỗi ≤ 0,1% |
| `transaction_sk` | Duy nhất |
| Dòng raw so với fact | Lệch 0 dòng |
| Nối tọa độ block | Ít nhất 98% giao dịch |
| Độ mới | `max(month)` không cũ quá 2 tháng dương lịch so với ngày chạy |

### 9.2. Điều kiện cảnh báo

- Tỷ lệ dòng trùng theo `business_hash`.
- Tỷ lệ dữ liệu đổi giữa hai snapshot.
- Khu hoặc loại căn mới.
- Block chưa có tọa độ.
- Biến động trung vị tháng lớn hơn 30%.
- Giá trị ngoài phân vị 0,1% hoặc 99,9%.

Cảnh báo không chặn publish, nhưng phải hiện trên trang vận hành.

### 9.3. Kiểm thử

- pytest cho parser, hash, manifest, quality gate.
- dbt tests cho khóa, not null, accepted values, relationships.
- Một phép đối chiếu thủ công: chọn 20 dòng ngẫu nhiên từ fact và truy vết về CSV raw.

---

## 10. Câu hỏi phân tích

Trước khi chạy Giai đoạn 4, ghi quy tắc vào `config/analysis_rules.yml` và lưu SHA-256. Sau đó không sửa ngưỡng. Thay đổi phải ghi trong `docs/decisions.md` và không được gọi là kết quả xác nhận.

### Thông tin khám phá đã biết

Phân tích nhanh trên file đã làm sạch của repo tham khảo cho thấy:

- Quan hệ giữa giá và thời hạn thuê có vẻ không tuyến tính.
- Hệ số thuê theo từng năm dao động, chưa thấy xu hướng tăng hoặc giảm đều.
- Hệ số MRT thay đổi mạnh khi thêm kiểm soát theo khu.
- Giao dịch cùng block không độc lập.

Đây chỉ là khám phá. Agent phải tính lại từ raw của dự án.

### Q1. Đường cong thời hạn thuê

**Câu hỏi:** Khi thời hạn thuê còn lại ngắn đi, giá giảm theo đường cong nào sau khi kiểm soát đặc điểm căn?

**Phương pháp:**

- Đơn vị: giao dịch.
- Biến phụ thuộc: `log(resale_price)`.
- Biến chính: nhóm thuê 5 năm.
- Nhóm tham chiếu: 70–75 năm.
- Kiểm soát: diện tích, tầng, loại căn, khu, tháng.
- Sai số gom theo block.
- Chia hai giai đoạn: 2017–2022 và 2023–nay.

**Đạt khi:**

- Mọi nhóm từ 50–90 năm có ít nhất 1.000 giao dịch trong mỗi giai đoạn.
- Spearman giữa hệ số hai giai đoạn ≥ 0,90.
- Sai khác tuyệt đối giữa hai giai đoạn ≤ 5 điểm phần trăm ở các nhóm từ 50–85 năm.

Nhóm 90+ được báo cáo riêng vì có thể bị lẫn hiệu ứng căn mới.

### Q2. Khác biệt theo khu

**Câu hỏi:** Mức chênh giữa nhóm thuê ngắn và nhóm tham chiếu có khác nhau giữa các khu không?

**Phương pháp:**

- So sánh thời hạn 55–65 năm với 70–80 năm.
- Chỉ dùng khu có ít nhất 200 giao dịch mỗi nhóm.
- Kiểm soát diện tích, tầng, loại căn, tháng.
- Sai số gom theo block.

**Đạt khi:**

- Có ít nhất 10 khu đủ dữ liệu.
- Spearman thứ hạng mức chênh giữa 2017–2022 và 2023–nay ≥ 0,60.

Không gọi khu nào "đáng mua hơn". Chỉ mô tả mức chênh.

### Q3. Giá thật sự tăng bao nhiêu?

**Câu hỏi:** Mức tăng thô khác gì mức tăng đã kiểm soát thành phần căn?

**Phương pháp:**

- Tính trung vị thô theo năm.
- Tính chỉ số hedonic với hiệu ứng năm.
- So sánh 2019 và năm đầy đủ gần nhất.
- Kiểm tra độ nhạy trong cùng block nếu đủ dữ liệu.

**Đạt khi:**

- Có đủ các năm đầy đủ từ 2017 đến năm đầy đủ gần nhất.
- Có kết quả cho toàn bộ và ít nhất ba loại căn.
- Báo cáo khoảng tin cậy hoặc kiểm tra độ nhạy.

### Q4. Hỗ trợ người mua

**Câu hỏi:** Với ngân sách, loại căn, thời hạn tối thiểu và khoảng cách MRT, khu nào có giao dịch gần đây phù hợp?

**Yêu cầu:**

- Dùng 12 tháng gần nhất.
- Hiển thị số giao dịch đủ điều kiện.
- Không hiển thị khu có dưới 10 giao dịch.
- Không tạo điểm "đáng mua".
- Không dự báo giá.
- Có câu cảnh báo: "Kết quả mô tả giao dịch đã đăng ký gần đây, không phải định giá."

---

## 11. Dashboard

### Nguyên tắc

- Mỗi trang trả lời một câu hỏi.
- Tiêu đề biểu đồ nêu kết luận được dữ liệu hỗ trợ.
- Có phần "Quyết định hỗ trợ" và "Giới hạn".
- Hiển thị ngày dữ liệu mới nhất.
- Không viết cứng số.
- Không dùng màu làm kênh duy nhất để truyền thông tin.
- Giao diện dùng tiếng Việt, giữ tên riêng Singapore.

### Các trang

| Trang | Câu hỏi | Biểu đồ chính |
|---|---|---|
| Tổng quan | Thị trường đang ở đâu? | Thẻ giao dịch, trung vị, thời hạn; xu hướng; bản đồ tóm tắt |
| Đường cong thuê | Giá thay đổi theo thời hạn thế nào? | Đường cong hệ số và khoảng tin cậy |
| So sánh khu | Khu nào có mức chênh khác biệt? | Dot plot hoặc bar plot có khoảng tin cậy |
| Giá đã điều chỉnh | Giá tăng thô và đã kiểm soát khác nhau ra sao? | Hai đường theo thời gian |
| Công cụ tìm khu | Với điều kiện này nên xem khu nào? | Bảng, bản đồ, phân bố giá |
| Vận hành | Hệ thống có đang khỏe không? | Lần chạy cuối, độ mới, dòng mới, kiểm tra, lỗi |

### Bộ lọc

- Năm.
- Khu.
- Loại căn.
- Nhóm thời hạn.
- Ngân sách.
- Khoảng cách MRT.

---

## 12. Các giai đoạn thực hiện

### Giai đoạn 0. Kiểm tra nguồn

**Mục tiêu:** xác nhận tải được dữ liệu từ máy thực thi.

Việc cần làm:

1. Gọi API HDB, ghi HTTP status, độ trễ, số dòng, cột, min/max tháng, SHA-256.
2. Gọi API MRT.
3. Kiểm tra `hdb3d-data` và OneMap.
4. Đọc và ghi điều khoản dữ liệu.
5. Tạo `docs/source_check.md`.

**Điều kiện qua giai đoạn:**

- HDB tải thành công.
- Có đủ 11 cột.
- `max(month)` đạt điều kiện độ mới.
- Có điều khoản sử dụng.

**Nếu trượt:** dừng, không xây hệ thống. Báo lại để chủ dự án quyết định chuyển sang phương án dự phòng.

### Giai đoạn 1. Khởi tạo và Extract

- Tạo repo.
- Cài môi trường.
- Viết extractor và manifest.
- Viết `docs/data_dictionary.md`.

### Giai đoạn 2. Load và dbt

- Nạp raw vào DuckDB.
- Viết staging, intermediate, marts.
- Viết dbt tests.
- Tạo tài liệu dbt.

### Giai đoạn 3. Kiểm soát chất lượng

- Viết quality gate.
- Viết publish.
- Viết pytest.
- Kiểm thử tình huống lỗi: thiếu cột, file trống, số dòng giảm.

### Giai đoạn 4. Phân tích

- Tạo `config/analysis_rules.yml` và SHA-256.
- Chạy Q1, Q2, Q3.
- Ghi `docs/analysis_results.md`.

### Giai đoạn 5. Dashboard

- Xây các trang.
- Kết nối bảng thật.
- Kiểm thử bộ lọc.
- Chụp ảnh màn hình ở cỡ desktop.

### Giai đoạn 6. Lịch chạy và vận hành

- Tạo `scripts/register_task.ps1`.
- Đăng ký Task Scheduler chạy hằng ngày.
- Theo dõi ít nhất 7 lần chạy theo lịch.
- Cập nhật `docs/runbook.md`.

### Giai đoạn 7. Mở rộng tùy chọn

Chỉ làm khi Giai đoạn 0–6 đã đạt:

- Airflow.
- MinIO.
- Docker Compose.
- Triển khai dashboard công khai.

### Giai đoạn 8. Báo cáo

Viết `report/report.md` theo mục 13.

---

## 13. Cấu trúc báo cáo

1. Mở đầu bằng một ví dụ thật: hai căn tương tự nhưng thời hạn thuê khác nhau.
2. Vấn đề và người dùng.
3. Câu hỏi phân tích.
4. Nguồn dữ liệu và giấy phép.
5. Kiến trúc ELT.
6. Kiểm soát chất lượng.
7. Phân tích và phương pháp.
8. Dashboard.
9. Kết quả: Quan sát, Diễn giải, Đề xuất.
10. Giới hạn.
11. Vận hành thực tế.
12. Kết luận.
13. Phụ lục: từ điển dữ liệu, nguồn, cách chạy lại.

Phần kết quả luôn tách:

- **Quan sát:** số đo trực tiếp.
- **Diễn giải:** cách hiểu có điều kiện.
- **Đề xuất:** việc cần làm và chỉ số theo dõi.

---

## 14. Giới hạn bắt buộc phải nêu

- Dữ liệu là giao dịch đã đăng ký, không phải toàn bộ cung cầu.
- Dữ liệu theo tháng.
- Không có mã giao dịch hoặc vị trí căn chính xác.
- Giá bán không phải giá thuê.
- Chưa điều chỉnh lạm phát.
- Thành phần căn được bán thay đổi theo thời gian.
- Thời hạn thuê liên quan đến tuổi căn và chất lượng căn.
- Khoảng cách là đường thẳng.
- Mạng MRT là hiện tại.
- Kết quả là mối liên quan, không phải nhân quả.
- Không phải tư vấn tài chính.

---

## 15. Tiêu chí nghiệm thu

Dự án chỉ được coi là hoàn thành khi có bằng chứng:

- [ ] Giai đoạn 0 đạt.
- [ ] `python pipeline/run_pipeline.py` chạy từ đầu đến cuối.
- [ ] Raw được lưu theo từng lần chạy và có manifest.
- [ ] Chạy lại không tạo dữ liệu trùng.
- [ ] `dbt build` thành công.
- [ ] pytest thành công.
- [ ] Quality gate chặn được file lỗi trong kiểm thử.
- [ ] Publish giữ dashboard ở phiên bản tốt gần nhất khi lỗi.
- [ ] Q1 đạt.
- [ ] Ít nhất một trong Q2 hoặc Q3 đạt.
- [ ] Q4 hoạt động với bộ lọc và không có điểm "đáng mua".
- [ ] Dashboard đọc dữ liệu thật và có trang vận hành.
- [ ] Có ít nhất 7 lần chạy theo lịch, kể cả lần `no_change`, được ghi lại.
- [ ] README cho phép người khác chạy lại.
- [ ] Báo cáo có giới hạn và nguồn dữ liệu.
- [ ] Không có token hoặc dữ liệu raw lớn trong Git.

Nếu Q1 trượt, không nới ngưỡng. Thu hẹp phạm vi hoặc báo cáo rằng đường cong không ổn định.

---

## 16. Rủi ro và cách xử lý

| Rủi ro | Dấu hiệu | Xử lý |
|---|---|---|
| API bị chặn hoặc đổi | 403, thiếu URL tải, đổi cột | Dừng, ghi lỗi, không vượt chặn |
| Dataset đổi cấu trúc | Quality gate thiếu cột | Không publish, cập nhật mapping có ghi nhận |
| Dữ liệu ít mới | `no_change` nhiều lần | Giữ dashboard và ghi rõ độ mới |
| Không có khóa giao dịch | Dòng trùng | Dùng `occurrence_no`, báo cáo giới hạn |
| Mô hình dễ bị hiểu sai | Người đọc nghĩ là nhân quả | Dùng ngôn ngữ mô tả, nêu giới hạn |
| Trùng với repo công khai | Câu hỏi và biểu đồ giống nhau | Tập trung vào đường cong thuê và tự viết code |

---

## 17. Việc cần chủ dự án xác nhận

- Môn học có chấp nhận dữ liệu cập nhật theo batch không.
- Đề tài có trùng với nhóm không, đặc biệt các đề bất động sản Hà Nội.
- Hạn nộp và giới hạn thời gian.
- Có cần dùng Airflow, MinIO hoặc Docker để đạt yêu cầu môn học không.

## 18. Lệnh mục tiêu

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python pipeline/run_pipeline.py
cd dbt_hdb
dbt build
cd ..
pytest
streamlit run app/Home.py
```

## 19. Nguồn tham khảo

- HDB Resale Flat Prices: https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view
- LTA MRT Station Exit: https://data.gov.sg/datasets/d_b39d3a0871985372d7e1637193335da5/view
- NUS 3D HDB dataset: https://github.com/ualsg/hdb3d-data
- OneMap API documentation: https://www.onemap.gov.sg/apidocs/
- Repo tham khảo ý tưởng, không sao chép: https://github.com/tianjiaoma2026-lab/hdb-resale-dashboard
