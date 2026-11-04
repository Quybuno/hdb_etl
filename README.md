# Căn hộ có hạn dùng: Giá HDB Singapore thay đổi thế nào khi thời hạn thuê còn lại ngắn đi?

Dự án môn Trực quan hóa Dữ liệu (DS608 / Data Visualization), bao gồm hệ thống ELT định kỳ và dashboard phân tích giá bán lại căn hộ Housing & Development Board (HDB) tại Singapore dựa trên thời hạn thuê còn lại (remaining lease).

---

## 1. Giới thiệu và Mục tiêu

Căn hộ HDB tại Singapore có thời hạn thuê 99 năm. Người mua không chỉ mua diện tích và vị trí, mà còn mua số năm còn lại của hợp đồng thuê. Hệ thống này giải quyết bài toán:
- Tự động trích xuất dữ liệu bán lại chính thức từ data.gov.sg (Jan 2017 - nay) và dữ liệu địa lý (MRT, OneMap, NUS 3D).
- Lưu trữ raw snapshot bất biến và kiểm soát chất lượng dữ liệu (Quality Gate).
- Chuyển đổi dữ liệu có cấu trúc qua dbt (staging, intermediate, marts).
- Phân tích hồi quy hedonic kiểm soát đặc điểm căn hộ (diện tích, tầng, khu vực, thời điểm giao dịch) với sai số gom cụm theo block.
- Trực quan hóa toàn diện trên Streamlit dashboard.

---

## 2. Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo mô hình **Batch ELT hiện đại (Extract - Load - Transform)**, kết hợp kiểm soát chất lượng nghiêm ngặt (Quality Gate) và xuất bản nguyên tử (Atomic Publish) để đảm bảo độ tin cậy của kho dữ liệu phục vụ ứng dụng Dashboard:

```mermaid
flowchart TD
    subgraph SOURCES ["1. Nguồn Dữ liệu (External Data Sources)"]
        S1["HDB Resale Flat Prices<br/>(data.gov.sg API)"]
        S2["LTA MRT Station Exits<br/>(data.gov.sg GeoJSON)"]
        S3["NUS 3D HDB Dataset<br/>(Tọa độ khối nhà)"]
        S4["SLA OneMap API<br/>(Geocoding bổ sung)"]
    end

    subgraph EXTRACT ["2. Trích xuất & Bất biến (Extract & Manifest)"]
        E1["extract_hdb.py<br/>(SHA-256 deduplication)"]
        E2["extract_mrt.py<br/>(613 ga & cửa MRT)"]
        E3["extract_blocks.py<br/>(9,769 block tòa nhà)"]
        RAW[("data/raw/hdb_resale/<br/>Immutable CSV & manifest.json")]
    end

    subgraph STAGING ["3. Nạp & Chuyển đổi dbt (warehouse_staging.duckdb)"]
        L1["load_raw.py<br/>(Nạp raw schema)"]
        subgraph DBT ["dbt-duckdb Transformation (dbt build)"]
            STG["Staging Models<br/>(stg_hdb_resale, stg_mrt_exits, stg_block_location)<br/>business_hash & occurrence_no & transaction_sk"]
            INT["Intermediate Models<br/>(int_resale_parsed, int_block_mrt_distance, int_resale_enriched)<br/>Haversine MRT & CBD"]
            MARTS["Marts & Ops Models<br/>(dim_*, fct_resale_transaction, mart_*, ops_*)<br/>24 dbt Data Tests PASS"]
        end
    end

    subgraph ANALYSIS ["4. Phân tích Kinh tế lượng (config/analysis_rules.yml)"]
        Q1["Q1: Đường cong thời hạn thuê<br/>(Lease Curve 5 năm - FAIL)"]
        Q2["Q2: Mức chênh theo khu vực<br/>(13 khu vực & Leave-one-out - PASS)"]
        Q3["Q3: Chỉ số giá Hedonic vs Thô<br/>(Chuỗi 2017-2026 kèm 95% CI cụm - PASS)"]
        AN_TABLES[("analytics schema<br/>lease_curve, town_lease_gap, price_index")]
    end

    subgraph QUALITY ["5. Kiểm soát Chất lượng & Xuất bản (Quality Gate & Publish)"]
        QG{"Quality Gate<br/>(12 Blocking Checks)"}
        PUB["publish.py<br/>(Atomic replace & Retry 5 lần trên Windows)"]
    end

    subgraph SERVING ["6. Kho Sản xuất & Ứng dụng (Production & Serving)"]
        PROD[("data/warehouse/warehouse.duckdb<br/>(Bản ghi sản xuất - Read Only)")]
        DASH["Streamlit Dashboard<br/>(app/Home.py - 6 trang trực quan)"]
        SCHED["Windows Task Scheduler<br/>(HDB_ELT_Daily_Run - 08:15 AM hàng ngày)"]
        LOGS["Nhật ký & Lần chạy lỡ<br/>(logs/scheduler/ & schedule_history.json)"]
    end

    %% Luồng dữ liệu
    S1 --> E1
    S2 --> E2
    S3 --> E3
    S4 --> E3

    E1 --> RAW
    E2 --> L1
    E3 --> L1
    RAW --> L1

    L1 --> STG
    STG --> INT
    INT --> MARTS

    MARTS --> Q1
    MARTS --> Q2
    MARTS --> Q3

    Q1 --> AN_TABLES
    Q2 --> AN_TABLES
    Q3 --> AN_TABLES

    MARTS --> QG
    AN_TABLES --> QG

    QG -- "PASS (12/12 checks)" --> PUB
    QG -- "FAIL" --> REJECT["Từ chối xuất bản<br/>Bảo toàn kho cũ"]

    PUB --> PROD
    PROD --> DASH
    SCHED --> |"Điều phối tự động"| E1
    SCHED --> LOGS
```

### Các thành phần cốt lõi:
1. **Extract & Immutability:** Trích xuất từ 4 nguồn chính thống (API HDB, LTA MRT, NUS 3D, OneMap SLA). Lưu trữ tệp raw CSV bất biến kèm `manifest.json` và cơ chế chống nhân bản dựa trên SHA-256 (`status: no_change`).
2. **Load & dbt Transformation:** Nạp raw vào `warehouse_staging.duckdb`. dbt thực thi quy trình chuyển đổi 3 lớp (Staging $\rightarrow$ Intermediate $\rightarrow$ Marts & Ops). Tự động tính toán định danh duy nhất `transaction_sk` (kết hợp `business_hash` và `occurrence_no` bảo toàn 100% dòng trùng gốc) và cự ly Haversine tới 613 cửa MRT và CBD.
3. **Econometric Analysis:** Mô hình định giá Hedonic cố định theo quy tắc đã khóa `config/analysis_rules.yml` (SHA-256 xác thực), lưu trữ kết quả phân tích (Q1, Q2, Q3) vào schema `analytics`.
4. **Quality Gate & Atomic Publish:** Thực thi 12 quy tắc kiểm tra nghiêm ngặt (chặn xuất bản nếu thiếu cột, file rỗng, số dòng sụt giảm > 1%, hoặc null trường cốt lõi). Xuất bản nguyên tử qua cơ chế thay thế tệp kèm retry 5 lần chống lỗi khóa tệp trên Windows.
5. **Serving & Automation:** Kho dữ liệu sản xuất `warehouse.duckdb` phục vụ Streamlit Dashboard 6 màn hình chuyên đề (chế độ Read-Only). Tự động hóa lịch chạy định kỳ hằng ngày lúc 08:15 AM qua Windows Task Scheduler (`\HDB_ELT_Daily_Run`) với nhật ký độc lập và phát hiện lần chạy lỡ.

---

## 3. Cấu trúc thư mục

```text
hdb_elt/
├── README.md                 # Hướng dẫn dự án
├── requirements.txt          # Thư viện phụ thuộc
├── .env.example              # Mẫu cấu hình môi trường
├── .gitignore                # Loại trừ file nhạy cảm và dữ liệu sinh ra
├── config/
│   ├── settings.yml          # Cấu hình tham số hệ thống
│   └── analysis_rules.yml    # Quy tắc phân tích khóa cứng (kèm SHA-256)
├── data/
│   ├── raw/                  # Dữ liệu thô bất biến theo lần chạy (không commit)
│   ├── reference/            # Tọa độ block và cửa ga MRT
│   └── warehouse/            # Cơ sở dữ liệu DuckDB (không commit)
├── pipeline/
│   ├── extract_hdb.py        # Tải HDB resale từ data.gov.sg
│   ├── extract_mrt.py        # Tải MRT station exits GeoJSON
│   ├── extract_blocks.py     # Tra cứu bổ sung tọa độ OneMap
│   ├── load_raw.py           # Nạp snapshot vào DuckDB raw schema
│   ├── quality_gate.py       # Kiểm tra chất lượng dữ liệu trước khi publish
│   ├── publish.py            # Chuyển đổi nguyên tử sang warehouse chính thức
│   ├── run_pipeline.py       # Điều phối pipeline ELT toàn trình
│   └── common/               # Hàm dùng chung: retry, manifest, logger
├── dbt_hdb/                  # Dự án dbt-duckdb
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
├── analysis/                 # Mô hình phân tích thống kê (Q1, Q2, Q3)
├── app/                      # Streamlit dashboard
├── tests/                    # Unit tests & quality gate tests
├── docs/                     # Tài liệu tiến độ, quyết định, từ điển dữ liệu
└── report/                   # Báo cáo tổng kết dự án
```

---

## 4. Cài đặt và Chạy hệ thống

### Yêu cầu tiên quyết
- Python 3.11 hoặc 3.12 trên hệ điều hành Windows / Linux / macOS.
- Kết nối Internet trực tiếp (không sử dụng proxy / VPN).

### Các bước thực hiện

1. **Cài đặt thư viện:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Chạy pipeline toàn trình (Thủ công):**
   ```powershell
   python pipeline/run_pipeline.py
   ```
   Lệnh trên sẽ tự động:
   - Tải snapshot HDB resale mới nhất và lưu manifest.
   - Cập nhật tọa độ MRT và block.
   - Nạp dữ liệu vào `warehouse_staging.duckdb`.
   - Thực thi các mô hình transform bằng dbt (`dbt build` - 24 tests PASS).
   - Chạy các mô hình phân tích kinh tế lượng (lease curve, town gap, price index).
   - Kiểm tra ngưỡng chất lượng dữ liệu (Quality Gate - 12 blocking checks).
   - Publish nguyên tử sang `warehouse.duckdb`.

3. **Chạy kiểm thử chất lượng và hồi quy:**
   ```powershell
   pytest -v
   ```

4. **Khởi chạy Dashboard trực quan hóa:**
   ```powershell
   streamlit run app/Home.py
   ```

5. **Đăng ký Lịch chạy Tự động hằng ngày (Windows Task Scheduler):**
   ```powershell
   powershell.exe -ExecutionPolicy Bypass -File scripts/register_task.ps1
   ```
   Tác vụ `\HDB_ELT_Daily_Run` sẽ tự động kích hoạt vào lúc **08:15 AM hằng ngày**, lưu log riêng biệt theo dấu thời gian vào `logs/scheduler/run_YYYYMMDD_HHMMSS.log` và theo dõi lần chạy lỡ tại `logs/scheduler/schedule_history.json`.

---

## 5. Nguồn dữ liệu và Bản quyền

- **HDB Resale Flat Prices:** Data.gov.sg (Housing & Development Board), giấy phép Singapore Open Data Licence version 1.0.
- **LTA MRT Station Exits:** Data.gov.sg (Land Transport Authority), giấy phép Singapore Open Data Licence version 1.0.
- **NUS 3D HDB Dataset:** NUS Urban Analytics Lab (Biljecki, 2020), giấy phép MIT.
- **OneMap Search API:** Singapore Land Authority (SLA).

---

## 6. Giới hạn bắt buộc

- Dữ liệu dựa trên giao dịch mua bán đã đăng ký hoàn tất, không phản ánh toàn bộ cung/cầu thị trường.
- Khoảng cách đến MRT và CBD tính theo đường thẳng (Haversine), không phải khoảng cách đi bộ thực tế.
- Mạng lưới MRT áp dụng là mạng lưới hiện hành, không phản ánh động lịch sử mở ga mới.
- Kết quả thống kê chỉ thể hiện mối tương quan có điều kiện (conditional correlation), không hàm ý quan hệ nhân quả.
- Dự án không cung cấp khuyến nghị đầu tư hoặc định giá căn hộ cá lẻ.

