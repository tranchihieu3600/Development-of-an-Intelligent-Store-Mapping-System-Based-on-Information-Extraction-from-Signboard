import sys
from PIL import Image, ExifTags
import pillow_heif

# Đăng ký opener cho HEIC
pillow_heif.register_heif_opener()

# ==============================================================================
# CẤU HÌNH: ĐỔI ĐƯỜNG DẪN ẢNH CỦA BẠN VÀO DƯỚI ĐÂY
# ==============================================================================
IMAGE_PATH = r"/home/quanghuy/DaiHoc/LuanVanTotNghiep/Web_GIS/map/20260105_150726.jpg"
# ==============================================================================

def get_decimal_from_dms(dms, ref):
    """Hàm chuyển đổi tọa độ dạng (Độ, Phút, Giây) sang Số thập phân"""
    try:
        def to_float(val):
            if isinstance(val, tuple):
                return val[0] / val[1] if val[1] != 0 else 0
            return float(val)

        degrees = to_float(dms[0])
        minutes = to_float(dms[1])
        seconds = to_float(dms[2])

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal
    except Exception as e:
        print(f"Lỗi tính toán tọa độ: {e}")
        return None

def check_image_metadata(img_path):
    print(f"\n--- ĐANG KIỂM TRA FILE: {img_path} ---")
    
    try:
        image = Image.open(img_path)
        # [SỬA LỖI] Dùng getexif() thay vì _getexif()
        exif = image.getexif()
    except Exception as e:
        print(f"❌ LỖI KHÔNG ĐỌC ĐƯỢC ẢNH: {e}")
        return

    if exif is None:
        print("❌ KẾT QUẢ: File không có metadata.")
        return

    print("✅ Đã đọc được EXIF. Đang tìm thông tin GPS...")
    
    # [QUAN TRỌNG] Với getexif(), GPS nằm trong một IFD riêng (ID 34853)
    # Ta phải lấy nó ra bằng hàm get_ifd()
    gps_info = exif.get_ifd(0x8825) # 0x8825 là mã hex của GPSInfo

    # In thông tin cơ bản
    for k, v in exif.items():
        tag = ExifTags.TAGS.get(k, k)
        if tag in ["Make", "Model", "DateTimeOriginal"]:
            print(f"📷 {tag}: {v}")

    print("-" * 50)

    if not gps_info:
        print("⚠️ CẢNH BÁO: Không tìm thấy thẻ GPS trong ảnh này.")
    else:
        print("📍 TÌM THẤY DỮ LIỆU GPS! Đang giải mã...")
        try:
            # GPSInfo Key: 1=LatRef, 2=Lat, 3=LonRef, 4=Lon
            lat_ref = gps_info.get(1)
            lat_dms = gps_info.get(2)
            lon_ref = gps_info.get(3)
            lon_dms = gps_info.get(4)

            if lat_dms and lon_dms and lat_ref and lon_ref:
                lat = get_decimal_from_dms(lat_dms, lat_ref)
                lon = get_decimal_from_dms(lon_dms, lon_ref)
                
                print(f"   ► Vĩ độ (Lat): {lat}")
                print(f"   ► Kinh độ (Lon): {lon}")
                print(f"   ► Google Maps: https://www.google.com/maps/search/?api=1&query={lat},{lon}")
            else:
                print("❌ Dữ liệu GPS bị thiếu.")
                print("Raw Data:", gps_info)
        except Exception as e:
            print(f"❌ Lỗi giải mã GPS: {e}")

if __name__ == "__main__":
    check_image_metadata(IMAGE_PATH)