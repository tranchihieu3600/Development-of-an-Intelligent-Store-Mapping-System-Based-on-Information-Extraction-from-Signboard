from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    decimal = degrees + minutes + seconds
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_clean_address(location):
    """Hàm lọc chỉ lấy Đường, Phường, Quận, Thành phố"""
    if not location:
        return "Không tìm thấy địa chỉ"
        
    addr = location.raw.get('address', {})
    
    # Tạo danh sách chứa các thành phần muốn lấy
    parts = []

    # 1. Lấy tên đường
    if 'road' in addr:
        parts.append(addr['road'])
    
    # 2. Lấy Phường/Xã (OSM thường lưu là 'quarter', 'village' hoặc 'ward')
    # Ưu tiên lấy quarter trước, nếu không có thì tìm các key khác
    ward = addr.get('quarter') or addr.get('ward') or addr.get('village')
    if ward:
        parts.append(ward)

    # 3. Lấy Quận/Huyện (OSM thường lưu là 'city_district', 'district' hoặc 'county')
    district = addr.get('city_district') or addr.get('district') or addr.get('county') or addr.get('suburb')
    if district:
        parts.append(district)

    # 4. Lấy Tỉnh/Thành phố
    city = addr.get('city') or addr.get('state')
    if city:
        parts.append(city)

    # Ghép lại bằng dấu phẩy
    return ", ".join(parts)

def get_geo_info(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            print("Ảnh không có dữ liệu EXIF.")
            return

        gps_info = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "GPSInfo":
                for key in value.keys():
                    sub_tag = GPSTAGS.get(key, key)
                    gps_info[sub_tag] = value[key]
        
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = get_decimal_from_dms(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
            lon = get_decimal_from_dms(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])

            print(f"📍 Toạ độ: {lat}, {lon}")

            # Gọi Geopy
            geolocator = Nominatim(user_agent="luan_van_app")
            location = geolocator.reverse(f"{lat}, {lon}")

            # --- PHẦN QUAN TRỌNG: LỌC ĐỊA CHỈ ---
            short_address = get_clean_address(location)
            print(f"🏠 Địa chỉ rút gọn: {short_address}")
            # ------------------------------------

        else:
            print("Ảnh này không có dữ liệu GPS.")

    except Exception as e:
        print(f"Lỗi: {e}")

# Chạy thử
# Lưu ý: Thay đường dẫn ảnh của bạn vào đây
get_geo_info("/home/quanghuy/DaiHoc/LuanVanTotNghiep/Web_GIS/map/9.jpg")