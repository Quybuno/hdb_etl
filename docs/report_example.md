# Ví dụ Thực tế Minh họa (Mở đầu Báo cáo)

Tài liệu này lưu trữ câu lệnh SQL truy vấn và khóa định danh `transaction_sk` của hai căn hộ thực tế trong kho dữ liệu `fct_resale_transaction` được sử dụng làm ví dụ mở đầu cho báo cáo `report/report.md`.

> **Lưu ý phương pháp:** Đây là hai quan sát thực tế được chọn để minh họa trực quan sự khác biệt về mức giá giữa hai căn hộ có thời hạn thuê khác nhau. Đây **không phải là kết quả đã kiểm soát** bằng mô hình kinh tế lượng (vì chưa kiểm soát vị trí vi mô cụ thể, cự ly chính xác đến ga tàu hay tình trạng cải tạo nội thất của từng căn).

---

## 1. Truy vấn SQL Đối chiếu

```sql
SELECT
    transaction_sk,
    month,
    town,
    flat_type,
    block,
    street_name,
    storey_range,
    floor_area_sqm,
    remaining_lease_years,
    resale_price,
    price_per_sqm
FROM main_marts.fct_resale_transaction
WHERE transaction_sk IN (
    '6422b1795eabe983b98ee59eb120fa2b10dc0c446852ce9d5b9091f6f0255df5',
    'bff535e26da9e95120bd78044e33f306d39c7da1902da444ce0cafa0fd701d83'
);
```

---

## 2. Thông tin Chi tiết Hai Căn hộ Đối chiếu

| Thuộc tính | Căn hộ 1 (Thuê ngắn) | Căn hộ 2 (Thuê dài) |
|---|---|---|
| **transaction_sk** | `6422b1795eabe983b98ee59eb120fa2b10dc0c446852ce9d5b9091f6f0255df5` | `bff535e26da9e95120bd78044e33f306d39c7da1902da444ce0cafa0fd701d83` |
| **Tháng giao dịch** | 2024-07 | 2024-07 |
| **Khu vực (Town)** | QUEENSTOWN | QUEENSTOWN |
| **Loại căn hộ** | 3 ROOM | 3 ROOM |
| **Vị trí Block** | Block 95, C'WEALTH DR | Block 89, TANGLIN HALT RD |
| **Khoảng tầng** | 04 TO 06 | 04 TO 06 |
| **Diện tích sàn** | 60.0 m² | 60.0 m² |
| **Thời hạn thuê còn lại** | **41 năm 7 tháng (41.58 năm)** | **83 năm 2 tháng (83.17 năm)** |
| **Giá bán lại (SGD)** | **322,000 SGD** | **592,000 SGD** |
| **Đơn giá trên m²** | **5,366.67 SGD/m²** | **9,866.67 SGD/m²** |
| **Chênh lệch đơn giá** | *Cơ sở tham chiếu* | **+83.85% (+4,500.00 SGD/m²)** |

---

## 3. Nhận xét Minh họa
Trong cùng tháng **07/2024**, tại cùng khu vực **QUEENSTOWN**, hai căn hộ cùng loại **3 ROOM**, cùng diện tích sàn **60.0 m²** và cùng nằm trong khoảng tầng **04 TO 06** ghi nhận giá giao dịch chênh lệch 270,000 SGD (+83.85% đơn giá trên mỗi mét vuông). Sự chênh lệch này gắn liền với khoảng cách thời hạn thuê lên tới 41.58 năm giữa hai khối nhà.

