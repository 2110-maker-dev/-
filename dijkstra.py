import pandas as pd
import heapq
import json

class DijkstraNavigator:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.coords = {}
        self.edge_paths = {}  # 存储边的详细路径（包含折点）
        
    def load_nodes(self, nodes_csv):
        """加载节点数据"""
        df = pd.read_csv(nodes_csv, encoding='utf-8-sig')
        for _, row in df.iterrows():
            node_id = int(row['node_id'])
            self.nodes[node_id] = row['name']
            self.coords[node_id] = (float(row['longitude']), float(row['latitude']))
            self.edges[node_id] = {}
        return self
    
    def load_edges(self, edges_csv):
        """加载边数据，包括道路折点信息"""
        df = pd.read_csv(edges_csv, encoding='utf-8-sig')
        edge_count = 0
        
        for _, row in df.iterrows():
            # 识别起点和终点列名
            if 'node1' in df.columns and 'node2' in df.columns:
                from_id = int(row['node1'])
                to_id = int(row['node2'])
            elif 'from' in df.columns and 'to' in df.columns:
                from_id = int(row['from'])
                to_id = int(row['to'])
            elif 'start' in df.columns and 'end' in df.columns:
                from_id = int(row['start'])
                to_id = int(row['end'])
            else:
                from_id = int(row.iloc[0])
                to_id = int(row.iloc[1])
            
            # 获取距离
            if 'distance' in df.columns:
                dist = float(row['distance'])
            elif 'length' in df.columns:
                dist = float(row['length'])
            elif 'weight' in df.columns:
                dist = float(row['weight'])
            else:
                dist = float(row.iloc[2])
            
            # 添加双向边
            self.edges[from_id][to_id] = dist
            self.edges[to_id][from_id] = dist
            edge_count += 1
            
            # 加载道路折点信息
            path_points = None
            if 'waypoints' in df.columns:
                path_points = self._parse_path_points(row['waypoints'])
            
            # 存储边的详细路径
            if path_points and len(path_points) > 0:
                self.edge_paths[(from_id, to_id)] = path_points
                self.edge_paths[(to_id, from_id)] = path_points[::-1]  # 反向路径
            else:
                # 如果没有折点，用节点坐标作为直线连接
                lon1, lat1 = self.coords[from_id]
                lon2, lat2 = self.coords[to_id]
                self.edge_paths[(from_id, to_id)] = [[lon1, lat1], [lon2, lat2]]
                self.edge_paths[(to_id, from_id)] = [[lon2, lat2], [lon1, lat1]]
        
        return self
    
    def _parse_path_points(self, path_str):
        """解析路径点字符串"""
        if not path_str or pd.isna(path_str):
            return None
        try:
            # JSON格式: [[lon1, lat1], [lon2, lat2], ...]
            if isinstance(path_str, str) and path_str.startswith('['):
                return json.loads(path_str)
            # 分号分隔格式: "lon1,lat1;lon2,lat2;..."
            if isinstance(path_str, str) and ';' in path_str:
                points = []
                for point_str in path_str.split(';'):
                    coords = [float(x.strip()) for x in point_str.split(',')]
                    points.append(coords)
                return points
            return None
        except Exception as e:
            return None
    
    def _build_detailed_path(self, node_path):
        """构建包含所有折点的详细路径"""
        detailed_coords = []
        
        for i in range(len(node_path) - 1):
            from_node = node_path[i]
            to_node = node_path[i + 1]
            
            # 获取这条边的详细路径点
            edge_path = self.edge_paths.get((from_node, to_node))
            
            if edge_path:
                if i == 0:
                    # 第一条边，添加所有点
                    detailed_coords.extend(edge_path)
                else:
                    # 后续边，跳过第一个点（避免重复）
                    detailed_coords.extend(edge_path[1:])
            else:
                # 如果没有存储的路径，使用节点坐标
                lon1, lat1 = self.coords[from_node]
                lon2, lat2 = self.coords[to_node]
                if i == 0:
                    detailed_coords.append([lon1, lat1])
                detailed_coords.append([lon2, lat2])
        
        return detailed_coords
    
    def find_path(self, start, end):
        """使用Dijkstra算法查找最短路径"""
        import time
        start_time = time.time()
        
        # 节点存在性检查
        if start not in self.nodes or end not in self.nodes:
            return {
                'success': False, 
                'error': f'节点不存在: start={start}, end={end}', 
                'path': None
            }
        
        # 检查起点是否有邻居
        if not self.edges.get(start):
            return {
                'success': False, 
                'error': f'起点{start}({self.nodes[start]})没有任何连接的边', 
                'path': None
            }
        
        # 检查终点是否有邻居
        if not self.edges.get(end):
            return {
                'success': False, 
                'error': f'终点{end}({self.nodes[end]})没有任何连接的边', 
                'path': None
            }
        
        # 初始化Dijkstra算法
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        previous = {node: None for node in self.nodes}
        pq = [(0, start)]  # 优先队列: (距离, 节点)
        visited = set()
        
        # Dijkstra主循环
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            # 如果节点已访问，跳过
            if current in visited:
                continue
            visited.add(current)
            
            # 如果到达终点，提前结束
            if current == end:
                break
            
            # 松弛操作：检查所有邻居
            for neighbor, weight in self.edges[current].items():
                if neighbor in visited:
                    continue
                    
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # 计算执行时间
        exec_time = (time.time() - start_time) * 1000
        
        # 检查是否找到路径
        if distances[end] == float('inf'):
            return {
                'success': False, 
                'error': f'从节点{start}({self.nodes[start]})到节点{end}({self.nodes[end]})不连通',
                'path': None,
                'visited_nodes': len(visited)
            }
        
        # 重建路径（从终点回溯到起点）
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        # 构建详细路径（包含所有折点）
        detailed_coords = self._build_detailed_path(path)
        
        # 转换坐标格式 [lon, lat] -> [lat, lon] 以适配Leaflet地图
        coords_path = [[coord[1], coord[0]] for coord in detailed_coords]
        
        # 返回结果
        return {
            'success': True,
            'algorithm': 'Dijkstra',
            'path': path,
            'path_names': [self.nodes[node_id] for node_id in path],
            'distance': round(distances[end], 2),
            'execution_time': round(exec_time, 2),
            'path_coords': coords_path,  # 包含所有折点的完整路径
            'node_count': len(path),  # 主要节点数
            'waypoint_count': len(coords_path),  # 路径点总数（包括折点）
            'visited_nodes': len(visited)  # 算法访问的节点数
        }

# 全局导航器实例
nav = DijkstraNavigator()

def init_dijkstra(nodes_csv, edges_csv):
    """初始化Dijkstra导航器"""
    try:
        nav.load_nodes(nodes_csv).load_edges(edges_csv)
        return nav
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

def dijkstra_find_path(navigator, start, end):
    """提供给Flask调用的接口函数"""
    return navigator.find_path(start, end)

# 兼容旧版本的函数名
def find_path(start, end):
    """直接使用全局导航器查找路径"""
    return nav.find_path(start, end)

# 测试代码
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        nodes_file = 'map_nodes.csv'
        edges_file = 'distance_final.csv'
    else:
        nodes_file = sys.argv[1]
        edges_file = sys.argv[2]
    
    # 初始化
    navigator = init_dijkstra(nodes_file, edges_file)
    
    if navigator and len(navigator.nodes) >= 2:
        # 测试路径查找
        node_ids = list(navigator.nodes.keys())
        start = node_ids[0]
        end = node_ids[-1]
        result = navigator.find_path(start, end)
