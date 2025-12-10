""" 代码的主要功能：
    使用高德地图API搜索指定关键词的地点(POI)，去除重复以及校外地点。
"""
import requests
import csv
import json
import time
from typing import List, Dict, Optional

class AmapPOI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/place/text"
        self.ress = []

    def search(self, keywords: str, city: str = "昆明", types: str = "", offset: int = 20, page: int = 1, extensions: str = "all") -> Optional[Dict]:
        #构造请求参数字典
        params = {
            'key': self.api_key,
            'keywords': keywords,
            'city': city,
            'offset': offset,
            'page': page,
            'extensions': extensions,
            'output': 'json'
        }
        #如果给定类型则加入参数
        if types:
            params['types'] = types

        try:
            rsp = requests.get(self.base_url, params=params, timeout=10)
            rsp.raise_for_status()
            data = rsp.json()
            #判断API返回是否成功
            if data.get('status') == '1':
                return data
            else:
                return None

        except requests.exceptions.RequestException:
            #捕获网络异常后返回None
            return None

    def search_kw(self, keyword_list: List[str], city: str = "昆明", delay: float = 0.5) -> List[Dict]:
    #云大呈贡校区大致坐标范围
        MIN_LON = 102.840  
        MAX_LON = 102.855  
        MIN_LAT = 24.820   
        MAX_LAT = 24.835 
    
        all_ress = []
        seen_ids = set()

        for kw in keyword_list:
            res = self.search(kw, city=city)

            if res and 'pois' in res:
                pois = res['pois']
                for poi in pois:
                    poi_id = poi.get('id', '')
                    if poi_id and poi_id in seen_ids:
                        continue
                #提取坐标
                    location = poi.get('location', ',').split(',')
                    if len(location) < 2:
                        continue
                    try:
                        lon = float(location[0])
                        lat = float(location[1])
                    #检查是否在校园范围内
                        if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
                            continue  #跳过校外地点
                    except ValueError:
                        continue
                    poi_data = self._ext_data(poi)
                    all_ress.append(poi_data)
                
                    if poi_id:
                        seen_ids.add(poi_id)
            time.sleep(delay)
        self.ress = all_ress
        return all_ress

    def _ext_data(self, poi: Dict) -> Dict:
        #解析经纬度字符串
        location = poi.get('location', ',').split(',')
        return {
            'name': poi.get('name', ''),
            'address': poi.get('address', ''),
            'longitude': location[0] if len(location) > 0 else '',
            'latitude': location[1] if len(location) > 1 else '',
        }

    def savef(self, filename: str = 'map_nodes.csv'):
        #若无结果则直接返回
        if not self.ress:
            return

        fieldnames = ['name', 'address', 'longitude', 'latitude']
        #写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.ress)

def main():
        API_KEY = "d12ddcf8aa0f9fb2489a3115d299fa42"

        #定义需要搜索的关键词列表
        keywords_list = [
            "云南大学呈贡校区 图书馆",
            "云南大学呈贡校区 行政楼",
            "云南大学呈贡校区 体育馆",
            "云南大学呈贡校区 教学楼",
            "云南大学呈贡校区 实验楼",
            "云南大学呈贡校区 梓苑",
            "云南大学呈贡校区 桦苑",
            "云南大学呈贡校区 楠苑",
            "云南大学呈贡校区 楸苑",
            "云南大学呈贡校区 食堂",
            "云南大学呈贡校区 超市",
            "云南大学呈贡校区 操场",
            "云南大学呈贡校区 校医院",
            "云南大学呈贡校区 南门",
            "云南大学呈贡校区 北门",
            "云南大学呈贡校区 东门",
            "云南大学呈贡校区 西门",
        ]

        #创建搜索器对象
        searcher = AmapPOI(API_KEY)
        #执行批量搜索
        ress = searcher.search_kw(keywords_list, city="昆明")
        output_filename = 'map_nodes.csv'
        searcher.savef(output_filename)

if __name__ == "__main__":
    main()