# Hướng dẫn Cài đặt và Khởi chạy Hệ thống Web GIS

Tài liệu này hướng dẫn chi tiết cách cài đặt và triển khai hệ thống Web GIS bao gồm Backend (Django), Frontend (React) và Map Server (GeoServer).

---

## 1. Yêu cầu hệ thống
- **Hệ điều hành:** Windows, Linux hoặc MacOS.
- **Python:** Phiên bản 3.9 trở lên.
- **Node.js:** Phiên bản 18.x trở lên.
- **Docker & Docker Compose:** Để chạy Cơ sở dữ liệu PostgreSQL + PostGIS.
- **Java (JRE 8 hoặc 11):** Để chạy GeoServer.

---

## 2. Cài đặt Backend (Django)

1. **Khởi chạy Cơ sở dữ liệu (PostGIS):**
   - Mở Terminal tại thư mục `Sys/`.
   - Chạy lệnh: `docker-compose up -d db`
   - Kích hoạt PostGIS (nếu chưa có): Kết nối vào DB (cổng 5433) và chạy SQL:
     ```sql
     CREATE EXTENSION IF NOT EXISTS postgis;
     ```

2. **Cài đặt Môi trường Python:**
   - Di chuyển vào thư mục `backend/`: `cd backend`
   - Tạo môi trường ảo: `python -m venv venv`
   - Kích hoạt:
     - Linux/MacOS: `source venv/bin/activate`
     - Windows: `venv\Scripts\activate`
   - Cài đặt thư viện: `pip install -r requirements.txt`

3. **Cấu hình file `.env`:**
   - Tạo file `.env` trong thư mục `backend/` với nội dung:
     ```env
     MAPTILER_KEY=your-maptiler-key
     SECRET_KEY=your-secret-key
     DEBUG=True
     ```

4. **Thiết lập Database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Chạy Server:**
   ```bash
   python manage.py runserver
   ```

---

## 3. Cài đặt Map Server (GeoServer)

Hệ thống sử dụng GeoServer để cung cấp các lớp bản đồ OSM và ranh giới hành chính.

1. Tải GeoServer (bản Binaries) từ [geoserver.org](https://geoserver.org).
2. Giải nén và chạy `startup.sh` (Linux/Mac) hoặc `startup.bat` (Windows) trong thư mục `bin/`.
3. Truy cập `http://localhost:8080/geoserver` (User: `admin` / Pass: `geoserver`).
4. **Cấu hình:**
   - Tạo Workspace: `cantho_map`.
   - Kết nối Data Store tới Database PostGIS đã tạo ở Bước 2.
   - Publish các layer: `planet_osm_line` và `ranh_gioi_can_tho`.
   - Áp dụng Style (SLD) cho các layer để hiển thị đúng màu sắc.

---

## 4. Cài đặt Frontend (React)

1. **Cài đặt thư viện:**
   - Di chuyển vào thư mục `frontend/`: `cd frontend`
   - Chạy lệnh: `npm install`

2. **Cấu hình file `.env`:**
   - Tạo file `.env` trong thư mục `frontend/` với nội dung:
     ```env
     REACT_APP_MAPTILER_KEY=your_key_here
     REACT_APP_GEOSERVER_URL=http://localhost:8080/geoserver
     REACT_APP_API_URL=http://127.0.0.1:8000/api
     ```

3. **Chạy ứng dụng:**
   - Chạy lệnh: `npm start`
   - Truy cập: `http://localhost:3000`

---

## 5. Lưu ý
- Đảm bảo các cổng `8000` (Backend), `3000` (Frontend), `8080` (GeoServer) và `5433` (Postgres) không bị xung đột.
- Các file `test_*.py` và `test_*.js` đã được lược bỏ trong bản đóng gói này để đảm bảo dung lượng nhẹ nhất.
