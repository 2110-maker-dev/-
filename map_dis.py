""" 代码的主要功能：
     - 读取修改后的map_nodes（节点列表）来构造图的边列表distance_final.csv
     - 使用高德地图API获取步行路径点，若API不可用则仅计算直线距离
"""
import requests
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import time

class DistanceCp:
    EARTH_RADIUS = 6371000
    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        #将经纬度转为弧度
        lon1_r, lat1_r, lon2_r, lat2_r = map(radians, [lon1, lat1, lon2, lat2])
        
        #计算经度差与纬度差
        dlon = lon2_r - lon1_r
        dlat = lat2_r - lat1_r
        
        #haversine公式中的 a
        a = sin(dlat/2)**2 + cos(lat1_r) * cos(lat2_r) * sin(dlon/2)**2
        
        #haversine公式中的 c
        c = 2 * asin(sqrt(a))
        return c * DistanceCp.EARTH_RADIUS

#高德路径查询封装类
class GDDT:
    API_URL = "https://restapi.amap.com/v3/direction/walking"
    
    def __init__(self, key):
        self.key = key
        
    def get_path(self, lon1, lat1, lon2, lat2):
        #构造请求参数
        params = {
            'key': self.key, 'origin': f"{lon1},{lat1}", 'destination': f"{lon2},{lat2}"}
        
        try:
            #发送GET请求,设置超时
            response = requests.get(self.API_URL, params=params, timeout=5)
            data = response.json()
            
            #检查响应是否成功并含有路线
            if data['status'] == '1' and 'route' in data:
                paths = data['route']['paths'][0]
                steps = paths['steps']
                
                coords = []
                #遍历每个步骤,提取经纬度点
                for step in steps:
                    polyline = step['polyline']
                    points = polyline.split(';')
                    
                    for point in points:
                        lon, lat = map(float, point.split(','))
                        coords.append([lon, lat])
                
                #为避免短时间过多请求,短暂休眠
                time.sleep(0.15)
                return coords
            else:
                #无有效路径时返回None
                return None
                
        except Exception:
            return None

#图构造类,基于节点生成边
class GraphB:
    def __init__(self, nodes_df, api_client=None):
        #节点数据(DataFrame)
        self.nodes = nodes_df
        self.n = len(nodes_df)
        self.api = api_client
        self.edges = []
        
    def build(self):
        #计算总共需要处理的无向边数量
        total = self.n * (self.n - 1) // 2
        count = 0
        
        #双重循环只枚举i < j的组合
        for i in range(self.n):
            node_i = self.nodes.iloc[i]
            
            for j in range(i + 1, self.n):
                node_j = self.nodes.iloc[j]
                count += 1
                
                #计算两点直线球面距离
                dist = DistanceCp.haversine(
                    node_i['longitude'], node_i['latitude'],
                    node_j['longitude'], node_j['latitude']
                )
                
                waypts = None
                #API_KEY还有效的情况下，可获取步行路径
                if self.api:
                    waypts = self.api.get_path(
                        node_i['longitude'], node_i['latitude'],
                        node_j['longitude'], node_j['latitude']
                    )
                
                waypts_str = None
                #若路径点足够，则取内部中间点拼接为字符串
                if waypts and len(waypts) > 2:
                    middle = waypts[1:-1]
                    waypts_str = ';'.join([f"{w[0]},{w[1]}" for w in middle])
                
                #构造边字典，包含节点与距离
                edge = {
                    'node1': node_i['node_id'],
                    'node2': node_j['node_id'],
                    'distance': round(dist, 2)
                }
                
                if waypts_str:
                    edge['waypoints'] = waypts_str
                
                self.edges.append(edge)
        return pd.DataFrame(self.edges)

class SaveF:
    @staticmethod
    def save_nodes(df, filename='map_nodes.csv'):
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
    @staticmethod
    def save_edges(df, filename='distance_final.csv'):
        df.to_csv(filename, index=False, encoding='utf-8-sig')

def main():
    #我的API KEY
    KEY = "d12ddcf8aa0f9fb2489a3115d299fa42"
    
    #读取修改后的节点
    input_file = 'map_nodes.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    #过滤掉缺失经纬度的行
    valid = df[df['longitude'].notna() & df['latitude'].notna()].copy()
    valid = valid.reset_index(drop=True)
    
    valid['node_id'] = range(len(valid))
    api = GDDT(KEY)

    #根据节点与API初始化图构造器
    builder = GraphB(valid, api)
    
    #构建边并返回DataFrame
    edges_df = builder.build()
    output = valid[['node_id', 'name', 'longitude', 'latitude', 'address']]
    
    SaveF.save_nodes(output, 'map_nodes.csv')
    SaveF.save_edges(edges_df)

if __name__ == "__main__":
    main()