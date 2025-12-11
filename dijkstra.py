import pandas as pd
import heapq
import json

class DijkstraNavigator:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.coords = {}
        
    def load_nodes(self, nodes_csv):
        df = pd.read_csv(nodes_csv, encoding='utf-8-sig')
        for _, row in df.iterrows():
            node_id = int(row['node_id'])
            self.nodes[node_id] = row['name']
            self.coords[node_id] = (float(row['longitude']), float(row['latitude']))
            self.edges[node_id] = {}
        print(f"加载了 {len(self.nodes)} 个节点")
        return self
    
    def load_edges(self, edges_csv):
        df = pd.read_csv(edges_csv, encoding='utf-8-sig')
        for _, row in df.iterrows():
            if 'node1' in df.columns and 'node2' in df.columns:
                from_id = int(row['node1'])
                to_id = int(row['node2'])
            else:
                from_id = int(row.iloc[0])
                to_id = int(row.iloc[1])
            
            if 'distance' in df.columns:
                dist = float(row['distance'])
            else:
                dist = float(row.iloc[2])
            
            self.edges[from_id][to_id] = dist
            self.edges[to_id][from_id] = dist
        
        print(f"加载了 {len(df)} 条边")
        return self
    
    def find_path(self, start, end):
        import time
        start_time = time.time()
        
        if start not in self.nodes or end not in self.nodes:
            return {'success': False, 'error': '节点不存在'}
        
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        previous = {node: None for node in self.nodes}
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == end:
                break
            
            for neighbor, weight in self.edges[current].items():
                if neighbor in visited:
                    continue
                    
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        exec_time = (time.time() - start_time) * 1000
        
        if distances[end] == float('inf'):
            return {'success': False, 'error': '路径不存在'}
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        coords_path = []
        for node_id in path:
            lon, lat = self.coords[node_id]
            coords_path.append([lat, lon])
        
        curved_path = self._make_curve(coords_path) if len(coords_path) > 2 else coords_path
        
        return {
            'success': True,
            'algorithm': 'Dijkstra',
            'path': path,
            'path_names': [self.nodes[node_id] for node_id in path],
            'distance': round(distances[end], 2),
            'execution_time': round(exec_time, 2),
            'path_coords': coords_path,
            'curved_path': curved_path,
            'node_count': len(path),
            'nodes_explored': len(visited)
        }
    
    def _make_curve(self, straight_path):
        if len(straight_path) < 3:
            return straight_path
        
        curved = []
        for i in range(len(straight_path) - 1):
            p1 = straight_path[i]
            p2 = straight_path[i + 1]
            
            if i == 0:
                curved.append(p1)
            
            mid = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]
            offset = 0.00005
            if i % 2 == 0:
                curved.append([mid[0] + offset, mid[1]])
            else:
                curved.append([mid[0], mid[1] + offset])
            
            if i == len(straight_path) - 2:
                curved.append(p2)
        
        return curved

nav = DijkstraNavigator()

def init_dijkstra(nodes_csv, edges_csv):
    nav.load_nodes(nodes_csv).load_edges(edges_csv)
    return nav

def find_path(start, end):
    return nav.find_path(start, end)