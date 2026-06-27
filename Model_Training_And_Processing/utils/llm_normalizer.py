import os
import re
from pathlib import Path

# Path to the GGUF model (user supplied)
MODEL_PATH = Path(r"D:\Thuc_Tap\models\qwen2.5-3b-instruct-q4_k_m.gguf")

# Cache the model globally so it only loads once
_llm_instance = None

def _load_llama_cpp():
    """Load the model using llama_cpp and return a Llama instance."""
    global _llm_instance
    if _llm_instance is None:
        from llama_cpp import Llama
        _llm_instance = Llama(model_path=str(MODEL_PATH), n_ctx=2048, n_gpu_layers=-1, verbose=False)
    return _llm_instance

DICT_STREETS_CLEAN = {
    "nguyễn văn cử": "Nguyễn Văn Cừ",
    "nguyễn văn cự": "Nguyễn Văn Cừ",
    "nguyễn văn cữ": "Nguyễn Văn Cừ",
    "văn cử": "Nguyễn Văn Cừ",
    "văn cự": "Nguyễn Văn Cừ",
    "nguyen van cu": "Nguyễn Văn Cừ",
    "nvc": "Nguyễn Văn Cừ",
    "cmt8": "Cách Mạng Tháng Tám",
    "cach mang thang 8": "Cách Mạng Tháng Tám",
    "cách mạng tháng 8": "Cách Mạng Tháng Tám",
    "nvl": "Nguyễn Văn Linh",
    "nguyen van linh": "Nguyễn Văn Linh",
    "3/2": "Đường 3 Tháng 2",
    "3 tháng 2": "Đường 3 Tháng 2",
    "30/4": "Đường 30 Tháng 4",
    "30 tháng 4": "Đường 30 Tháng 4",
}

DICT_WARDS_CLEAN = {
    "an khánh": "An Khánh",
    "an khanh": "An Khánh",
    "xuân khánh": "Xuân Khánh",
    "xuan khanh": "Xuân Khánh",
    "hưng lợi": "Hưng Lợi",
    "hung loi": "Hưng Lợi",
    "an hòa": "An Hòa",
    "an hoa": "An Hòa",
    "cái khế": "Cái Khế",
    "cai khe": "Cái Khế",
    "tân an": "Tân An",
    "tan an": "Tân An",
    "thới bình": "Thới Bình",
    "thoi binh": "Thới Bình",
    "an nghiệp": "An Nghiệp",
    "an nghiep": "An Nghiệp",
    "an phú": "An Phú",
    "an phu": "An Phú",
    "an hội": "An Hội",
    "an hoi": "An Hội",
    "an lạc": "An Lạc",
    "an lac": "An Lạc",
}

DICT_DISTRICTS_CLEAN = {
    "ninh kiều": "Ninh Kiều",
    "ninh kieu": "Ninh Kiều",
    "bình thủy": "Bình Thủy",
    "binh thuy": "Bình Thủy",
    "cái răng": "Cái Răng",
    "cai rang": "Cái Răng",
}

def preprocess_address(addr: str) -> str:
    # 1. Standard replacements (abbreviations and spelling fixes)
    addr = re.sub(r'(?i)\b(nvc|văn cử|văn cự|nguyễn văn cử|nguyễn văn cự|nguyễn văn cữ|nguyen van cu)\b', 'Nguyễn Văn Cừ', addr)
    addr = re.sub(r'(?i)\b(cmt8|cach mang thang 8|cách mạng tháng 8)\b', 'Cách Mạng Tháng Tám', addr)
    addr = re.sub(r'(?i)\b(nvl|nguyen van linh)\b', 'Nguyễn Văn Linh', addr)
    addr = re.sub(r'(?i)\b(tpct|ct)\b', 'Cần Thơ', addr)
    addr = re.sub(r'(?i)\b(nk)\b', 'Ninh Kiều', addr)
    
    # Clean up prefixes
    addr = re.sub(r'(?i)\bp\.ak\b', 'An Khánh', addr)
    addr = re.sub(r'(?i)\bp\.xk\b', 'Xuân Khánh', addr)
    addr = re.sub(r'(?i)\bp\.hl\b', 'Hưng Lợi', addr)
    addr = re.sub(r'(?i)\bp\.ah\b', 'An Hòa', addr)
    addr = re.sub(r'(?i)\bp\.ck\b', 'Cái Khế', addr)
    addr = re.sub(r'(?i)\bp\.ta\b', 'Tân An', addr)
    addr = re.sub(r'(?i)\bp\.tb\b', 'Thới Bình', addr)
    addr = re.sub(r'(?i)\bp\.an\b', 'An Nghiệp', addr)
    addr = re.sub(r'(?i)\bp\.ap\b', 'An Phú', addr)
    
    addr = re.sub(r'(?i)\b(nd|nd\.)\b', 'nối dài', addr)
    
    # 3/2 and 30/4
    addr = re.sub(r'(?i)\b3/2\b', 'Đường 3 Tháng 2', addr)
    addr = re.sub(r'(?i)\b30/4\b', 'Đường 30 Tháng 4', addr)
    
    return addr

def postprocess_address(addr: str) -> str:
    parts = [p.strip() for p in addr.split(",")]
    street = ""
    ward = ""
    district = ""
    city = ""
    
    if len(parts) == 4:
        street, ward, district, city = parts
    elif len(parts) == 3:
        street, district, city = parts
    elif len(parts) == 2:
        street, city = parts
    elif len(parts) == 1:
        street = parts[0]
    elif len(parts) > 4:
        city = parts[-1]
        district = parts[-2]
        ward = parts[-3]
        street = ", ".join(parts[:-3])
        
    # Clean up XML/HTML tags and placeholders like "<Thiếu thành phần này>"
    street = re.sub(r'<[^>]*>', '', street).strip()
    ward = re.sub(r'<[^>]*>', '', ward).strip()
    district = re.sub(r'<[^>]*>', '', district).strip()
    city = re.sub(r'<[^>]*>', '', city).strip()
    
    # Clean up terms meaning missing/unspecified info
    for term in ["thiếu", "chưa rõ", "không có", "unknown", "none", "null"]:
        if term in street.lower():
            street = ""
        if term in ward.lower():
            ward = ""
        if term in district.lower():
            district = ""
        if term in city.lower():
            city = ""
            
    # Self-healing logical checks for misplaced components
    # 1. Check if district is actually a ward (e.g. LLM output: "Nguyễn Văn Cừ, , Phường Tân An, Cần Thơ")
    district_lower = district.lower()
    for k, v in DICT_WARDS_CLEAN.items():
        if k in district_lower:
            ward = v
            district = ""
            break
            
    # 2. Check if ward is actually a district (e.g. LLM output: "Nguyễn Văn Cừ, Ninh Kiều, , Cần Thơ")
    ward_lower = ward.lower()
    for k, v in DICT_DISTRICTS_CLEAN.items():
        if k in ward_lower:
            district = v
            ward = ""
            break

    # Street corrections
    street_lower = street.lower()
    for k, v in DICT_STREETS_CLEAN.items():
        if k in street_lower:
            street = re.sub(re.escape(k), v, street, flags=re.IGNORECASE)
            
    # Ward corrections
    ward_lower = ward.lower()
    matched_ward = False
    for k, v in DICT_WARDS_CLEAN.items():
        if k in ward_lower:
            ward = v
            matched_ward = True
            break
            
    # District corrections
    district_lower = district.lower()
    matched_district = False
    for k, v in DICT_DISTRICTS_CLEAN.items():
        if k in district_lower:
            district = v
            matched_district = True
            break
            
    # Automatic district mapping if ward is known (Ninh Kieu wards)
    if matched_ward and not district:
        district = "Ninh Kiều"
        
    # City corrections
    city_lower = city.lower()
    if "cần thơ" in city_lower or "tpct" in city_lower or "ct" in city_lower or not city:
        city = "Thành phố Cần Thơ"
    elif "hồ chí minh" in city_lower or "tphcm" in city_lower or "hcm" in city_lower:
        city = "Thành phố Hồ Chí Minh"
        
    if ward and not ward.startswith("Phường"):
        if not ward.startswith("Xã"):
            ward = "Phường " + ward
            
    if district and not district.startswith("Quận") and not district.startswith("Huyện"):
        district = "Quận " + district
        
    # Clean up duplicate words like "Đường Đường", "Phường Phường", "Quận Quận"
    street = re.sub(r'(?i)\bđường\s+đường\b', 'Đường', street)
    ward = re.sub(r'(?i)\bphường\s+phường\b', 'Phường', ward)
    district = re.sub(r'(?i)\bquận\s+quận\b', 'Quận', district)
    city = re.sub(r'(?i)\bthành\s+phố\s+thành\s+phố\b', 'Thành phố', city)

    # Reassemble structured address
    return f"{street}, {ward}, {district}, {city}"

SYSTEM_PROMPT = """Bạn là chuyên gia định dạng địa chỉ Việt Nam. Nhiệm vụ của bạn là nhận vào một địa chỉ và định dạng nó thành cấu trúc chuẩn.

QUY TẮC BẮT BUỘC:
1. Giữ nguyên số nhà (ví dụ: 123, 12/5, 45A, số 23-A). Nếu không có số nhà thì bỏ trống phần đó.
2. Định dạng đầu ra BẮT BUỘC phải là: <Số nhà> <Tên đường>, <Phường/Xã>, <Quận/Huyện>, <Thành phố>
3. Hãy giữ nguyên dấu tiếng Việt và tên đường chuẩn như trong input (ví dụ: "Nguyễn Văn Cừ", "Mậu Thân", "Cách Mạng Tháng Tám", "Đường 3 Tháng 2"). KHÔNG tự ý thay đổi hay viết sai tên đường.
4. Nếu thiếu thành phần nào thì bỏ trống phần đó nhưng VẪN GIỮ CÁC DẤU PHẨY để phân tách các trường.
5. Chỉ trả về một dòng địa chỉ duy nhất, KHÔNG giải thích gì thêm.

VÍ DỤ:
Input: "123 Nguyễn Văn Cừ, Phường An Khánh, Ninh Kiều, Cần Thơ"
Output: "123 Nguyễn Văn Cừ, Phường An Khánh, Quận Ninh Kiều, Thành phố Cần Thơ"

Input: "45A Đường 3 Tháng 2, p.xuan khanh, q.ninh kieu, tp.can tho"
Output: "45A Đường 3 Tháng 2, Phường Xuân Khánh, Quận Ninh Kiều, Thành phố Cần Thơ"

Input: "Nguyễn Văn Linh, Phường Hưng Lợi, Quận Ninh Kiều, Thành phố Cần Thơ"
Output: "Nguyễn Văn Linh, Phường Hưng Lợi, Quận Ninh Kiều, Thành phố Cần Thơ"
"""

USER_PROMPT_TEMPLATE = """Chuan hoa dia chi sau:
Input: "{input_address}"
Output:"""


def normalize_address(raw_address: str) -> str:
    """Standardize a raw address string using a hybrid Python + LLM approach."""
    if not raw_address or not raw_address.strip():
        return ", , , "

    # 1. Preprocess in Python (fixes spelling errors, replaces abbreviations)
    preprocessed = preprocess_address(raw_address)

    # 2. Run through LLM to structure
    llm = _load_llama_cpp()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(input_address=preprocessed)}
    ]

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=128,
        temperature=0.0,
        stop=["\n\n"]
    )

    text = output["choices"][0]["message"]["content"]
    result = text.strip().strip('"').strip("'").strip()
    if result.lower().startswith("output:"):
        result = result[7:].strip().strip('"').strip("'").strip()

    # 3. Postprocess in Python (ensures exact district matching, correct city, cleans commas)
    final_result = postprocess_address(result)
    return final_result
