import random
import pandas as pd
import unidecode
import re

# ==============================================================================
# 1. SIÊU TỪ ĐIỂN TỪ KHÓA (GIỮ NGUYÊN BỘ 100 TỪ/NHÓM)
# ==============================================================================
KEYWORDS = {
    "Ẩm Thực": [
        "Quán Cơm", "Cơm Tấm", "Cơm Niêu", "Cơm Văn Phòng", "Cơm Gà", "Cơm Chay", "Cơm Bình Dân", "Cơm Phần",
        "Phở", "Phở Bò", "Phở Gà", "Phở Gia Truyền", "Phở Tái Nạm", "Phở Cuốn", "Phở Trộn",
        "Bún Bò", "Bún Bò Huế", "Bún Riêu", "Bún Riêu Cua", "Bún Mắm", "Bún Thái", "Bún Chả", "Bún Thịt Nướng", "Bún Đậu Mắm Tôm",
        "Hủ Tiếu", "Hủ Tiếu Nam Vang", "Hủ Tiếu Gõ", "Hủ Tiếu Mực", "Hủ Tiếu Xương", "Mì Quảng", "Mì Cay", "Mì Vịt Tiềm",
        "Bánh Canh", "Bánh Canh Ghẹ", "Bánh Canh Cá Lóc", "Nui Xào", "Miến Gà", "Miến Lươn",
        "Lẩu", "Lẩu Nướng", "Lẩu Dê", "Lẩu Bò", "Lẩu Mắm", "Lẩu Cá", "Lẩu Thái", "Lẩu Cua Đồng",
        "Buffet", "BBQ", "Nướng Không Khói", "Xiên Que", "Nướng Ngói", "Bò Né", "Bò Kho",
        "Nhà Hàng", "Quán Ăn", "Quán Nhậu", "Bia Hơi", "Mồi Bén", "Hải Sản", "Ốc Đêm", "Cua Cà Mau",
        "Bánh Mì", "Bánh Mì Thổ Nhĩ Kỳ", "Bánh Mì Chảo", "Xôi", "Xôi Gà", "Bánh Bao", "Bánh Cuốn", "Bánh Xèo", "Bánh Khọt",
        "Vịt Quay", "Heo Quay", "Gà Nướng", "Gà Rán", "Cháo Ếch", "Cháo Lòng", "Nem Nướng", "Bít Tết", "Pizza", "Sushi", "Kimbap"
    ],
    "Đồ Uống": [
        "Cà Phê", "Cafe", "Coffee", "Kafe", "Cà Phê Mang Đi", "Cafe Võng", "Cafe Sân Vườn", "Cafe Máy lạnh", "Cafe Cóc",
        "Cà Phê Rang Xay", "Espresso", "Capuchino", "Latte", "Macchiato", "Bạc Xỉu", "Cà Phê Trứng",
        "Trà Sữa", "Milk Tea", "Trà Sữa Trân Châu", "Trà Chanh", "Trà Đào", "Trà Tắc", "Hồng Trà", "Lục Trà", "Trà Oolong",
        "Sinh Tố", "Nước Ép", "Rau Má", "Rau Má Đậu Xanh", "Sữa Đậu Nành", "Nước Mía", "Dừa Tắc", "Sâm Bí Đao", "Nước Mát",
        "Chè", "Chè Thái", "Chè Bưởi", "Tàu Hủ", "Tàu Hủ Đá", "Sữa Chua", "Sữa Chua Trân Châu", "Kem", "Kem Tự Chọn",
        "Quán Bar", "Pub", "Lounge", "Beer Club", "Cocktail", "Wine", "Hầm Rượu", "Bia Craft"
    ],
    "Xe Cộ & Phương Tiện": [
        "Showroom", "Salon Auto", "Đại Lý Xe", "Cửa Hàng Xe Máy", "Mua Bán Xe", "Xe Máy Cũ", "Xe Lướt", "Trao Đổi Xe",
        "Xe Điện", "Xe Đạp Điện", "Xe Đạp", "Xe Đạp Thể Thao", "Motor", "Moto Phân Khối Lớn", "Vespa",
        "Honda", "Yamaha", "Suzuki", "Piaggio", "Sym", "VinFast", "Toyota", "Hyundai", "Kia", "Ford", "Mazda",
        "Head Honda", "Town", "3S", "Kymco", "Ducati", "Kawasaki",
        "Sửa Xe", "Tiệm Sửa Xe", "Sửa Xe Tay Ga", "Chuyên Sửa Honda", "Cứu Hộ Xe Máy",
        "Rửa Xe", "Rửa Xe Bọt Tuyết", "Chăm Sóc Xe", "Detailing", "Phủ Ceramic", "Đánh Bóng",
        "Gara", "Garage", "Auto", "Đồng Sơn", "Sơn Xe", "Dán Keo Xe", "Dán Decal", "Độ Xe",
        "Phụ Tùng", "Đồ Chơi Xe", "Phụ Kiện Ô Tô", "Nội Thất Ô Tô", "Camera Hành Trình",
        "Thay Nhớt", "Castrol", "Motul", "Vá Vỏ", "Lốp Xe", "Vỏ Xe", "Michelin", "Bình Ắc Quy", "Mũ Bảo Hiểm", "Bãi Giữ Xe"
    ],
    "Mua Sắm": [
        "Shop Quần Áo", "Thời Trang", "Fashion", "Boutique", "Shop Nam", "Shop Nữ", "Đồ Trẻ Em", "Mẹ và Bé",
        "Giày Dép", "Sneaker", "Giày Da", "Giày Cao Gót", "Dép Lào", "Sandal",
        "Túi Xách", "Ba Lô", "Vali", "Bóp Da", "Ví Da", "Thắt Lưng", "Dây Nịt",
        "Đồ Lót", "Nội Y", "Đồ Ngủ", "Đồ Bộ", "Đồ Thể Thao", "Sport", "Vest", "Áo Dài", "May Đo", "Nhà May",
        "Mỹ Phẩm", "Cosmetics", "Nước Hoa", "Perfume", "Son Môi", "Kem Dưỡng Da", "Tinh Dầu",
        "Trang Sức", "Vàng Bạc", "Đá Quý", "Tiệm Vàng", "Cầm Đồ", "Kim Hoàn", "Nữ Trang", "Nhẫn Cưới",
        "Đồng Hồ", "Kính Mắt", "Mắt Kính", "Gọng Kính", "Shop Hoa", "Hoa Tươi", "Quà Lưu Niệm", "Gấu Bông"
    ],
    "Công Nghệ & Điện Máy": [
        "Điện Thoại", "Mobile", "Smartphone", "Di Động", "iPhone", "Samsung", "Oppo", "Xiaomi", "Apple Store",
        "Laptop", "Máy Tính", "PC", "Computer", "Macbook", "Dell", "HP", "Asus", "Gaming Gear",
        "Sửa Chữa Laptop", "Sửa Điện Thoại", "Ép Kính", "Thay Màn Hình", "Thay Pin", "Cài Win", "Unlock", "Mở Khóa iCloud",
        "Camera", "Máy Ảnh", "Camera Quan Sát", "Camera Hành Trình", "Lắp Đặt Camera",
        "Phụ Kiện Điện Thoại", "Ốp Lưng", "Cường Lực", "Tai Nghe", "Loa Bluetooth", "Sạc Dự Phòng",
        "Sim Số Đẹp", "Thẻ Cào", "Linh Kiện Điện Tử", "Bo Mạch", "Ram", "SSD",
        "Điện Máy", "Điện Lạnh", "Máy Lạnh", "Máy Giặt", "Tivi", "Tủ Lạnh", "Máy Lọc Nước", "Robot Hút Bụi",
        "Điện Gia Dụng", "Nồi Cơm Điện", "Bếp Từ", "Lò Vi Sóng"
    ],
    "Siêu Thị & Tạp Hóa": [
        "Chợ", "Siêu Thị", "Supermarket", "Mart", "Mini Mart", "Cửa Hàng Tiện Lợi", "Store", "FamilyMart", "Circle K",
        "Bách Hóa", "Tạp Hóa", "Cửa Hàng Tự Chọn", "WinMart", "Co.op Food", "Bách Hóa Xanh",
        "Vựa Trái Cây", "Trái Cây Nhập Khẩu", "Hoa Quả Sạch", "Sầu Riêng", "Dừa Xiêm",
        "Vựa Gạo", "Đại Lý Gạo", "Nước Suối", "Đổi Nước", "Gas", "Đổi Gas",
        "Hải Sản Tươi Sống", "Thực Phẩm Sạch", "Thực Phẩm Đông Lạnh", "Thịt Heo", "Thịt Bò", "Trứng Gà", "Gia Vị", "Sữa Bỉm"
    ],
    "Y Tế & Sức Khỏe": [
        "Bệnh Viện", "Đa Khoa", "Phòng Khám", "Bác Sĩ", "Y Tế", "Trạm Y Tế", "Trung Tâm Y Tế",
        "Nha Khoa", "Răng Hàm Mặt", "Niềng Răng", "Trồng Răng Implant", "Tẩy Trắng Răng",
        "Nhà Thuốc", "Quầy Thuốc", "Dược Phẩm", "Pharmacy", "Thuốc Tây", "Hiệu Thuốc",
        "Đông Y", "Y Học Cổ Truyền", "Châm Cứu", "Bấm Huyệt", "Vật Lý Trị Liệu", "Phục Hồi Chức Năng",
        "Massage Người Mù", "Massage Trị Liệu", "Xông Hơi Thuốc Bắc",
        "Xét Nghiệm", "Tiêm Chủng", "Vắc Xin", "Siêu Âm", "X-Quang",
        "Mắt Kính Thuốc", "Đo Mắt", "Kính Cận", "Tai Mũi Họng", "Da Liễu", "Sản Phụ Khoa", "Nhi Khoa"
    ],
    "Làm Đẹp & Spa": [
        "Spa", "Thẩm Mỹ Viện", "Beauty", "Clinic", "Skin Care", "Chăm Sóc Da", "Trị Mụn", "Tắm Trắng", "Triệt Lông",
        "Nail", "Tiệm Nail", "Móng Tay", "Sơn Gel", "Vẽ Móng", "Nối Mi", "Phun Xăm", "Điêu Khắc Chân Mày", "Phun Môi",
        "Salon Tóc", "Hair Salon", "Viện Tóc", "Gội Đầu", "Cắt Tóc", "Barber", "Hớt Tóc Nam", "Uốn Duỗi Nhuộm", "Phục Hồi Tóc",
        "Gội Đầu Dưỡng Sinh", "Tattoo", "Xăm Hình Nghệ Thuật", "Xỏ Khuyên"
    ],
    "Giáo Dục": [
        "Trường Đại Học", "Học Viện", "Cao Đẳng", "Trung Cấp", "Trường Nghề", "Đại Học Cần Thơ", "FPT",
        "Trường THPT", "Trường THCS", "Trường Tiểu Học", "Trường Mầm Non", "Nhà Trẻ", "Mẫu Giáo",
        "Trung Tâm Anh Ngữ", "Tiếng Anh", "Ngoại Ngữ", "Tin Học", "IELTS", "TOEIC", "Anh Văn Giao Tiếp",
        "Gia Sư", "Luyện Thi", "Dạy Thêm", "Toán Lý Hóa",
        "Dạy Nghề", "Đào Tạo Lái Xe", "Dạy Nhạc", "Piano", "Guitar", "Dạy Vẽ", "Mỹ Thuật",
        "Nhà Sách", "Văn Phòng Phẩm", "Photocopy", "In Ấn", "Thư Viện", "Sách Giáo Khoa"
    ],
    "Lưu Trú": [
        "Khách Sạn", "Hotel", "Nhà Nghỉ", "Motel", "Homestay", "Hostel", "Dorm",
        "Resort", "Khu Nghỉ Dưỡng", "Villa", "Biệt Thự", "Bungalow",
        "Nhà Trọ", "Phòng Trọ", "Cho Thuê Phòng", "Ký Túc Xá", "Sleepbox", "Căn Hộ Dịch Vụ", "Apartment"
    ],
    "Giải Trí": [
        "Karaoke", "KTV", "Hát Với Nhau", "Phòng Thu Âm",
        "Bida", "Billiards", "CLB Bida", "Bi A", "Bida Phăng", "Bida Lỗ",
        "Internet", "Cyber Game", "Tiệm Net", "Gaming House", "eSports",
        "Rạp Phim", "Cinema", "Khu Vui Chơi", "Nhà Thiếu Nhi", "Thú Nhún", "Nhà Banh",
        "Câu Cá", "Hồ Câu", "Bắn Cá",
        "Phòng Gym", "Fitness", "Yoga", "Aerobic", "Zumba", "Pilates",
        "Sân Bóng Đá", "Sân Cỏ Nhân Tạo", "Hồ Bơi", "Tennis", "Cầu Lông"
    ],
    "Vận Tải & Kho Bãi": [
        "Bến Xe", "Nhà Xe", "Trạm Xe Buýt", "Bus Station", "Điểm Đón Trả Khách",
        "Chành Xe", "Vận Tải", "Chở Hàng", "Ba Gác", "Xe Tải", "Chuyển Nhà", "Dọn Nhà",
        "Chuyển Phát Nhanh", "Logistics", "Express", "Giao Hàng", "Ship Hàng", "Bưu Cục", "Bưu Điện", "Viettel Post", "VNPost",
        "Phòng Vé Máy Bay", "Vé Tàu", "Đại Lý Vé", "Booking", "Visa"
    ],
    "Xây Dựng & Nội Thất": [
        "Vật Liệu Xây Dựng", "VLXD", "Cửa Hàng Sơn", "Gạch Men", "Xi Măng", "Sắt Thép", "Tôn Hoa Sen", "Cát Đá",
        "Nhôm Kính", "Cửa Cuốn", "Thạch Cao", "Trần Nhựa", "Inox", "Cơ Khí", "Hàn Tiện",
        "Nội Thất", "Trang Trí", "Rèm Cửa", "Đèn Trang Trí", "Sàn Gỗ", "Giấy Dán Tường",
        "Điện Nước", "Ống Nước", "Dây Điện", "Thiết Bị Vệ Sinh", "Bồn Cầu", "Lavabo",
        "Đồ Gia Dụng", "Khóa Cửa", "Kính Cường Lực", "Mái Hiên", "Bạt Che"
    ],
    "Hành Chính & Công Cộng": [
        "Ủy Ban Nhân Dân", "UBND", "Hội Đồng Nhân Dân", "HĐND", "Đảng Ủy",
        "Công An", "Trụ Sở", "Cảnh Sát", "PCCC", "CSGT", "Chốt Dân Phòng",
        "Tòa Án", "Viện Kiểm Sát", "Thi Hành Án",
        "Kho Bạc", "Bảo Hiểm Xã Hội", "Sở Giao Thông", "Sở Tài Nguyên", "Sở Xây Dựng",
        "Nhà Văn Hóa", "Trung Tâm Hành Chính", "Đài Truyền Hình", "Bưu Điện Tỉnh"
    ],
    "Tài Chính & Doanh Nghiệp": [
        "Ngân Hàng", "Bank", "ATM", "Phòng Giao Dịch", "Tín Dụng",
        "Vietcombank", "Agribank", "BIDV", "Techcombank", "VietinBank", "MB Bank", "ACB", "VPBank", "TPBank",
        "Sacombank", "Kienlongbank", "MSB", "OceanBank", "SeABank", "DongA Bank", "LienVietPostBank",
        "PGBank", "SaigonBank", "IVB", "HDBank", "NaviBank", "EximBank", "Vietbank", "BacABank",
        "Cầm Đồ", "Tài Chính", "Cho Vay", "Đáo Hạn", "Hỗ Trợ Vốn",
        "Công Ty", "Company", "Văn Phòng", "Office", "Chi Nhánh", "Trụ Sở Chính", "Đại Diện", "TNHH", "Cổ Phần",
        "Luật Sư", "Công Chứng", "Thừa Phát Lại", "Kế Toán", "Kiểm Toán",
        "Bất Động Sản", "Nhà Đất", "Môi Giới", "Ký Gửi", "Địa Ốc", "Dự Án"
    ],
    "Tôn Giáo": [
        "Chùa", "Tịnh Xá", "Thiền Viện", "Tu Viện", "Niệm Phật Đường",
        "Nhà Thờ", "Giáo Xứ", "Công Giáo", "Tin Lành", "Dòng Tu",
        "Đình Thần", "Miếu", "Thánh Thất", "Cao Đài", "Lăng Ông",
        "Phật Giáo", "Hòa Hảo", "Ban Trị Sự", "Hội Thánh"
    ],
    "Nông Nghiệp & Thú Y": [
        "Phân Bón", "Thuốc Trừ Sâu", "Bảo Vệ Thực Vật", "Đạm Phú Mỹ", "NPK",
        "Hạt Giống", "Cây Giống", "Vườn Ươm", "Hoa Kiểng", "Cây Cảnh", "Lan Rừng", "Bonsai",
        "Vật Tư Nông Nghiệp", "Máy Nông Nghiệp", "Máy Cày", "Hệ Thống Tưới",
        "Thú Y", "Pet Shop", "Phòng Khám Thú Y", "Thức Ăn Chăn Nuôi", "Cám Con Cò", "Thuốc Thú Y", "Chó Mèo", "Cá Cảnh"
    ]
}

# ==============================================================================
# 1. CẤU HÌNH DỮ LIỆU THEO NGỮ CẢNH (CONTEXT CONFIG)
# ==============================================================================
# Mỗi danh mục có bộ Tiền tố (Pre) và Hậu tố (Suf) riêng biệt
DATA_CONFIG = {
    "Ẩm Thực": {
        "keywords": [
        "Quán Cơm", "Cơm Tấm", "Cơm Niêu", "Cơm Văn Phòng", "Cơm Gà", "Cơm Chay", "Cơm Bình Dân", "Cơm Phần",
        "Phở", "Phở Bò", "Phở Gà", "Phở Gia Truyền", "Phở Tái Nạm", "Phở Cuốn", "Phở Trộn",
        "Bún Bò", "Bún Bò Huế", "Bún Riêu", "Bún Riêu Cua", "Bún Mắm", "Bún Thái", "Bún Chả", "Bún Thịt Nướng", "Bún Đậu Mắm Tôm",
        "Hủ Tiếu", "Hủ Tiếu Nam Vang", "Hủ Tiếu Gõ", "Hủ Tiếu Mực", "Hủ Tiếu Xương", "Mì Quảng", "Mì Cay", "Mì Vịt Tiềm",
        "Bánh Canh", "Bánh Canh Ghẹ", "Bánh Canh Cá Lóc", "Nui Xào", "Miến Gà", "Miến Lươn",
        "Lẩu", "Lẩu Nướng", "Lẩu Dê", "Lẩu Bò", "Lẩu Mắm", "Lẩu Cá", "Lẩu Thái", "Lẩu Cua Đồng",
        "Buffet", "BBQ", "Nướng Không Khói", "Xiên Que", "Nướng Ngói", "Bò Né", "Bò Kho",
        "Nhà Hàng", "Quán Ăn", "Quán Nhậu", "Bia Hơi", "Mồi Bén", "Hải Sản", "Ốc Đêm", "Cua Cà Mau",
        "Bánh Mì", "Bánh Mì Thổ Nhĩ Kỳ", "Bánh Mì Chảo", "Xôi", "Xôi Gà", "Bánh Bao", "Bánh Cuốn", "Bánh Xèo", "Bánh Khọt",
        "Vịt Quay", "Heo Quay", "Gà Nướng", "Gà Rán", "Cháo Ếch", "Cháo Lòng", "Nem Nướng", "Bít Tết", "Pizza", "Sushi", "Kimbap"
    ],
        "prefixes": ["Quán", "Tiệm", "Nhà Hàng", "Bếp", "Tiệm Ăn", "Làng Nướng", "Vườn", "Ẩm Thực", "Hệ Thống", "Thế Giới", "Vua", "Lò"],
        "suffixes": ["Gia Truyền", "Bình Dân", "Ngon", "Sài Gòn", "Hà Nội", "Huế", "Gốc Hoa", "Đặc Biệt", "Đêm", "Vỉa Hè", "Máy Lạnh", "Sân Vườn", "Bờ Kè"]
    },
    "Đồ Uống": {
        "keywords": [
        "Cà Phê", "Cafe", "Coffee", "Kafe", "Cà Phê Mang Đi", "Cafe Võng", "Cafe Sân Vườn", "Cafe Máy lạnh", "Cafe Cóc",
        "Cà Phê Rang Xay", "Espresso", "Capuchino", "Latte", "Macchiato", "Bạc Xỉu", "Cà Phê Trứng",
        "Trà Sữa", "Milk Tea", "Trà Sữa Trân Châu", "Trà Chanh", "Trà Đào", "Trà Tắc", "Hồng Trà", "Lục Trà", "Trà Oolong",
        "Sinh Tố", "Nước Ép", "Rau Má", "Rau Má Đậu Xanh", "Sữa Đậu Nành", "Nước Mía", "Dừa Tắc", "Sâm Bí Đao", "Nước Mát",
        "Chè", "Chè Thái", "Chè Bưởi", "Tàu Hủ", "Tàu Hủ Đá", "Sữa Chua", "Sữa Chua Trân Châu", "Kem", "Kem Tự Chọn",
        "Quán Bar", "Pub", "Lounge", "Beer Club", "Cocktail", "Wine", "Hầm Rượu", "Bia Craft"
    ],
        "prefixes": ["Tiệm", "Quán", "Hệ Thống", "Xe", "Quầy", "The", "Mr.", "Mrs.", "Tiệm Trà", "Vườn"],
        "suffixes": ["Mang Đi", "Take Away", "Rang Xay", "Nguyên Chất", "Nhà Làm", "Handmade", "Võng", "Sân Vườn", "Acoustic", "Rooftop", "Chill", "24h"]
    },
    "Xe Cộ & Phương Tiện": {
        "keywords": [
        "Showroom", "Salon Auto", "Đại Lý Xe", "Cửa Hàng Xe Máy", "Mua Bán Xe", "Xe Máy Cũ", "Xe Lướt", "Trao Đổi Xe",
        "Xe Điện", "Xe Đạp Điện", "Xe Đạp", "Xe Đạp Thể Thao", "Motor", "Moto Phân Khối Lớn", "Vespa",
        "Honda", "Yamaha", "Suzuki", "Piaggio", "Sym", "VinFast", "Toyota", "Hyundai", "Kia", "Ford", "Mazda",
        "Head Honda", "Town", "3S", "Kymco", "Ducati", "Kawasaki",
        "Sửa Xe", "Tiệm Sửa Xe", "Sửa Xe Tay Ga", "Chuyên Sửa Honda", "Cứu Hộ Xe Máy",
        "Rửa Xe", "Rửa Xe Bọt Tuyết", "Chăm Sóc Xe", "Detailing", "Phủ Ceramic", "Đánh Bóng",
        "Gara", "Garage", "Auto", "Đồng Sơn", "Sơn Xe", "Dán Keo Xe", "Dán Decal", "Độ Xe",
        "Phụ Tùng", "Đồ Chơi Xe", "Phụ Kiện Ô Tô", "Nội Thất Ô Tô", "Camera Hành Trình",
        "Thay Nhớt", "Castrol", "Motul", "Vá Vỏ", "Lốp Xe", "Vỏ Xe", "Michelin", "Bình Ắc Quy", "Mũ Bảo Hiểm", "Bãi Giữ Xe"
    ],
        "prefixes": ["Cửa Hàng", "Showroom", "Salon", "Trung Tâm", "Đại Lý", "Head", "Tiệm", "Xưởng", "Garage", "Auto", "Thế Giới", "Siêu Thị"],
        "suffixes": ["Chính Hãng", "Uy Tín", "Chuyên Nghiệp", "Giá Rẻ", "Trả Góp", "Cũ Mới", "Nhập Khẩu", "3S", "4S", "Detailing", "Bọt Tuyết"]
    },
    "Mua Sắm": {
        "keywords": [
        "Shop Quần Áo", "Thời Trang", "Fashion", "Boutique", "Shop Nam", "Shop Nữ", "Đồ Trẻ Em", "Mẹ và Bé",
        "Giày Dép", "Sneaker", "Giày Da", "Giày Cao Gót", "Dép Lào", "Sandal",
        "Túi Xách", "Ba Lô", "Vali", "Bóp Da", "Ví Da", "Thắt Lưng", "Dây Nịt",
        "Đồ Lót", "Nội Y", "Đồ Ngủ", "Đồ Bộ", "Đồ Thể Thao", "Sport", "Vest", "Áo Dài", "May Đo", "Nhà May",
        "Mỹ Phẩm", "Cosmetics", "Nước Hoa", "Perfume", "Son Môi", "Kem Dưỡng Da", "Tinh Dầu",
        "Trang Sức", "Vàng Bạc", "Đá Quý", "Tiệm Vàng", "Cầm Đồ", "Kim Hoàn", "Nữ Trang", "Nhẫn Cưới",
        "Đồng Hồ", "Kính Mắt", "Mắt Kính", "Gọng Kính", "Shop Hoa", "Hoa Tươi", "Quà Lưu Niệm", "Gấu Bông"
    ],
        "prefixes": ["Shop", "Cửa Hàng", "Tiệm", "Boutique", "Store", "Tổng Kho", "Xưởng", "Thế Giới", "Siêu Thị", "Vương Quốc"],
        "suffixes": ["Nam Nữ", "Trẻ Em", "Xuất Khẩu", "Quảng Châu", "Thiết Kế", "Cao Cấp", "Authentic", "Xách Tay", "Chính Hãng", "Hàn Quốc"]
    },
    "Công Nghệ & Điện Máy": {
        "keywords": [
        "Điện Thoại", "Mobile", "Smartphone", "Di Động", "iPhone", "Samsung", "Oppo", "Xiaomi", "Apple Store",
        "Laptop", "Máy Tính", "PC", "Computer", "Macbook", "Dell", "HP", "Asus", "Gaming Gear",
        "Sửa Chữa Laptop", "Sửa Điện Thoại", "Ép Kính", "Thay Màn Hình", "Thay Pin", "Cài Win", "Unlock", "Mở Khóa iCloud",
        "Camera", "Máy Ảnh", "Camera Quan Sát", "Camera Hành Trình", "Lắp Đặt Camera",
        "Phụ Kiện Điện Thoại", "Ốp Lưng", "Cường Lực", "Tai Nghe", "Loa Bluetooth", "Sạc Dự Phòng",
        "Sim Số Đẹp", "Thẻ Cào", "Linh Kiện Điện Tử", "Bo Mạch", "Ram", "SSD",
        "Điện Máy", "Điện Lạnh", "Máy Lạnh", "Máy Giặt", "Tivi", "Tủ Lạnh", "Máy Lọc Nước", "Robot Hút Bụi",
        "Điện Gia Dụng", "Nồi Cơm Điện", "Bếp Từ", "Lò Vi Sóng"
    ],
        "prefixes": ["Cửa Hàng", "Trung Tâm", "Siêu Thị", "Thế Giới", "Shop", "Store", "Điện Máy", "Viễn Thông", "Kỹ Thuật", "Bệnh Viện"],
        "suffixes": ["Chính Hãng", "Giá Kho", "Trả Góp 0%", "Xách Tay", "Lock", "Quốc Tế", "Cũ Giá Rẻ", "Lấy Liền", "Uy Tín"]
    },
    "Siêu Thị & Tạp Hóa": {
        "keywords": [
        "Chợ", "Siêu Thị", "Supermarket", "Mart", "Mini Mart", "Cửa Hàng Tiện Lợi", "Store", "FamilyMart", "Circle K",
        "Bách Hóa", "Tạp Hóa", "Cửa Hàng Tự Chọn", "WinMart", "Co.op Food", "Bách Hóa Xanh",
        "Vựa Trái Cây", "Trái Cây Nhập Khẩu", "Hoa Quả Sạch", "Sầu Riêng", "Dừa Xiêm",
        "Vựa Gạo", "Đại Lý Gạo", "Nước Suối", "Đổi Nước", "Gas", "Đổi Gas",
        "Hải Sản Tươi Sống", "Thực Phẩm Sạch", "Thực Phẩm Đông Lạnh", "Thịt Heo", "Thịt Bò", "Trứng Gà", "Gia Vị", "Sữa Bỉm"
        ],
        "prefixes": ["Cửa Hàng", "Tiệm", "Vựa", "Đại Lý", "Kho", "Siêu Thị", "Ki Ốt", "Sạp", "Quầy"],
        "suffixes": ["Tiện Lợi", "Tự Chọn", "Sạch", "Tươi Sống", "Nhập Khẩu", "Miền Tây", "Thái Lan", "Giao Tận Nơi"]
    },
    "Y Tế & Sức Khỏe": {
        "keywords": [
        "Bệnh Viện", "Đa Khoa", "Phòng Khám", "Bác Sĩ", "Y Tế", "Trạm Y Tế", "Trung Tâm Y Tế",
        "Nha Khoa", "Răng Hàm Mặt", "Niềng Răng", "Trồng Răng Implant", "Tẩy Trắng Răng",
        "Nhà Thuốc", "Quầy Thuốc", "Dược Phẩm", "Pharmacy", "Thuốc Tây", "Hiệu Thuốc",
        "Đông Y", "Y Học Cổ Truyền", "Châm Cứu", "Bấm Huyệt", "Vật Lý Trị Liệu", "Phục Hồi Chức Năng",
        "Massage Người Mù", "Massage Trị Liệu", "Xông Hơi Thuốc Bắc",
        "Xét Nghiệm", "Tiêm Chủng", "Vắc Xin", "Siêu Âm", "X-Quang",
        "Mắt Kính Thuốc", "Đo Mắt", "Kính Cận", "Tai Mũi Họng", "Da Liễu", "Sản Phụ Khoa", "Nhi Khoa"
    ],
        "prefixes": ["Trung Tâm", "Viện", "Bác Sĩ", "Lương Y", "Nhà Thuốc", "Quầy Thuốc", "Hiệu Thuốc", "Phòng Chẩn Trị"],
        "suffixes": ["Đa Khoa", "Quốc Tế", "Sài Gòn", "Gia Truyền", "Trung Ương", "Chất Lượng Cao", "Người Mù", "24/7"]
    },
    "Làm Đẹp & Spa": {
        "keywords": [
        "Spa", "Thẩm Mỹ Viện", "Beauty", "Clinic", "Skin Care", "Chăm Sóc Da", "Trị Mụn", "Tắm Trắng", "Triệt Lông",
        "Nail", "Tiệm Nail", "Móng Tay", "Sơn Gel", "Vẽ Móng", "Nối Mi", "Phun Xăm", "Điêu Khắc Chân Mày", "Phun Môi",
        "Salon Tóc", "Hair Salon", "Viện Tóc", "Gội Đầu", "Cắt Tóc", "Barber", "Hớt Tóc Nam", "Uốn Duỗi Nhuộm", "Phục Hồi Tóc",
        "Gội Đầu Dưỡng Sinh", "Tattoo", "Xăm Hình Nghệ Thuật", "Xỏ Khuyên"
    ],
        "prefixes": ["Viện", "Trung Tâm", "Tiệm", "Salon", "Academy", "Học Viện", "Beauty"],
        "suffixes": ["Công Nghệ Cao", "Hàn Quốc", "Nghệ Thuật", "Nam Nữ", "Dưỡng Sinh", "Thảo Dược", "Tại Nhà"]
    },
    "Giáo Dục": {
        "keywords": [
        "Trường Đại Học", "Học Viện", "Cao Đẳng", "Trung Cấp", "Trường Nghề", "Đại Học Cần Thơ", "FPT",
        "Trường THPT", "Trường THCS", "Trường Tiểu Học", "Trường Mầm Non", "Nhà Trẻ", "Mẫu Giáo",
        "Trung Tâm Anh Ngữ", "Tiếng Anh", "Ngoại Ngữ", "Tin Học", "IELTS", "TOEIC", "Anh Văn Giao Tiếp",
        "Gia Sư", "Luyện Thi", "Dạy Thêm", "Toán Lý Hóa",
        "Dạy Nghề", "Đào Tạo Lái Xe", "Dạy Nhạc", "Piano", "Guitar", "Dạy Vẽ", "Mỹ Thuật",
        "Nhà Sách", "Văn Phòng Phẩm", "Photocopy", "In Ấn", "Thư Viện", "Sách Giáo Khoa"
    ],
        "prefixes": ["Trường", "Trung Tâm", "Học Viện", "Lớp", "Nhà Sách", "Cửa Hàng", "Tiệm", "Văn Phòng"],
        "suffixes": ["Quốc Tế", "Chất Lượng Cao", "Thực Hành", "Văn Phòng Phẩm", "Giá Rẻ", "In Ấn"]
    },
    "Lưu Trú": {
        "keywords": [
        "Khách Sạn", "Hotel", "Nhà Nghỉ", "Motel", "Homestay", "Hostel", "Dorm",
        "Resort", "Khu Nghỉ Dưỡng", "Villa", "Biệt Thự", "Bungalow",
        "Nhà Trọ", "Phòng Trọ", "Cho Thuê Phòng", "Ký Túc Xá", "Sleepbox", "Căn Hộ Dịch Vụ", "Apartment"
    ],
        "prefixes": ["Hệ Thống", "Khu", "Chuỗi", "Dịch Vụ"],
        "suffixes": ["5 Sao", "Cao Cấp", "Bình Dân", "Theo Giờ", "Qua Đêm", "Gần Biển", "View Đẹp", "Luxury"]
    },
    "Giải Trí": {
        "keywords": [
        "Karaoke", "KTV", "Hát Với Nhau", "Phòng Thu Âm",
        "Bida", "Billiards", "CLB Bida", "Bi A", "Bida Phăng", "Bida Lỗ",
        "Internet", "Cyber Game", "Tiệm Net", "Gaming House", "eSports",
        "Rạp Phim", "Cinema", "Khu Vui Chơi", "Nhà Thiếu Nhi", "Thú Nhún", "Nhà Banh",
        "Câu Cá", "Hồ Câu", "Bắn Cá",
        "Phòng Gym", "Fitness", "Yoga", "Aerobic", "Zumba", "Pilates",
        "Sân Bóng Đá", "Sân Cỏ Nhân Tạo", "Hồ Bơi", "Tennis", "Cầu Lông"
    ],
        "prefixes": ["Quán", "Tiệm", "CLB", "Câu Lạc Bộ", "Phòng", "Trung Tâm", "Hệ Thống", "Sân"],
        "suffixes": ["Gia Đình", "Máy Lạnh", "VIP", "Cao Cấp", "Giải Trí", "Thư Giãn"]
    },
    "Vận Tải & Kho Bãi": {
        "keywords": [
        "Bến Xe", "Nhà Xe", "Trạm Xe Buýt", "Bus Station", "Điểm Đón Trả Khách",
        "Chành Xe", "Vận Tải", "Chở Hàng", "Ba Gác", "Xe Tải", "Chuyển Nhà", "Dọn Nhà",
        "Chuyển Phát Nhanh", "Logistics", "Express", "Giao Hàng", "Ship Hàng", "Bưu Cục", "Bưu Điện", "Viettel Post", "VNPost",
        "Phòng Vé Máy Bay", "Vé Tàu", "Đại Lý Vé", "Booking", "Visa"
    ],
        "prefixes": ["Công Ty", "Dịch Vụ", "Văn Phòng", "Trạm", "Đại Lý", "Hãng"],
        "suffixes": ["Trọn Gói", "Bắc Nam", "Tốc Hành", "Giá Rẻ", "Giao Hàng Nhanh", "24/7"]
    },
    "Xây Dựng & Nội Thất": {
        "keywords": [
        "Vật Liệu Xây Dựng", "VLXD", "Cửa Hàng Sơn", "Gạch Men", "Xi Măng", "Sắt Thép", "Tôn Hoa Sen", "Cát Đá",
        "Nhôm Kính", "Cửa Cuốn", "Thạch Cao", "Trần Nhựa", "Inox", "Cơ Khí", "Hàn Tiện",
        "Nội Thất", "Trang Trí", "Rèm Cửa", "Đèn Trang Trí", "Sàn Gỗ", "Giấy Dán Tường",
        "Điện Nước", "Ống Nước", "Dây Điện", "Thiết Bị Vệ Sinh", "Bồn Cầu", "Lavabo",
        "Đồ Gia Dụng", "Khóa Cửa", "Kính Cường Lực", "Mái Hiên", "Bạt Che"
    ],
        "prefixes": ["Cửa Hàng", "Đại Lý", "Công Ty", "Kho", "Xưởng", "Nhà Máy"],
        "suffixes": ["Cao Cấp", "Chính Hãng", "Thi Công", "Lắp Đặt", "Trọn Gói"]
    },
    "Hành Chính & Công Cộng": {
        "keywords": [
        "Ủy Ban Nhân Dân", "UBND", "Hội Đồng Nhân Dân", "HĐND", "Đảng Ủy",
        "Công An", "Trụ Sở", "Cảnh Sát", "PCCC", "CSGT", "Chốt Dân Phòng",
        "Tòa Án", "Viện Kiểm Sát", "Thi Hành Án",
        "Kho Bạc", "Bảo Hiểm Xã Hội", "Sở Giao Thông", "Sở Tài Nguyên", "Sở Xây Dựng",
        "Nhà Văn Hóa", "Trung Tâm Hành Chính", "Đài Truyền Hình", "Bưu Điện Tỉnh"
    ],
        "prefixes": ["Trụ Sở", "Văn Phòng", "Cơ Quan"],
        "suffixes": ["Phường", "Quận", "Thành Phố", "Tỉnh", "Nhân Dân"]
    },
    "Tài Chính & Doanh Nghiệp": {
        "keywords": [
        "Ngân Hàng", "Bank", "ATM", "Phòng Giao Dịch", "Tín Dụng",
        "Vietcombank", "Agribank", "BIDV", "Techcombank", "VietinBank", "MB Bank", "ACB", "VPBank", "TPBank",
        "Sacombank", "Kienlongbank", "MSB", "OceanBank", "SeABank", "DongA Bank", "LienVietPostBank",
        "PGBank", "SaigonBank", "IVB", "HDBank", "NaviBank", "EximBank", "Vietbank", "BacABank",
        "Cầm Đồ", "Tài Chính", "Cho Vay", "Đáo Hạn", "Hỗ Trợ Vốn",
        "Công Ty", "Company", "Văn Phòng", "Office", "Chi Nhánh", "Trụ Sở Chính", "Đại Diện", "TNHH", "Cổ Phần",
        "Luật Sư", "Công Chứng", "Thừa Phát Lại", "Kế Toán", "Kiểm Toán",
        "Bất Động Sản", "Nhà Đất", "Môi Giới", "Ký Gửi", "Địa Ốc", "Dự Án"
    ],
        "prefixes": ["Văn Phòng", "Công Ty", "Tập Đoàn", "Chi Nhánh", "Phòng Giao Dịch", "Dịch Vụ"],
        "suffixes": ["TNHH", "Cổ Phần", "Tư Vấn", "Môi Giới", "Cho Vay", "Lãi Suất Thấp"]
    },
    "Tôn Giáo": {
        "keywords": [
        "Chùa", "Tịnh Xá", "Thiền Viện", "Tu Viện", "Niệm Phật Đường",
        "Nhà Thờ", "Giáo Xứ", "Công Giáo", "Tin Lành", "Dòng Tu",
        "Đình Thần", "Miếu", "Thánh Thất", "Cao Đài", "Lăng Ông",
        "Phật Giáo", "Hòa Hảo", "Ban Trị Sự", "Hội Thánh"
    ],
        "prefixes": ["Tổ Đình", "Thiền Viện", "Tu Viện", "Ngôi"],
        "suffixes": ["Cổ Tự", "Đường", "Tự"]
    },
    "Nông Nghiệp & Thú Y": {
        "keywords": [
        "Phân Bón", "Thuốc Trừ Sâu", "Bảo Vệ Thực Vật", "Đạm Phú Mỹ", "NPK",
        "Hạt Giống", "Cây Giống", "Vườn Ươm", "Hoa Kiểng", "Cây Cảnh", "Lan Rừng", "Bonsai",
        "Vật Tư Nông Nghiệp", "Máy Nông Nghiệp", "Máy Cày", "Hệ Thống Tưới",
        "Thú Y", "Pet Shop", "Phòng Khám Thú Y", "Thức Ăn Chăn Nuôi", "Cám Con Cò", "Thuốc Thú Y", "Chó Mèo", "Cá Cảnh"
    ],
        "prefixes": ["Cửa Hàng", "Đại Lý", "Vườn", "Trại", "Phòng Khám"],
        "suffixes": ["Bảo Vệ Thực Vật", "Nông Nghiệp", "Cây Cảnh", "Uy Tín"]
    }
}

# Tên riêng ngẫu nhiên (Dùng chung cho tất cả để tạo tên thương hiệu)
NAMES = ["An", "Bình", "Cường", "Dũng", "Phát", "Tài", "Lộc", "Hưng", "Thịnh", "Việt", "Nam", "Sài Gòn", "Cần Thơ", "365", "247", "123", "99", "68", "Hùng", "Cô Ba", "Chú Bảy", "Bà Năm", "Ông Sáu", "Cô Tư", "Chú Năm", "Bà Sáu", "Ông Bảy", "Cô Sáu", "Chú Tám", "Bà Bảy", "Ông Chín", "Quang Huy", "Chí Hiếu", "Minh Anh", "Ngọc Lan", "Phương Thảo", "Tuấn Kiệt", "Hải Yến", "Đức Phúc", "Thảo Nguyên", "Văn Long", "Bảo Châu"]

# ==============================================================================
# 2. BỘ MÁY TẠO NHIỄU (3 CHẾ ĐỘ)
# ==============================================================================
def apply_no_noise(text):
    """Chế độ 80%: Dữ liệu sạch 100% (giữ nguyên hoàn toàn)"""
    return text

def apply_light_noise(text):
    """Chế độ 10%: Lỗi nhẹ - chỉ mất dấu hoặc viết hoa/thường"""
    if random.random() < 0.7:
        # Mất dấu (70%)
        text = unidecode.unidecode(text)
    else:
        # Viết hoa/thường (30%)
        if random.random() < 0.6:
            text = text.lower()
        else:
            text = text.upper()
    return text

def apply_heavy_ocr_noise(text):
    """Chế độ 10%: Lỗi nặng - OCR sai, dính chữ, sai ký tự, kí tự lạ"""
    # Mất dấu trước tiên (85%)
    if random.random() < 0.85:
        text = unidecode.unidecode(text)
    
    chars = list(text)
    new_chars = []
    noise_type = random.randint(1, 3)
    
    if noise_type == 1:
        # --- Loại 1: Sai ký tự tương tự (OCR confusion) ---
        for i, c in enumerate(chars):
            if random.random() < 0.12:  # 12% ký tự bị OCR sai
                if c in ['O', 'o', '0']: c = random.choice(['0', 'O', 'o', 'D'])
                elif c in ['I', 'l', '1', 'i']: c = random.choice(['1', 'I', 'l', '|'])
                elif c in ['A', '4', 'a']: c = random.choice(['4', 'A', 'a'])
                elif c in ['E', '3', 'e']: c = random.choice(['3', 'E', 'e'])
                elif c in ['G', '6']: c = random.choice(['6', 'G', '9'])
                elif c in ['B', '8']: c = random.choice(['8', 'B'])
                elif c in ['S', '5']: c = random.choice(['5', 'S'])
                elif c in ['Z', '2']: c = random.choice(['2', 'Z'])
            new_chars.append(c)
    
    elif noise_type == 2:
        # --- Loại 2: Dính chữ (mất spaces) và break chữ ---
        i = 0
        while i < len(chars):
            new_chars.append(chars[i])
            if chars[i] == ' ' and random.random() < 0.25:  # 25% mất space
                pass  # Dính chữ
            i += 1
    
    else:
        # --- Loại 3: Ký tự lạ + sai vị trí ---
        for c in chars:
            if random.random() < 0.08:  # 8% thêm/sai ký tự
                if c == ' ':
                    if random.random() < 0.5:
                        new_chars.append('\n')  # Thay space = newline
                    else:
                        pass  # Bỏ space
                elif random.random() < 0.5:
                    new_chars.append('*')  # Thêm ký tự lạ
                else:
                    new_chars.append(random.choice(['@', '#', '!']))
            new_chars.append(c)
    
    result = "".join(new_chars).strip()
    return result if result else text

# ==============================================================================
# 3. HÀM SINH DỮ LIỆU
# ==============================================================================
def generate_context_data(target_per_cat=15000): # 15k x 17 = 255k dòng
    data = []
    
    print(f">> Bắt đầu sinh dữ liệu NGỮ CẢNH ({target_per_cat} dòng/nhóm)...")
    
    for cat, config in DATA_CONFIG.items():
        kws = config["keywords"]
        pres = config["prefixes"]
        sufs = config["suffixes"]
        
        count = 0
        seen_texts = set()
        attempts = 0
        max_attempts = target_per_cat * 50
        
        while count < target_per_cat and attempts < max_attempts:
            attempts += 1
            kw = random.choice(kws)
            
            # --- CẤU TRÚC ĐA DẠNG ---
            # 1. [Tiền tố] + [Từ khóa]
            # 2. [Từ khóa] + [Hậu tố]
            # 3. [Tiền tố] + [Từ khóa] + [Tên riêng]
            # 4. [Từ khóa] + [Tên riêng] + [Hậu tố]
            # 5. [Tiền tố] + [Từ khóa] + [Hậu tố]

            
            rtype = random.randint(1, 5)
            parts = []
            
            if rtype == 1: parts = [random.choice(pres), kw]
            elif rtype == 2: parts = [kw, random.choice(sufs)]
            elif rtype == 3: parts = [random.choice(pres), kw, random.choice(NAMES)]
            elif rtype == 4: parts = [kw, random.choice(NAMES), random.choice(sufs)]
            elif rtype == 5: parts = [random.choice(pres), kw, random.choice(sufs)]
            
            raw_text = " ".join(parts)
            
            # --- TRỘN NHIỄU (80/10/10 RULE) ---
            dice = random.random()
            if dice < 0.80:
                # 80% Dữ liệu sạch 100%
                final_text = apply_no_noise(raw_text)
            elif dice < 0.90:
                # 10% Lỗi nhẹ (mất dấu, viết hoa/thường)
                final_text = apply_light_noise(raw_text)
            else:
                # 10% Lỗi nặng (OCR sai, dính chữ, ký tự lạ)
                final_text = apply_heavy_ocr_noise(raw_text)
            
            # Kiểm tra trùng và độ dài tối thiểu
            if final_text not in seen_texts and len(final_text) > 3:
                seen_texts.add(final_text)
                data.append({"text": final_text, "label": cat})
                count += 1
                
        print(f"   - Xong nhóm '{cat}': {count} dòng.")

    df = pd.DataFrame(data)
    df = df.sample(frac=1).reset_index(drop=True)
    
    filename = "train_data_context_final.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    # === THỐNG KỀ CHẤT LƯỢNG DỮ LIỆU ===
    print(f"\n" + "="*70)
    print(f">> HOÀN TẤT SINH DỮ LIỆU!")
    print(f"="*70)
    print(f"📊 File: {filename}")
    print(f"📈 Tổng số dòng: {len(df):,}")
    print(f"\n📋 Phân bố theo nhóm:")
    print(df['label'].value_counts().to_string())
    print(f"\n✅ Chất lượng dữ liệu:")
    print(f"   - 80% Dữ liệu SẠCH 100% (giữ nguyên)")
    print(f"   - 10% Lỗi NHẸ (mất dấu, viết hoa/thường)")
    print(f"   - 10% Lỗi NẶNG (OCR sai, dính chữ, ký tự lạ)")
    print(f"\n🎯 Mục tiêu: >= 80% dữ liệu sạch đẹp, 20% lỗi đa dạng")
    print(f"="*70)

if __name__ == "__main__":
    generate_context_data(15000)