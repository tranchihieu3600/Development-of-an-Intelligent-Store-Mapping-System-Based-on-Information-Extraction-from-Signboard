import psycopg2
import json
from collections import defaultdict
import math
import sys
import heapq
from rtree import index

DB_CONFIG = {
    'dbname' : 'gisdb',
    'user' : 'postgres',
    'password' : '05112004',
    'host' : 'localhost',
    'port' : '5432'
}

def _get_data ():
    """
        Lấy dữ liệu từ database
    """

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
        SELECT gid, length_m, source, target, 
                cost, reverse_cost, ST_AsGeoJSON(the_geom) as the_geom
        FROM ways
    """

    cursor.execute(sql)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data

def _standardization_data (data):
    """
        Chuẩn hóa dữ liệu thành những phần có thể sử dụng (giống với lý thuyết)
        - Danh sách các đỉnh để  thực hiện thuật toán sẽ bao gồm:
            + vertice_id
            + Các đỉnh kề
            + Độ dài cạnh
            + Heuristic
        - Danh sách các cạnh để vẽ lên bản đồ sẽ bao gồm:
            + edge_id
            + Điểm đầu
            + Điểm cuối
            + geometry
            + one_way
    """
    graph = defaultdict(list)
    nodes_coords = {}

    # Lấy các đỉnh kề
    for gid, length_m, source, target, cost, reverse_cost, the_geom in data:

        geom = json.loads(the_geom)
        coords = geom['coordinates']
        nodes_coords[source] = tuple(coords[0])
        nodes_coords[target] = tuple(coords[-1])

        # Chiều thuận
        if cost >= 0:
            graph[source].append((target, cost))

        # Chiều ngược (nếu tồn tại)
        if reverse_cost >= 0:
            graph[target].append((source, reverse_cost))

    return graph, nodes_coords

def haversine (coord1, coord2):
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371
    phi1 = math.radians(lon1)
    lamda1 = math.radians(lat1)
    phi2 = math.radians(lon2)
    lamda2 = math.radians(lat2)

    delta_phi = phi2 - phi1
    delta_lamda = lamda2 - lamda1

    d = 2*R * math.asin(math.sqrt(math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lamda/2)**2))
    return d

def near_node (coord_root, nodes_coords):
    distance_min = sys.float_info.max
    for node, coord in nodes_coords.item():
        distance = haversine(coord_root, coord)
        if (distance < distance_min):
            node_nearest = node
    return node_nearest

def dijsktra_sovle (graph, start, end):
    priority_queue = [(0, start)]
    came_from = {start: None}
    cost_min_curr = {start: 0}

    while priority_queue:
        curr_cost, curr = heapq.heappop(priority_queue)

        if curr == end:
            path = []
            temp = curr
            while temp != start:
                prev = came_from[temp]
                path.append(prev)
                temp = prev
            return path[::-1]

        if curr_cost > cost_min_curr.get(curr, float('inf')):continue

        for neighbor, cost in graph.get(curr, []):
            new_cost = curr_cost + cost
            if(new_cost < cost_min_curr.get(neighbor, float('inf'))):
                cost_min_curr[neighbor] = new_cost
                heapq.heappush(priority_queue, (new_cost, neighbor))
                came_from[neighbor] = (curr)

def astart_solve (graph, nodes_coords, start, end):
    priority_queue = [(0, 0, float('inf'), start)]
    came_from = {start: None}
    curr = start
    f_dict = {start: haversine(nodes_coords[start], nodes_coords[end])}

    while curr != end:
        f, g, h, node = heapq.heappop(priority_queue)
        
        curr = node
        for neighbor, cost in graph.get(curr, []):
            g_new = cost + g
            h_new = haversine(nodes_coords[neighbor], nodes_coords[end])
            f_new = g_new + h_new
            if f_new > f_dict.get(neighbor, float('inf')): 
                continue
            heapq.heappush(priority_queue, (f_new, g_new, h_new, neighbor))
            came_from[neighbor] = (curr)
            f_dict[neighbor] = f_new
    
    temp = end
    path = []
    while temp != start:
        path.append(temp)
        temp = came_from[temp]

    return path[::-1]


data = _get_data()
graph, nodes = _standardization_data(data)
# print(graph)

print(dijsktra_sovle(graph, 5100, 5040))
print(astart_solve(graph, nodes, 5100, 5040))