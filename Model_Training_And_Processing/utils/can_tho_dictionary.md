# Từ điển Chuẩn hóa Địa chỉ Cần Thơ (Can Tho Address Dictionary)

Tài liệu này cung cấp danh sách chuẩn các Quận/Huyện, Phường/Xã, Tên đường và danh sách viết tắt phổ biến tại Thành phố Cần Thơ để làm tài liệu tham khảo (Knowledge Base) cho mô hình LLM khi chuẩn hóa địa chỉ.

---

## 1. Danh sách Quận / Huyện (Districts) tại Cần Thơ
- Quận Ninh Kiều
- Quận Bình Thủy
- Quận Cái Răng
- Quận Ô Môn
- Quận Thốt Nốt
- Huyện Phong Điền
- Huyện Cờ Đỏ
- Huyện Thới Lai
- Huyện Vĩnh Thạnh

---

## 2. Danh sách Phường / Xã phổ biến (Wards)
### Quận Ninh Kiều:
- Phường An Khánh
- Phường An Hòa
- Phường An Nghiệp
- Phường An Phú
- Phường An Hội
- Phường An Lạc
- Phường Cái Khế
- Phường Hưng Lợi
- Phường Tân An
- Phường Thới Bình
- Phường Xuân Khánh

### Quận Bình Thủy:
- Phường Bình Thủy
- Phường An Thới
- Phường Trà An
- Phường Trà Nóc
- Phường Bùi Hữu Nghĩa
- Phường Long Tuyền
- Phường Long Hòa
- Phường Thới An Đông

### Quận Cái Răng:
- Phường Lê Bình
- Phường Hưng Phú
- Phường Hưng Thạnh
- Phường Ba Láng
- Phường Thường Thạnh
- Phường Phú Thứ
- Phường Tân Phú

---

## 3. Danh sách Tên đường chính phổ biến (Streets)
- Nguyễn Văn Cừ
- Nguyễn Văn Cừ Nối Dài
- Mậu Thân
- Đường 3 Tháng 2 (3/2, Ba Tháng Hai)
- Đường 30 Tháng 4 (30/4, Ba Mươi Tháng Tư)
- Nguyễn Văn Linh
- Cách Mạng Tháng Tám (Cách Mạng Tháng 8, CMT8)
- Trần Hưng Đạo
- Hùng Vương
- Đại lộ Hòa Bình (Hòa Bình)
- Trần Văn Hoài
- Đề Thám
- Lý Tự Trọng
- Võ Văn Kiệt
- Nguyễn Trãi
- Hai Bà Trưng
- Trần Văn Khéo
- Đồng Khởi
- Ngô Quyền
- Xô Viết Nghệ Tĩnh
- Đinh Tiên Hoàng
- Nguyễn An Ninh
- Châu Văn Liêm
- Quang Trung
- Trần Hoàng Na
- Nguyễn Việt Hồng
- Lý Thường Kiệt
- Phan Đình Phùng
- 30 Tháng 4
- 3 Tháng 2
- Nguyễn Văn Cử -> SỬA THÀNH: Nguyễn Văn Cừ
- Nguyễn Văn Cự -> SỬA THÀNH: Nguyễn Văn Cừ

---

## 4. Quy tắc ánh xạ viết tắt và lỗi chính tả phổ biến (Mapping Rules)
Dưới đây là các từ viết tắt/lỗi OCR bắt buộc phải chuyển sang từ chuẩn có dấu:

| Từ gốc / Viết tắt (Input) | Từ chuẩn hóa (Output) | Loại |
| :--- | :--- | :--- |
| `nvc`, `NVC`, `nguyen van cu`, `văn cử`, `văn cự` | **Nguyễn Văn Cừ** | Đường |
| `cmt8`, `CMT8`, `cach mang thang 8` | **Cách Mạng Tháng Tám** | Đường |
| `3/2`, `3 tháng 2`, `ba thang hai` | **Đường 3 Tháng 2** | Đường |
| `30/4`, `30 tháng 4`, `ba muoi thang tu` | **Đường 30 Tháng 4** | Đường |
| `nvl`, `NVL`, `nguyen van linh` | **Nguyễn Văn Linh** | Đường |
| `nk`, `NK`, `ninh kieu` | **Ninh Kiều** | Quận |
| `tpct`, `TPCT`, `can tho`, `ct` | **Thành phố Cần Thơ** | Thành phố |
| `p.ak`, `pak`, `an khanh` | **Phường An Khánh** | Phường |
| `p.xk`, `pxk`, `xuan khanh` | **Phường Xuân Khánh** | Phường |
| `p.hl`, `phl`, `hung loi` | **Phường Hưng Lợi** | Phường |
| `p.ah`, `pah`, `an hoa` | **Phường An Hòa** | Phường |
| `p.ck`, `pck`, `cai khe` | **Phường Cái Khế** | Phường |
| `p.ta`, `pta`, `tan an` | **Phường Tân An** | Phường |
| `p.tb`, `ptb`, `thoi binh` | **Phường Thới Bình** | Phường |
| `p.an`, `pan`, `an nghiep` | **Phường An Nghiệp** | Phường |
| `p.ap`, `pap`, `an phu` | **Phường An Phú** | Phường |
| `p.th`, `pth`, `thoi binh` | **Phường Thới Bình** | Phường |
| `nd`, `ND`, `noi dai` | **Nối Dài** | Hậu tố đường |
| `tphcm`, `tp.hcm`, `hcm` | **Thành phố Hồ Chí Minh** | Thành phố |
