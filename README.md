# Hệ Thống Chuẩn Hóa & Bản Đồ Số GIS Biển Hiệu Cửa Hàng Quận Ninh Kiều, Cần Thơ

Chào mừng bạn đến với kho lưu trữ mã nguồn của đề tài nghiên cứu và phát triển **Hệ thống Bản đồ số Web GIS tích hợp Đồ thị Tri thức phục vụ chuẩn hóa, quản lý dữ liệu biển hiệu ocr tại quận Ninh Kiều, Cần Thơ**.

Repository này đã được tái cấu trúc sạch sẽ và khoa học để chuẩn bị cho việc đẩy lên GitHub.

---

## 📁 Cấu Trúc Thư Mục Dự Án (Repository Structure)

Dự án được chia thành 3 phân vùng lớn chính như sau:

```plaintext
d:\LuanVan\
├── Model_Training_And_Processing/  # Phân hệ Học máy & Xử lý OCR
│   ├── Application_Version_8.py     # Ứng dụng chính nhận diện & ocr biển hiệu
│   ├── tools/                       # Các công cụ chuẩn hóa thô ban đầu
│   └── utils/                       # NLP Normalizer sử dụng LLM & Từ điển
│
├── Web_GIS_App/                    # Phân hệ Ứng dụng Bản đồ Số Web GIS
│   ├── Sys/
│   │   ├── frontend/               # Frontend ReactJS + Mapbox GL GIS
│   │   └── backend/                # Backend ExpressJS + PostgreSQL/PostGIS
│
└── Graph_Visualization/             # Phân hệ Đồ thị Tri thức Độc lập (Knowledge Graph)
    ├── generate_graph.py            # Script tự động lấy dữ liệu từ DB & dựng đồ thị
    ├── signkg_graph.html            # Đồ thị tri thức biển hiệu tương tác 2D trực quan
    └── graph_documentation.md       # Tài liệu kỹ thuật chi tiết về thực thể & liên kết
```

---

## 1. Phân Hệ Học Máy & Xử Lý Biển Hiệu (`Model_Training_And_Processing`)
* **Vai trò:** Huấn luyện mô hình phát hiện chữ viết trên biển hiệu cửa hàng (OCR) và xử lý phân loại danh mục kinh doanh.
* **Chi tiết:**
  * Mô hình nhận diện hình ảnh và trích xuất thông tin biển hiệu.
  * Thư mục `utils` chứa `llm_normalizer.py` và từ điển địa danh `can_tho_dictionary.md` chịu trách nhiệm nâng cấp và sửa lỗi sai ocr tự động qua NLP.
* **Lưu ý:** Các file model nặng (`*.pt`, `*.pth`, `*.zip`) đã được đưa vào cấu hình `.gitignore` để tuân thủ giới hạn dung lượng tải lên GitHub (<100MB).

---

## 2. Ứng Dụng Bản Đồ Số Web GIS (`Web_GIS_App`)
* **Vai trò:** Ứng dụng bản đồ số tương tác đầy đủ tính năng (Full-stack Web GIS) tích hợp tất cả các nguồn dữ liệu chuẩn hóa của cửa hàng lên bản đồ không gian.
* **Các chức năng chính:**
  * Hiển thị danh sách cửa hàng định vị trên nền bản đồ Mapbox.
  * Lọc tìm kiếm theo Tên thương hiệu, Phường hành chính, Tuyến đường, và Danh mục kinh doanh.
  * Chỉ đường thông minh qua công cụ tìm đường đi ngắn nhất (Routing Engine).
  * Quản trị viên (Admin Dashboard) thêm mới, chỉnh sửa, phê duyệt dữ liệu biển hiệu.

---

## 3. Đồ Thị Tri Thức Biển Hiệu (`Graph_Visualization`)
* **Vai trò:** Biểu diễn các liên kết tri thức dạng mạng lưới đồ thị mạng xã hội liên kết đa chiều.
* **Tính năng nổi bật:**
  * Tích hợp bộ lọc dropdown địa giới phân cấp (`Quận Ninh Kiều -> Phường -> Tuyến đường`).
  * Tích hợp bộ lọc checkbox trực quan cho phép bật/tắt hiển thị từng loại thuộc tính nút (Cửa hàng, Thương hiệu, Địa chỉ, Số điện thoại, Tọa độ, Dịch vụ,...).
  * Mở trực tiếp [signkg_graph.html](Graph_Visualization/signkg_graph.html) trên trình duyệt để tương tác độc lập.

---

## 🛠️ Hướng Dẫn Cài Đặt Nhanh (Quick Start)

### 1. Khởi động Cơ sở dữ liệu PostGIS
Đảm bảo bạn đã khôi phục CSDL từ file backup `dump-gisdb-normalized.sql` vào PostgreSQL:
```bash
# Khôi phục cơ sở dữ liệu
pg_restore -h localhost -p 5433 -U myuser -d mydb dump-gisdb-normalized.sql
```

### 2. Chạy Ứng Dụng Web GIS
* **Backend:**
  ```bash
  cd Web_GIS_App/Sys/backend
  npm install
  npm run dev
  ```
* **Frontend:**
  ```bash
  cd Web_GIS_App/Sys/frontend
  npm install
  npm start
  ```

### 3. Cập nhật Đồ thị Tri thức
Nếu có sự thay đổi dữ liệu trong CSDL, chạy lại script để cập nhật đồ thị:
```bash
cd Graph_Visualization
python generate_graph.py
```
