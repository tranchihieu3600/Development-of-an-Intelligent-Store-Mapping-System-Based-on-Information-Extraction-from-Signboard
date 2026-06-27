import re
import sys
import os
import psycopg2
from unidecode import unidecode
import networkx as nx
from pyvis.network import Network

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "mydb",
    "user": "myuser",
    "password": "mypassword",
}

def make_id(text):
    text = unidecode(str(text)).lower().strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w_]", "", text)
    return text


# Từ điển chuẩn hóa tên đường
STREETS_CLEAN = {
    "nguyễn văn cừ nối dài": "Nguyễn Văn Cừ Nối Dài",
    "nguyen van cu noi dai": "Nguyễn Văn Cừ Nối Dài",
    "nguyễn văn cừ (nối dài)": "Nguyễn Văn Cừ Nối Dài",
    "nguyễn văn cừ nd": "Nguyễn Văn Cừ Nối Dài",
    "nguyễn văn cừ": "Nguyễn Văn Cừ",
    "nguyen van cu": "Nguyễn Văn Cừ",
    "nguyễn văn cự": "Nguyễn Văn Cừ",
    "nguyễn văn cữ": "Nguyễn Văn Cừ",
    "văn cử": "Nguyễn Văn Cừ",
    "văn cự": "Nguyễn Văn Cừ",
    "nvc": "Nguyễn Văn Cừ",
    
    "3 tháng 2": "Đường 3 Tháng 2",
    "3/2": "Đường 3 Tháng 2",
    
    "30 tháng 4": "Đường 30 Tháng 4",
    "30/4": "Đường 30 Tháng 4",
    "30-4": "Đường 30 Tháng 4",
    "30 4": "Đường 30 Tháng 4",
    "0/4": "Đường 30 Tháng 4",
    
    "cách mạng tháng tám": "Cách Mạng Tháng Tám",
    "cách mạng tháng 8": "Cách Mạng Tháng Tám",
    "cach mang thang 8": "Cách Mạng Tháng Tám",
    "cmt8": "Cách Mạng Tháng Tám",
    
    "nguyễn văn linh": "Nguyễn Văn Linh",
    "nguyen van linh": "Nguyễn Văn Linh",
    "nvl": "Nguyễn Văn Linh",
    "văn linh": "Nguyễn Văn Linh",
    "nguyễn văn": "Nguyễn Văn Cừ",
    
    "mậu thân": "Mậu Thân",
    "mau than": "Mậu Thân",
    
    "trần hưng đạo": "Trần Hưng Đạo",
    "tran hung dao": "Trần Hưng Đạo",
    "trần hưng đao": "Trần Hưng Đạo",
    
    "hùng vương": "Hùng Vương",
    "hung vuong": "Hùng Vương",
    
    "đại lộ hòa bình": "Đại lộ Hòa Bình",
    "hòa bình": "Đại lộ Hòa Bình",
    "hoa binh": "Đại lộ Hòa Bình",
    
    "trần văn hoài": "Trần Văn Hoài",
    "tran van hoai": "Trần Văn Hoài",
    
    "lý tự trọng": "Lý Tự Trọng",
    "ly tu trong": "Lý Tự Trọng",
    
    "võ văn kiệt": "Võ Văn Kiệt",
    "vo van kiet": "Võ Văn Kiệt",
    
    "nguyễn trãi": "Nguyễn Trãi",
    "nguyen trai": "Nguyễn Trãi",
    
    "đề thám": "Đề Thám",
    "de tham": "Đề Thám",
    
    "đinh tiên hoàng": "Đinh Tiên Hoàng",
    "châu văn liêm": "Châu Văn Liêm",
    "ngô quyền": "Ngô Quyền",
    "quang trung": "Quang Trung",
    "trần hoàng na": "Trần Hoàng Na",
    "nguyễn việt hồng": "Nguyễn Việt Hồng",
    "lý thường kiệt": "Lý Thường Kiệt",
    "phan đình phùng": "Phan Đình Phùng",
    "hai bà trưng": "Hai Bà Trưng",
    "trần văn khéo": "Trần Văn Khéo",
    "đồng khởi": "Đồng Khởi",
    "xô viết nghệ tĩnh": "Xô Viết Nghệ Tĩnh",
    "nguyễn an ninh": "Nguyễn An Ninh",
    "đường số 1": "Đường Số 1",
    "đường số 2": "Đường Số 2",
}

WARDS_LIST = [
    "An Khánh", "An Hòa", "An Nghiệp", "An Phú", "An Hội", "An Lạc",
    "Cái Khế", "Hưng Lợi", "Tân An", "Thới Bình", "Xuân Khánh"
]

def parse_address(address):
    if not address:
        return {"street": "", "ward": "", "district": "Quận Ninh Kiều", "city": "Thành phố Cần Thơ"}
    
    parts = [p.strip() for p in address.split(",")]
    city = "Thành phố Cần Thơ"
    district = "Quận Ninh Kiều"
    ward = ""
    street_line = ""
    
    if len(parts) >= 4:
        ward = parts[-3]
        street_line = ", ".join(parts[:-3])
    elif len(parts) == 3:
        p0 = parts[0].lower()
        has_street = True
        for w in WARDS_LIST:
            if w.lower() in p0:
                has_street = False
                break
        if has_street:
            street_line = parts[0]
            ward = parts[1]
        else:
            ward = parts[0]
    elif len(parts) == 2:
        street_line = parts[0]
    else:
        street_line = parts[0]
        
    def clean_val(val):
        if not val:
            return ""
        val_lower = val.lower()
        if val_lower in ["none", "null", "unknown", "thiếu", "không có", "chưa rõ", ""]:
            return ""
        # Remove duplicates like Phường Phường
        val = re.sub(r'(?i)\bphường\s+phường\b', 'Phường', val)
        return val.strip()

    ward = clean_val(ward)
    street_line = clean_val(street_line)
    
    # Standardize ward from the list
    matched_ward = ""
    if ward:
        ward_lower = ward.lower()
        for w in WARDS_LIST:
            if w.lower() in ward_lower:
                matched_ward = f"Phường {w}"
                break
    
    clean_street = street_line
    if clean_street:
        # Pre-clean weird characters at start/end
        clean_street = re.sub(r'^[\s\-\.\:\,]+', '', clean_street)
        clean_street = clean_street.strip(' -.,:')
        
        # 1. Tách số nhà/số hẻm ở chuỗi gốc
        match_num = re.match(r'^([a-zA-Z]?\d+[\w/\\-]*)\s*', clean_street)
        if match_num:
            cand = match_num.group(1).strip()
            if cand.lower() not in ["f4", "f5", "c4", "c6", "c10"]:
                clean_street = clean_street[match_num.end():].strip()
                
        # Loại bỏ lặp các tiền tố "Đường", "Đại lộ", "Hẻm", "Ngõ", "Đ.", "H."
        while True:
            new_val = re.sub(r'^(?i:đường|đại\s+lộ|số|hẻm|đ\.|h\.)\s+', '', clean_street)
            if new_val == clean_street:
                break
            clean_street = new_val
        clean_street = clean_street.strip(' -.,:')
        
        # 2. Tìm tên đường chuẩn từ từ điển dựa trên phần còn lại
        val_lower = clean_street.lower()
        matched_street = ""
        for k, v in sorted(STREETS_CLEAN.items(), key=lambda x: len(x[0]), reverse=True):
            if k in val_lower:
                matched_street = v
                break
                
        if not matched_street:
            # Nếu không có trong từ điển, chuẩn hóa bằng cách viết hoa chữ cái đầu
            cl = clean_street.lower()
            if (not cl or cl in ["none", "null", "unknown", "thiếu", "không có", "chưa rõ", "đường", "phường xã", "y khánh"] or
                cl.startswith("phường ") or cl.startswith("xã ") or cl.startswith("quận ") or cl.startswith("huyện ") or
                cl.startswith("p.") or cl.startswith("p. ") or cl.startswith("q.") or cl.startswith("q. ") or
                cl == "tân an" or cl == "an khánh" or cl == "cần thơ" or "tổ " in cl or "khu vực" in cl or cl.startswith("cổng chợ") or
                "dân cư" in cl or "kv" in cl or "kim mã" in cl or "vành kh" in cl):
                clean_street = ""
            else:
                words = clean_street.split()
                matched_street = " ".join([w.capitalize() for w in words])
        else:
            clean_street = matched_street

        # Đảm bảo không có từ "Đường" hay "Đại lộ" trùng lặp ở đầu
        if clean_street:
            clean_street = re.sub(r'^(?i:đường|đại\s+lộ)\s+', '', clean_street)
            is_dai_lo = "hòa bình" in clean_street.lower() or "đại lộ" in clean_street.lower()
            street_prefix = "Đại lộ" if is_dai_lo else "Đường"
            clean_street = f"{street_prefix} {clean_street}"
            
    if not clean_street:
        clean_street = ""
        
    return {
        "street": clean_street,
        "ward": matched_ward,
        "district": "Quận Ninh Kiều",
        "city": city
    }



def add_node(G, node_id, label, node_type):
    G.add_node(
        node_id,
        label=label,
        title=f"{node_type}: {label}",
        group=node_type
    )


def add_edge(G, source, target, relation):
    G.add_edge(source, target, label=relation)


def add_store_to_graph(G, store):
    store_node = f"Store:{store['store_id']}"
    add_node(G, store_node, store['store_id'], "Store")

    brand_node = f"Brand:{make_id(store['brand'])}"
    category_node = f"Category:{make_id(store['category'])}"
    address_node = f"Address:{make_id(store['address'])}"
    
    add_node(G, brand_node, store["brand"], "Brand")
    add_node(G, category_node, store["category"], "Category")
    add_node(G, address_node, store["address"], "Address")
    
    if store.get("phone"):
        phone_node = f"Phone:{make_id(store['phone'])}"
        add_node(G, phone_node, store["phone"], "Phone")
        add_edge(G, store_node, phone_node, "HAS_PHONE")
        
    if store.get("lat") is not None and store.get("lon") is not None:
        location_node = f"Location:{store['lat']}_{store['lon']}"
        add_node(G, location_node, f"{store['lat']}, {store['lon']}", "Location")
        add_edge(G, store_node, location_node, "HAS_GEO")

    add_edge(G, store_node, brand_node, "HAS_BRAND")
    add_edge(G, store_node, category_node, "BELONGS_TO")
    add_edge(G, store_node, address_node, "LOCATED_AT")

    for service in store.get("service", []):
        service_node = f"Service:{make_id(service)}"
        add_node(G, service_node, service, "Service")
        add_edge(G, store_node, service_node, "PROVIDES")

    addr = parse_address(store["address"])

    if addr["street"]:
        street_node = f"Street:{make_id(addr['street'])}"
        add_node(G, street_node, addr["street"], "Street")
        add_edge(G, address_node, street_node, "ON_STREET")

    if addr["ward"]:
        ward_node = f"Ward:{make_id(addr['ward'])}"
        add_node(G, ward_node, addr["ward"], "Ward")
        add_edge(G, address_node, ward_node, "IN_WARD")
        if addr["street"]:
            # Optionally link street to ward
            add_edge(G, street_node, ward_node, "IN_WARD")

    if addr["district"]:
        district_node = f"District:{make_id(addr['district'])}"
        add_node(G, district_node, addr["district"], "District")
        if addr["ward"]:
            add_edge(G, ward_node, district_node, "IN_DISTRICT")
        else:
            add_edge(G, address_node, district_node, "IN_DISTRICT")

    if addr["city"]:
        city_node = f"City:{make_id(addr['city'])}"
        add_node(G, city_node, addr["city"], "City")
        if addr["district"]:
            add_edge(G, district_node, city_node, "IN_CITY")


def load_stores_from_db():
    print("Loading stores from database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()
    
    query = """
        SELECT 
            s.id, 
            s.name, 
            c.name as category, 
            s.address, 
            s.phone, 
            ST_Y(s.location::geometry) as lat, 
            ST_X(s.location::geometry) as lon 
        FROM shops_store s
        JOIN shops_category c ON s.category_id = c.id;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    stores = []
    for row in rows:
        sid, name, category, address, phone, lat, lon = row
        stores.append({
            "store_id": f"S{sid}",
            "brand": name,
            "category": category,
            "address": address,
            "phone": phone if phone else "",
            "lat": lat,
            "lon": lon,
            "service": []  # Service field is empty for now as it's not in db columns
        })
        
    cur.close()
    conn.close()
    print(f"Loaded {len(stores)} stores from database.")
    return stores

# 1. Fetch stores
stores = load_stores_from_db()

# 2. Build graph
G = nx.DiGraph()
for store in stores:
    add_store_to_graph(G, store)

# 3. Create network visualization
net = Network(
    height="750px",
    width="100%",
    directed=True,
    notebook=False
)
net.from_nx(G)

net.set_options("""
{
  "nodes": {
    "shape": "dot",
    "size": 20,
    "font": {
      "size": 18
    }
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true
      }
    },
    "font": {
      "size": 12,
      "align": "middle"
    }
  },
  "physics": {
    "enabled": true,
    "barnesHut": {
      "gravitationalConstant": -8000,
      "springLength": 180
    }
  }
}
""")

script_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(script_dir, "signkg_graph.html")
net.write_html(html_path)
print(f"Graph generated successfully: {html_path}")

# Post-process to inline lib/bindings/utils.js and inject address filters for a self-contained HTML file
utils_js_path = os.path.join(script_dir, "lib", "bindings", "utils.js")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 1. Inline lib/bindings/utils.js if available
    if os.path.exists(utils_js_path):
        print("Inlining lib/bindings/utils.js...")
        with open(utils_js_path, "r", encoding="utf-8") as f:
            utils_js_content = f.read()
        inlined_script = f"<script type=\"text/javascript\">\n{utils_js_content}\n</script>"
        html_content = re.sub(
            r'<script\s+src=["\']lib/bindings/utils\.js["\']\s*>\s*</script>',
            inlined_script,
            html_content
        )
        print("Successfully inlined lib/bindings/utils.js!")
    else:
        print("Warning: lib/bindings/utils.js not found, skipping inline.")

    # 2. Inject interactive address filters (District, Ward, Street) script & styles
    filter_js_content = """
<script type="text/javascript">
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(initGraphFilters, 200);
});

function initGraphFilters() {
    const container = document.getElementById('mynetwork');
    if (!container) return;
    
    // Create the filter interface container
    const filterDiv = document.createElement('div');
    filterDiv.className = 'graph-filters';
    filterDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px; font-weight: bold; color: #1a73e8; font-size: 14px; margin-right: 10px;">
            🔍 Bộ Lọc Địa Chỉ Tri Thức:
        </div>
        <div class="filter-group">
            <label for="filter-district">Quận/Huyện:</label>
            <select id="filter-district" class="graph-select">
                <option value="">-- Tất cả Quận/Huyện --</option>
            </select>
        </div>
        <div class="filter-group">
            <label for="filter-ward">Phường/Xã:</label>
            <select id="filter-ward" class="graph-select" disabled>
                <option value="">-- Tất cả Phường/Xã --</option>
            </select>
        </div>
        <div class="filter-group">
            <label for="filter-street">Đường:</label>
            <select id="filter-street" class="graph-select">
                <option value="">-- Tất cả Đường --</option>
            </select>
        </div>
        <button id="btn-reset-filters" class="graph-btn">Xóa bộ lọc</button>
    `;
    
    // Create the checkbox filters container
    const checkboxDiv = document.createElement('div');
    checkboxDiv.className = 'checkbox-filters';
    checkboxDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px; font-weight: bold; color: #1a73e8; font-size: 14px; margin-right: 10px;">
            🎨 Hiển thị thuộc tính (Nút):
        </div>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Store" checked> Cửa hàng</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Brand" checked> Thương hiệu</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Category" checked> Danh mục</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Address" checked> Địa chỉ</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Street" checked> Đường</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Ward" checked> Phường/Xã</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-District" checked> Quận/Huyện</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-City" checked> Thành phố</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Location" checked> Tọa độ</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Phone" checked> Điện thoại</label>
        <label class="checkbox-group"><input type="checkbox" id="chk-group-Service" checked> Dịch vụ</label>
    `;
    
    // Insert filter panels before mynetwork container
    container.parentNode.insertBefore(filterDiv, container);
    container.parentNode.insertBefore(checkboxDiv, container);
    
    // Inject styles for the filter panel
    const style = document.createElement('style');
    style.innerHTML = `
        .graph-filters {
            display: flex;
            gap: 15px;
            align-items: center;
            background: #ffffff;
            padding: 12px 20px;
            border: 1px solid #dadce0;
            border-radius: 12px;
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            flex-wrap: wrap;
        }
        .checkbox-filters {
            display: flex;
            gap: 12px;
            align-items: center;
            background: #ffffff;
            padding: 10px 20px;
            border: 1px solid #dadce0;
            border-radius: 12px;
            margin-bottom: 15px;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            flex-wrap: wrap;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #202124;
            cursor: pointer;
            user-select: none;
            padding: 4px 8px;
            border-radius: 6px;
            transition: background-color 0.2s;
        }
        .checkbox-group:hover {
            background-color: #f1f3f4;
        }
        .checkbox-group input {
            cursor: pointer;
            accent-color: #1a73e8;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .filter-group label {
            font-size: 11px;
            font-weight: bold;
            color: #5f6368;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .graph-select {
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #dadce0;
            background-color: white;
            min-width: 180px;
            font-size: 13px;
            color: #202124;
            outline: none;
            transition: border-color 0.2s;
        }
        .graph-select:focus {
            border-color: #1a73e8;
        }
        .graph-select:disabled {
            background-color: #f1f3f4;
            color: #9aa0a6;
            cursor: not-allowed;
        }
        .graph-btn {
            padding: 8px 18px;
            background-color: #1a73e8;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            align-self: flex-end;
            margin-bottom: 1px;
            font-size: 13px;
            transition: background-color 0.2s;
        }
        .graph-btn:hover {
            background-color: #1557b0;
        }
    `;
    document.head.appendChild(style);
    
    const districtSelect = document.getElementById('filter-district');
    const wardSelect = document.getElementById('filter-ward');
    const streetSelect = document.getElementById('filter-street');
    const resetBtn = document.getElementById('btn-reset-filters');
    
    const checkboxIds = [
        'chk-group-Store', 'chk-group-Brand', 'chk-group-Category', 'chk-group-Address',
        'chk-group-Street', 'chk-group-Ward', 'chk-group-District', 'chk-group-City',
        'chk-group-Location', 'chk-group-Phone', 'chk-group-Service'
    ];
    
    // Extract unique values
    const allGraphNodes = nodes.get();
    const districts = new Set();
    const wards = new Set();
    const streets = new Set();
    
    allGraphNodes.forEach(node => {
        if (node.group === 'District') districts.add(node.label);
        if (node.group === 'Ward') wards.add(node.label);
        if (node.group === 'Street') streets.add(node.label);
    });
    
    Array.from(districts).sort().forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.textContent = d;
        districtSelect.appendChild(opt);
    });
    
    Array.from(streets).sort().forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        streetSelect.appendChild(opt);
    });
    
    // Scan edges to establish Ward <-> District & Street <-> Ward relations
    const wardToDistrict = {};
    const streetToWard = {};
    const allGraphEdges = edges.get();
    
    allGraphEdges.forEach(edge => {
        const fromNode = allGraphNodes.find(n => n.id === edge.from);
        const toNode = allGraphNodes.find(n => n.id === edge.to);
        if (fromNode && toNode) {
            if (fromNode.group === 'Ward' && toNode.group === 'District') {
                wardToDistrict[fromNode.label] = toNode.label;
            }
            if (fromNode.group === 'Street' && toNode.group === 'Ward') {
                streetToWard[fromNode.label] = toNode.label;
            }
        }
    });
    
    function updateWardsDropdown() {
        const selDistrict = districtSelect.value;
        wardSelect.innerHTML = '<option value="">-- Tất cả Phường/Xã --</option>';
        wardSelect.disabled = !selDistrict;
        
        if (selDistrict) {
            Array.from(wards).sort().forEach(w => {
                if (wardToDistrict[w] === selDistrict) {
                    const opt = document.createElement('option');
                    opt.value = w;
                    opt.textContent = w;
                    wardSelect.appendChild(opt);
                }
            });
        }
    }
    
    districtSelect.addEventListener('change', () => {
        updateWardsDropdown();
        applyFilters();
    });
    wardSelect.addEventListener('change', applyFilters);
    streetSelect.addEventListener('change', applyFilters);
    
    checkboxIds.forEach(id => {
        const chk = document.getElementById(id);
        if (chk) {
            chk.addEventListener('change', applyFilters);
        }
    });
    
    resetBtn.addEventListener('click', () => {
        districtSelect.value = '';
        updateWardsDropdown();
        streetSelect.value = '';
        checkboxIds.forEach(id => {
            const chk = document.getElementById(id);
            if (chk) chk.checked = true;
        });
        applyFilters();
    });
    
    function applyFilters() {
        const selDistrict = districtSelect.value;
        const selWard = wardSelect.value;
        const selStreet = streetSelect.value;
        
        // Checkboxes states
        const activeGroups = {
            'Store': document.getElementById('chk-group-Store').checked,
            'Brand': document.getElementById('chk-group-Brand').checked,
            'Category': document.getElementById('chk-group-Category').checked,
            'Address': document.getElementById('chk-group-Address').checked,
            'Street': document.getElementById('chk-group-Street').checked,
            'Ward': document.getElementById('chk-group-Ward').checked,
            'District': document.getElementById('chk-group-District').checked,
            'City': document.getElementById('chk-group-City').checked,
            'Location': document.getElementById('chk-group-Location').checked,
            'Phone': document.getElementById('chk-group-Phone').checked,
            'Service': document.getElementById('chk-group-Service').checked
        };
        
        const nodesToUpdate = [];
        
        allGraphNodes.forEach(node => {
            let matches = true;
            
            // First check checkbox state
            if (!activeGroups[node.group]) {
                matches = false;
            } else if (selDistrict || selWard || selStreet) {
                if (node.group === 'District') {
                    matches = (node.label === selDistrict);
                }
                else if (node.group === 'Ward') {
                    matches = (!selWard || node.label === selWard) && (!selDistrict || wardToDistrict[node.label] === selDistrict);
                }
                else if (node.group === 'Street') {
                    matches = (!selStreet || node.label === selStreet) && 
                              (!selWard || streetToWard[node.label] === selWard) &&
                              (!selDistrict || !streetToWard[node.label] || wardToDistrict[streetToWard[node.label]] === selDistrict);
                }
                else {
                    // Trace connections
                    const connected = network.getConnectedNodes(node.id);
                    let nodeDistrict = '';
                    let nodeWard = '';
                    let nodeStreet = '';
                    
                    connected.forEach(connId => {
                        const connNode = allGraphNodes.find(n => n.id === connId);
                        if (connNode) {
                            if (connNode.group === 'District') nodeDistrict = connNode.label;
                            if (connNode.group === 'Ward') nodeWard = connNode.label;
                            if (connNode.group === 'Street') nodeStreet = connNode.label;
                            
                            if (connNode.group === 'Address') {
                                const addrConn = network.getConnectedNodes(connNode.id);
                                addrConn.forEach(acId => {
                                    const acNode = allGraphNodes.find(n => n.id === acId);
                                    if (acNode) {
                                        if (acNode.group === 'District') nodeDistrict = acNode.label;
                                        if (acNode.group === 'Ward') nodeWard = acNode.label;
                                        if (acNode.group === 'Street') nodeStreet = acNode.label;
                                    }
                                });
                            }
                        }
                    });
                    
                    // Fallback
                    if (nodeStreet) {
                        if (!nodeWard && streetToWard[nodeStreet]) nodeWard = streetToWard[nodeStreet];
                    }
                    if (nodeWard) {
                        if (!nodeDistrict && wardToDistrict[nodeWard]) nodeDistrict = wardToDistrict[nodeWard];
                    }
                    
                    if (selDistrict && nodeDistrict !== selDistrict) matches = false;
                    if (selWard && nodeWard !== selWard) matches = false;
                    if (selStreet && nodeStreet !== selStreet) matches = false;
                }
            }
            
            node.hidden = !matches;
            nodesToUpdate.push(node);
        });
        
        nodes.update(nodesToUpdate);
    }
}
</script>
</body>
"""
    
    # Append the custom script at the end of the body
    html_content = html_content.replace("</body>", filter_js_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Successfully injected interactive address filters into signkg_graph.html!")
else:
    print("Error: signkg_graph.html not found, cannot post-process.")


