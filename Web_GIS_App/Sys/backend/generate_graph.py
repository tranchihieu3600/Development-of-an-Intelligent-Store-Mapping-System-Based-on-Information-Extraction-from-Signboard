import os
import sys
import re
import django
from unidecode import unidecode
import networkx as nx
from pyvis.network import Network

# Thiết lập môi trường Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from shops.models import Store, Category

def make_id(text):
    text = unidecode(str(text)).lower().strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w_]", "", text)
    return text

def parse_address(address):
    if not address:
        return {"street": "", "district": "", "city": "Cần Thơ"}
    
    # 1. Chuẩn hóa dấu phân cách
    address_norm = address.replace(" - ", ", ").replace("-", ",")
    parts = [p.strip() for p in address_norm.split(",") if p.strip()]
    
    street = ""
    district = ""
    city = "Cần Thơ" # Mặc định là Cần Thơ vì hầu hết dữ liệu ở đây
    
    # Danh sách các quận/huyện của Cần Thơ để so khớp chính xác
    districts_db = {
        "ninh kiều": "Ninh Kiều", "ninh kieu": "Ninh Kiều",
        "cái răng": "Cái Răng", "cai rang": "Cái Răng",
        "bình thủy": "Bình Thủy", "binh thuy": "Bình Thủy",
        "ô môn": "Ô Môn", "o mon": "Ô Môn",
        "thốt nốt": "Thốt Nốt", "thot not": "Thốt Nốt",
        "phong điền": "Phong Điền", "phong dien": "Phong Điền",
        "cờ đỏ": "Cờ Đỏ", "co do": "Cờ Đỏ",
        "thới lai": "Thới Lai", "thoi lai": "Thới Lai",
        "vĩnh thạnh": "Vĩnh Thạnh", "vinh thanh": "Vĩnh Thạnh"
    }

    # 2. Tìm kiếm Thành phố và Quận Huyện bằng từ khóa trước
    found_district = False
    for part in parts:
        part_lower = part.lower()
        
        # Tìm quận huyện
        for dk, dv in districts_db.items():
            if dk in part_lower:
                district = dv
                found_district = True
                break
        
        # Tìm thành phố
        if "cần thơ" in part_lower or "can tho" in part_lower or "tpct" in part_lower or "tp.ct" in part_lower:
            city = "Cần Thơ"

    # 3. Phân tích Tuyến đường (Street)
    # Loại bỏ các phần liên quan đến quận huyện, thành phố, hẻm, tổ, khu vực để tìm tên đường chính xác
    skip_keywords = ["khu vực", "khu vuc", "kv", "ấp", "ap", "hẻm", "hem", "ngõ", "ngo", "tổ", "to", "nền", "nen", "số", "so"]
    ward_keywords = ["phường", "phuong", "p.", "xã", "xa", "tt.", "thị trấn"]
    
    candidate_parts = []
    for part in parts:
        part_lower = part.lower()
        
        # Bỏ các phần là thành phố hoặc quận huyện đã nhận diện
        is_city_or_district = False
        if "cần thơ" in part_lower or "can tho" in part_lower or "tpct" in part_lower or "tp.ct" in part_lower:
            is_city_or_district = True
        for dk in districts_db.keys():
            if dk in part_lower:
                is_city_or_district = True
                break
                
        # Bỏ các phần chỉ chứa phường/xã
        is_ward = any(w in part_lower for w in ward_keywords)
        
        # Bỏ các phần chỉ chứa số nhà đơn thuần hoặc hẻm/khu vực đơn thuần
        is_skip = any(part_lower.startswith(k) for k in skip_keywords) or re.match(r'^\d+[\w/-]*$', part)
        
        if not is_city_or_district and not is_ward and not is_skip:
            candidate_parts.append(part)

    if candidate_parts:
        street = candidate_parts[0]
    elif parts:
        street = parts[0]
        
    # Làm sạch tên đường (loại bỏ số nhà đứng đầu, chữ "Đường"...)
    street = re.sub(r'^(?:so\s+|số\s+)?(?:\d+[\w/-]*\s*[-/]*\s*)+', '', street, flags=re.IGNORECASE).strip()
    street = re.sub(r'^(?:đường|duong)\s+', '', street, flags=re.IGNORECASE).strip()
    
    # Chuẩn hóa một số tên đường phổ biến bị viết tắt hoặc dư thừa
    street_lower = street.lower()
    if "nguyen van cu" in street_lower or "nguyễn văn cừ" in street_lower:
        street = "Nguyễn Văn Cừ"
    elif "mậu thân" in street_lower or "mau than" in street_lower:
        street = "Mậu Thân"
    elif "nguyen van linh" in street_lower or "nguyễn văn linh" in street_lower:
        street = "Nguyễn Văn Linh"
    elif "30/4" in street_lower or "30 tháng 4" in street_lower:
        street = "30 Tháng 4"
    elif "3/2" in street_lower or "3 tháng 2" in street_lower:
        street = "3 Tháng 2"
    elif "hòa bình" in street_lower or "hoa binh" in street_lower:
        street = "Đại lộ Hòa Bình"
    elif "mậu thân" in street_lower or "mau than" in street_lower:
        street = "Mậu Thân"
        
    # Dự phòng nếu ko tìm thấy quận huyện, xem phần trước Cần Thơ có phải quận huyện ko
    if not district:
        if len(parts) >= 2:
            last_parts = parts[-2].lower()
            if not any(k in last_parts for k in skip_keywords + ward_keywords):
                district = parts[-2]
        if not district:
            district = "Ninh Kiều"

    district = re.sub(r'^(?:quận|quan|huyện|huyen)\s+', '', district, flags=re.IGNORECASE).strip()
    
    return {
        "street": street.strip(),
        "district": district.strip(),
        "city": city.strip()
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
    store_id_str = f"S{store.id:03d}"
    store_node = f"Store:{store_id_str}"
    add_node(G, store_node, store_id_str, "Store")

    # Lấy thông tin từ các trường model của Django
    brand_name = store.name
    category_name = store.category.name
    address_str = store.address
    lat = store.location.y if store.location else 0.0
    lon = store.location.x if store.location else 0.0

    brand_node = f"Brand:{make_id(brand_name)}"
    category_node = f"Category:{make_id(category_name)}"
    address_node = f"Address:{make_id(address_str)}"
    location_node = f"Location:{lat}_{lon}"

    add_node(G, brand_node, brand_name, "Brand")
    add_node(G, category_node, category_name, "Category")
    add_node(G, address_node, address_str, "Address")
    add_node(G, location_node, f"{lat}, {lon}", "Location")

    add_edge(G, store_node, brand_node, "HAS_BRAND")
    add_edge(G, store_node, category_node, "BELONGS_TO")
    add_edge(G, store_node, address_node, "LOCATED_AT")
    add_edge(G, store_node, location_node, "HAS_GEO")

    if store.phone and store.phone.strip():
        phone_str = store.phone.strip()
        phone_node = f"Phone:{make_id(phone_str)}"
        add_node(G, phone_node, phone_str, "Phone")
        add_edge(G, store_node, phone_node, "HAS_PHONE")

    # Lấy các dịch vụ từ phần mô tả (describe) nếu có
    services = []
    if store.describe:
        services = [s.strip() for s in store.describe.split(",") if len(s.strip()) > 0]
    
    for service in services:
        service_node = f"Service:{make_id(service)}"
        add_node(G, service_node, service, "Service")
        add_edge(G, store_node, service_node, "PROVIDES")

    addr = parse_address(address_str)

    if addr["street"]:
        street_node = f"Street:{make_id(addr['street'])}"
        add_node(G, street_node, addr["street"], "Street")
        add_edge(G, address_node, street_node, "ON_STREET")

    district_node = None
    if addr["district"]:
        district_node = f"District:{make_id(addr['district'])}"
        add_node(G, district_node, addr["district"], "District")
        add_edge(G, address_node, district_node, "IN_DISTRICT")

    if addr["city"]:
        city_node = f"City:{make_id(addr['city'])}"
        add_node(G, city_node, addr["city"], "City")
        if district_node:
            add_edge(G, district_node, city_node, "IN_CITY")
        else:
            add_edge(G, address_node, city_node, "IN_CITY")

def generate_graph():
    # Lấy toàn bộ các Store từ database thực tế
    db_stores = Store.objects.all()
    if not db_stores.exists():
        print("Empty database. Please add stores first!")
        return

    G = nx.DiGraph()
    for store in db_stores:
        add_store_to_graph(G, store)

    net = Network(
        height="750px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources="remote",
        select_menu=True,
        filter_menu=True,
        neighborhood_highlight=True
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
      },
      "groups": {
        "Store": {
          "color": {
            "background": "#ff7675",
            "border": "#d63031"
          },
          "shape": "dot"
        },
        "Brand": {
          "color": {
            "background": "#ffeaa7",
            "border": "#fdcb6e"
          },
          "shape": "diamond"
        },
        "Category": {
          "color": {
            "background": "#81ecec",
            "border": "#00cec9"
          },
          "shape": "star"
        },
        "Address": {
          "color": {
            "background": "#a29bfe",
            "border": "#6c5ce7"
          },
          "shape": "box"
        },
        "Phone": {
          "color": {
            "background": "#fd79a8",
            "border": "#e84393"
          },
          "shape": "ellipse"
        },
        "Location": {
          "color": {
            "background": "#55efc4",
            "border": "#00b894"
          },
          "shape": "dot"
        },
        "Service": {
          "color": {
            "background": "#fab1a0",
            "border": "#e17055"
          },
          "shape": "triangle"
        },
        "Street": {
          "color": {
            "background": "#74b9ff",
            "border": "#0984e3"
          },
          "shape": "box"
        },
        "District": {
          "color": {
            "background": "#ffeaa7",
            "border": "#fdcb6e"
          },
          "shape": "dot"
        },
        "City": {
          "color": {
            "background": "#dfe6e9",
            "border": "#b2bec3"
          },
          "shape": "dot"
        }
      }
    }
    """)

    # Lưu đồ thị ra thư mục LuanVan chính
    output_path = r"D:\LuanVan\signkg_graph.html"
    net.write_html(output_path)
    post_process_html(output_path)
    print("Graph generated successfully at: " + output_path)

def post_process_html(file_path):
    import re
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Việt hóa menu tìm kiếm thực thể (Select Node ID)
    html = html.replace('<option selected>Select a Node by ID</option>', '<option value="">Tìm kiếm thực thể (Node)...</option>')
    html = html.replace('Reset Selection</button>', 'Đặt lại</button>')

    # 2. Thay thế menu lọc mặc định của PyVis bằng bộ lọc Đơn giản của chúng ta (dùng index để chính xác tuyệt đối)
    new_filter_menu = """<div id="filter-menu" class="card-header bg-light">
                <div class="row align-items-center">
                  <div class="col-md-3 col-sm-6 pb-2">
                    <label class="form-label fw-bold text-secondary small mb-1">Danh mục cửa hàng</label>
                    <select id="filter-category" multiple placeholder="Chọn danh mục..."></select>
                  </div>
                  <div class="col-md-3 col-sm-6 pb-2">
                    <label class="form-label fw-bold text-secondary small mb-1">Tuyến đường (Phố)</label>
                    <select id="filter-street" multiple placeholder="Chọn tuyến đường..."></select>
                  </div>
                  <div class="col-md-3 col-sm-6 pb-2">
                    <label class="form-label fw-bold text-secondary small mb-1">Quận/Huyện</label>
                    <select id="filter-district" multiple placeholder="Chọn quận/huyện..."></select>
                  </div>
                  <div class="col-md-3 col-sm-12 pb-2 d-flex align-items-end pt-3">
                    <button type="button" class="btn btn-danger w-100" onclick="resetAllFilters();">Đặt lại bộ lọc</button>
                  </div>
                </div>
                
                <div class="row pt-2 mt-2 border-top">
                  <div class="col-12">
                    <span class="fw-bold text-secondary small me-3">Hiển thị liên kết:</span>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Brand" value="Brand" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Brand">Thương hiệu</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Category" value="Category" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Category">Danh mục</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Address" value="Address" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Address">Địa chỉ</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Location" value="Location" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Location">Tọa độ</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Phone" value="Phone" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Phone">Số điện thoại</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Service" value="Service" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Service">Dịch vụ</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-Street" value="Street" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-Street">Tuyến đường</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-District" value="District" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-District">Quận/Huyện</label>
                    </div>
                    <div class="form-check form-check-inline">
                      <input class="form-check-input node-type-toggle" type="checkbox" id="toggle-City" value="City" checked onchange="applyRealtimeFilters()">
                      <label class="form-check-label small" for="toggle-City">Thành phố</label>
                    </div>
                  </div>
                </div>
              </div>"""

    idx_start = html.find('<div id="filter-menu"')
    idx_end = html.find('<div id="mynetwork"')
    if idx_start != -1 and idx_end != -1:
        html = html[:idx_start] + new_filter_menu + "\n            " + html[idx_end:]

    # 3. Thay thế script TomSelect mặc định bằng script đã được sửa đổi cho bộ lọc mới
    old_script_pattern = re.compile(
        r'new TomSelect\("#select-node".*?function updateFilter\(value, key\) \{.*?\}',
        re.DOTALL
    )

    new_script = """new TomSelect("#select-node",{
                      create: false,
                      placeholder: "Tìm kiếm thực thể (Node)...",
                      noResultsText: "Không tìm thấy kết quả",
                      sortField: {
                          field: "text",
                          direction: "asc"
                      }
                  });

                  // Khởi tạo các bộ lọc TomSelect trống
                  let categoryTs = new TomSelect("#filter-category", {
                      maxItems: null,
                      valueField: 'id',
                      labelField: 'title',
                      searchField: 'title',
                      create: false,
                      placeholder: "Tất cả danh mục",
                      onChange: applyRealtimeFilters
                  });

                  let streetTs = new TomSelect("#filter-street", {
                      maxItems: null,
                      valueField: 'id',
                      labelField: 'title',
                      searchField: 'title',
                      create: false,
                      placeholder: "Tất cả tuyến đường",
                      onChange: applyRealtimeFilters
                  });

                  let districtTs = new TomSelect("#filter-district", {
                      maxItems: null,
                      valueField: 'id',
                      labelField: 'title',
                      searchField: 'title',
                      create: false,
                      placeholder: "Tất cả quận/huyện",
                      onChange: applyRealtimeFilters
                  });

                  let storeConnections = {};
                  let storeMeta = {};

                  function initFiltersData() {
                      let allNodesObj = nodes.get({ returnType: "Object" });
                      let allEdgesObj = edges.get({ returnType: "Object" });

                      for (let nodeId in allNodesObj) {
                          if (allNodesObj[nodeId].group === 'Store') {
                              storeConnections[nodeId] = new Set([nodeId]);
                              storeMeta[nodeId] = { category: '', street: '', district: '' };
                          }
                      }

                      let addressToStreet = {};
                      let addressToDistrict = {};

                      for (let edgeId in allEdgesObj) {
                          let edge = allEdgesObj[edgeId];
                          let fromNode = edge.from;
                          let toNode = edge.to;
                          
                          if (allNodesObj[fromNode] && allNodesObj[fromNode].group === 'Address') {
                              if (allNodesObj[toNode] && allNodesObj[toNode].group === 'Street') {
                                  addressToStreet[fromNode] = toNode;
                              }
                              if (allNodesObj[toNode] && allNodesObj[toNode].group === 'District') {
                                  addressToDistrict[fromNode] = toNode;
                              }
                          }
                      }

                      for (let edgeId in allEdgesObj) {
                          let edge = allEdgesObj[edgeId];
                          let fromNode = edge.from;
                          let toNode = edge.to;
                          
                          let storeId = null;
                          let otherNodeId = null;
                          
                          if (storeConnections[fromNode]) {
                              storeId = fromNode;
                              otherNodeId = toNode;
                          } else if (storeConnections[toNode]) {
                              storeId = toNode;
                              otherNodeId = fromNode;
                          }
                          
                          if (storeId && otherNodeId) {
                              storeConnections[storeId].add(otherNodeId);
                              
                              let otherNode = allNodesObj[otherNodeId];
                              if (otherNode) {
                                  if (otherNode.group === 'Category') {
                                      storeMeta[storeId].category = otherNodeId;
                                  }
                                  if (otherNode.group === 'Address') {
                                      let addrId = otherNodeId;
                                      if (addressToStreet[addrId]) {
                                          storeConnections[storeId].add(addressToStreet[addrId]);
                                          storeMeta[storeId].street = addressToStreet[addrId];
                                      }
                                      if (addressToDistrict[addrId]) {
                                          storeConnections[storeId].add(addressToDistrict[addrId]);
                                          storeMeta[storeId].district = addressToDistrict[addrId];
                                      }
                                  }
                              }
                          }
                      }

                      // Điền dữ liệu vào dropdowns
                      let uniqueCategories = {};
                      let uniqueStreets = {};
                      let uniqueDistricts = {};

                      for (let storeId in storeMeta) {
                          let meta = storeMeta[storeId];
                          if (meta.category && allNodesObj[meta.category]) {
                              uniqueCategories[meta.category] = allNodesObj[meta.category].label;
                          }
                          if (meta.street && allNodesObj[meta.street]) {
                              uniqueStreets[meta.street] = allNodesObj[meta.street].label;
                          }
                          if (meta.district && allNodesObj[meta.district]) {
                              uniqueDistricts[meta.district] = allNodesObj[meta.district].label;
                          }
                      }

                      for (let id in uniqueCategories) {
                          categoryTs.addOption({ id: id, title: uniqueCategories[id] });
                      }
                      for (let id in uniqueStreets) {
                          streetTs.addOption({ id: id, title: uniqueStreets[id] });
                      }
                      for (let id in uniqueDistricts) {
                          districtTs.addOption({ id: id, title: uniqueDistricts[id] });
                      }
                  }

                  function applyRealtimeFilters() {
                      let selectedCats = categoryTs.getValue();
                      let selectedStreets = streetTs.getValue();
                      let selectedDistricts = districtTs.getValue();
                      
                      let checkedTypes = new Set(['Store']);
                      document.querySelectorAll('.node-type-toggle:checked').forEach(cb => {
                          checkedTypes.add(cb.value);
                      });
                      
                      let hasFilter = selectedCats.length > 0 || selectedStreets.length > 0 || selectedDistricts.length > 0;
                      let visibleNodes = new Set();
                      
                      for (let storeId in storeMeta) {
                          let meta = storeMeta[storeId];
                          let matchesCat = selectedCats.length === 0 || selectedCats.includes(meta.category);
                          let matchesStreet = selectedStreets.length === 0 || selectedStreets.includes(meta.street);
                          let matchesDistrict = selectedDistricts.length === 0 || selectedDistricts.includes(meta.district);
                          
                          if (matchesCat && matchesStreet && matchesDistrict) {
                              if (storeConnections[storeId]) {
                                  storeConnections[storeId].forEach(nodeId => {
                                      visibleNodes.add(nodeId);
                                  });
                              }
                          }
                      }
                      
                      let allNodes = nodes.get({ returnType: "Object" });
                      let updateArray = [];
                      
                      for (let nodeId in allNodes) {
                          let node = allNodes[nodeId];
                          let linkedToStore = !hasFilter || visibleNodes.has(nodeId);
                          let typeAllowed = checkedTypes.has(node.group);
                          let shouldBeVisible = linkedToStore && typeAllowed;
                          
                          if (node.hidden !== !shouldBeVisible) {
                              node.hidden = !shouldBeVisible;
                              if (node.hidden) {
                                  if (node.savedLabel === undefined) {
                                      node.savedLabel = node.label;
                                      node.label = undefined;
                                  }
                              } else {
                                  if (node.savedLabel !== undefined) {
                                      node.label = node.savedLabel;
                                      node.savedLabel = undefined;
                                  }
                              }
                              updateArray.push(node);
                          }
                      }
                      
                      if (updateArray.length > 0) {
                          nodes.update(updateArray);
                      }
                  }

                  function resetAllFilters() {
                      categoryTs.clear();
                      streetTs.clear();
                      districtTs.clear();
                      document.querySelectorAll('.node-type-toggle').forEach(cb => {
                          cb.checked = true;
                      });
                      applyRealtimeFilters();
                  }

                  setTimeout(initFiltersData, 500);"""

    html = old_script_pattern.sub(new_script, html)

    # 4. Thay thế highlightFilter có bug returnType: 'object'
    html = html.replace("let allEdges = edges.get({returnType: 'object'});", "let allEdges = edges.get({returnType: 'Object'});")
    html = html.replace("let allEdges = edges.get({ returnType: 'object' });", "let allEdges = edges.get({ returnType: 'Object' });")
    html = html.replace("let allEdges = edges.get({ returnType: \"object\" });", "let allEdges = edges.get({ returnType: \"Object\" });")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    generate_graph()
