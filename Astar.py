"""
    代码主要功能:
    基于A*算法实现路径搜索,支持道路折点的处理。
"""
import pandas as pd
import heapq
import math
import json

class Map_Astar:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.coords = {}
        self.edge_paths = {}  
        
    def add_node(self, node_id, name, lon, lat):
        self.nodes[node_id] = name
        self.coords[node_id] = (lon, lat)
        if node_id not in self.edges:
            self.edges[node_id] = {}
    
    def add_bian(self, from_id, to_id, dist, path_points=None):
        if from_id not in self.edges:
            self.edges[from_id] = {}
        if to_id not in self.edges:
            self.edges[to_id] = {}
        self.edges[from_id][to_id] = dist
        self.edges[to_id][from_id] = dist
        #存储路径折点
        if path_points and len(path_points) > 0:
            self.edge_paths[(from_id, to_id)] = path_points
            self.edge_paths[(to_id, from_id)] = path_points[::-1]
        else:
            #如果没有折点,就用直线连接
            self.edge_paths[(from_id, to_id)] = [
                list(self.coords[from_id]),
                list(self.coords[to_id])
            ]
            self.edge_paths[(to_id, from_id)] = [
                list(self.coords[to_id]),
                list(self.coords[from_id])
            ]

    #获取两个节点之间的详细路径点
    def get_edge_path(self, from_id, to_id):
        return self.edge_paths.get((from_id, to_id), None)
    
    #使用Haversine公式计算地球表面两点距离
    def get_str8dist(self, n1, n2):
        lon1, lat1 = self.coords[n1]
        lon2, lat2 = self.coords[n2]
        #转换为弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        #Haversine公式
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        #地球半径(米)
        R = 6371000
        return R * c
    
    def assearch(self, start, end):
        visited_c = 0
        
        # 增加边界检查
        if start not in self.nodes or end not in self.nodes:
            return None, float('inf'), None, 0
        
        if start not in self.edges or not self.edges[start]:
            print(f"警告: 起点{start}没有任何连接的边")
            return None, float('inf'), None, 0
        
        if end not in self.edges or not self.edges[end]:
            print(f"警告: 终点{end}没有任何连接的边")
            return None, float('inf'), None, 0
        
        g_score = {node: float('inf') for node in self.nodes}
        g_score[start] = 0
        f_score = {node: float('inf') for node in self.nodes}
        f_score[start] = self.get_str8dist(start, end)
        openlist = []
        heapq.heappush(openlist, (f_score[start], start))
        yuan = {}
        closed_set = set()
        
        while openlist:
            curr_f, curr = heapq.heappop(openlist)
            if curr in closed_set:
                continue

            visited_c += 1
            closed_set.add(curr)
            
            if curr == end:
                path = [] 
                totdist = g_score[end]
                temp = end
                while temp in yuan:
                    path.append(temp)
                    temp = yuan[temp]
                path.append(start)
                path.reverse()
                detailed_path = self._build_detailed_path(path)
                return path, totdist, detailed_path, visited_c
            
            if curr not in self.edges:
                continue

            for neighbor, weight in self.edges[curr].items():
                if neighbor in closed_set:
                    continue
                ttt_g = g_score[curr] + weight
                if ttt_g < g_score[neighbor]:
                    yuan[neighbor] = curr 
                    g_score[neighbor] = ttt_g
                    f_score[neighbor] = ttt_g + self.get_str8dist(neighbor, end)
                    heapq.heappush(openlist, (f_score[neighbor], neighbor))
        
        # 未找到路径，打印调试信息
        print(f"A*算法未找到路径: {start}→{end}, 访问了{visited_c}个节点")
        return None, float('inf'), None, visited_c
    
    def _build_detailed_path(self, node_path):        
        detailed_coords = []
        for i in range(len(node_path) - 1):
            from_node = node_path[i]
            to_node = node_path[i + 1]
            #获取这条边的详细路径点
            edge_path = self.get_edge_path(from_node, to_node)
            if edge_path:
                if i == 0:
                    #第一条边,添加所有点
                    detailed_coords.extend(edge_path)
                else:
                    #后续边,跳过第一个点(避免重复)
                    detailed_coords.extend(edge_path[1:])
        return detailed_coords
    
    def get_nodename(self, node_id):
        return self.nodes.get(node_id, "Unknown")
    
    def get_coord(self, node_id):
        return self.coords.get(node_id, None)

#解析路径点字符串
def parse_path_points(path_str):
    if not path_str or pd.isna(path_str):
        return None
    try:
        #JSON格式
        if path_str.startswith('['):
            return json.loads(path_str)
        #分号分隔格式
        if ';' in path_str:
            points = []
            for point_str in path_str.split(';'):
                coords = [float(x.strip()) for x in point_str.split(',')]
                points.append(coords)
            return points
        return None
    except:
        return None

#加载图数据,支持道路折点
def get_graph(nodes_csv, distance_csv):
    g = Map_Astar()
    df_nodes = pd.read_csv(nodes_csv, encoding='utf-8-sig')
    for _, row in df_nodes.iterrows():
        g.add_node(row['node_id'], row['name'], row['longitude'], row['latitude'])
    df_dist = pd.read_csv(distance_csv, encoding='utf-8-sig')
    for _, row in df_dist.iterrows():
        #识别起点和终点列名
        if 'node1' in row and 'node2' in row:
            from_id, to_id = row['node1'], row['node2']
        elif 'from' in row and 'to' in row:
            from_id, to_id = row['from'], row['to']
        elif 'start' in row and 'end' in row:
            from_id, to_id = row['start'], row['end']
        else:
            from_id, to_id = row.iloc[0], row.iloc[1]
        
        distance = row.get('distance', row.get('length', row.get('weight', row.iloc[2])))
        path_points = None
        if 'waypoints' in row:
            path_points = parse_path_points(row['waypoints'])
        g.add_bian(from_id, to_id, distance, path_points)
    return g

#运行A*算法并返回结果
def run_astar(start_id, end_id, graph):
    path, dist, detailed_coords, visited_count = graph.assearch(start_id, end_id)
    #转换坐标格式[lon,lat]->[lat,lon] 
    path_coords = [[coord[1], coord[0]] for coord in detailed_coords] if detailed_coords else []
    result = {
        'path': path,
        'distance': round(dist, 2) if dist != float('inf') else None,
        'path_names': [graph.get_nodename(nid) for nid in path] if path else [],
        'path_coords': path_coords,  #包含所有折点的详细路径
        'node_count': len(path) if path else 0,
        'waypoint_count': len(path_coords) if path_coords else 0,
        'visited_nodes': visited_count 
    }
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        nodes_file = 'map_nodes.csv'
        edges_file = 'distance_final.csv'
    else:
        nodes_file = sys.argv[1]
        edges_file = sys.argv[2]
    graph = get_graph(nodes_file, edges_file)

    if len(graph.nodes) >= 2:
        start = list(graph.nodes.keys())[0]
        end = list(graph.nodes.keys())[-1]
        result = run_astar(start, end, graph)