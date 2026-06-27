import sys
import re
from PIL import Image, ExifTags
import pillow_heif

# Đăng ký HEIC
pillow_heif.register_heif_opener()

# ==============================================================================
# ĐƯỜNG DẪN ẢNH SAMSUNG M34 CỦA BẠN
# ==============================================================================
IMAGE_PATH = r"/home/quanghuy/DaiHoc/LuanVanTotNghiep/Web_GIS/map/20260105_150726.jpg" 
# ==============================================================================

def scan_file_for_gps_text(path):
    """Quét thô toàn bộ file để tìm chuỗi văn bản liên quan đến GPS (XMP)"""
    print(">> Đang quét thô (Raw Scan) tìm dữ liệu XMP/Text...")
    try:
        with open(path, 'rb') as f:
            content = f.read()
            # Tìm các từ khóa GPS phổ biến trong metadata dạng text (XML/XMP)
            # Ví dụ: <exif:GPSLatitude>...</exif:GPSLatitude>
            patterns = [
                rb'GPSLatitude', rb'GPSLongitude', 
                rb'gps:Latitude', rb'gps:Longitude'
            ]
            
            found = False
            for p in patterns:
                if p in content:
                    print(f"   ✅ TÌM THẤY chuỗi '{p.decode()}' trong file! -> Có XMP GPS.")
                    found = True
                    # Cố gắng trích xuất đoạn text xung quanh để xem
                    idx = content.find(p)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + 100)
                    snippet = content[start:end]
                    try:
                        print(f"      Trích đoạn: {snippet.decode('utf-8', errors='ignore')}")
                    except: pass
            
            if not found:
                print("   ❌ Không tìm thấy từ khóa GPS trong dạng văn bản (XMP).")
                
    except Exception as e:
        print(f"   Lỗi quét thô: {e}")

def check_deep_metadata(img_path):
    print(f"\n--- KIỂM TRA SÂU: {img_path} ---")
    
    try:
        img = Image.open(img_path)
    except Exception as e:
        print(f"❌ Không mở được ảnh: {e}")
        return

    # 1. KIỂM TRA EXIF CHUẨN (Standard EXIF)
    print("\n[1] KIỂM TRA EXIF CHUẨN (getexif):")
    exif = img.getexif()
    if not exif:
        print("   ❌ Không có EXIF header.")
    else:
        # Tìm GPS trong IFD (0x8825)
        gps_info = exif.get_ifd(0x8825)
        if gps_info:
            print(f"   ✅ TÌM THẤY THẺ GPS IFD (0x8825)!")
            print(f"   Dữ liệu thô: {gps_info}")
        else:
            print("   ❌ Có EXIF nhưng KHÔNG CÓ thẻ GPS (0x8825).")

    # 2. KIỂM TRA INFO DICT (Nơi pillow_heif thường giấu metadata)
    print("\n[2] KIỂM TRA PIL INFO DICTIONARY:")
    for k, v in img.info.items():
        # XMP thường nằm ở key 'xmp' hoặc 'XML:com.adobe.xmp'
        if 'xmp' in str(k).lower():
            print(f"   ✅ TÌM THẤY GÓI XMP (Key: {k})!")
            # Convert bytes sang string để tìm GPS
            if isinstance(v, bytes):
                v_str = v.decode('utf-8', errors='ignore')
            else:
                v_str = str(v)
            
            if 'GPS' in v_str:
                print("   👉 Dữ liệu GPS nằm trong XMP này!")
                # In thử 1 đoạn có chứa GPS
                idx = v_str.find("GPS")
                print(f"      Nội dung: ...{v_str[idx:idx+100]}...")
            else:
                print("   👉 Có XMP nhưng không thấy chữ 'GPS' bên trong.")
        else:
            print(f"   - Tìm thấy key khác: {k}")

    # 3. QUÉT THÔ FILE (Biện pháp cuối cùng)
    print("\n[3] QUÉT THÔ FILE (RAW BYTE SEARCH):")
    scan_file_for_gps_text(img_path)

if __name__ == "__main__":
    check_deep_metadata(IMAGE_PATH)