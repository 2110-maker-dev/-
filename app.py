from flask import Flask, request, jsonify
import pandas as pd
import json
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from Astar import get_graph, run_astar
    from dijkstra import init_dijkstra, dijkstra_find_path
    ALGO_OK = True
except ImportError:
    ALGO_OK = False

app = Flask(__name__)

NODES = 'map_nodes.csv'
EDGES = 'distance_final.csv'

astar_g = None
dijkstra_g = None
nodes = []

# 后端（周永婷）：加载节点和边数据，初始化算法图结构
def init_data():
    global astar_g, dijkstra_g, nodes
    
    try:
        if os.path.exists(NODES):
            df = pd.read_csv(NODES, encoding='utf-8-sig')
            nodes = []
            for _, row in df.iterrows():
                nodes.append({
                    'id': int(row['node_id']),
                    'name': str(row['name']),
                    'lon': float(row['longitude']),
                    'lat': float(row['latitude']),
                    'address': str(row.get('address', ''))
                })
        else:
            return False
        
        if ALGO_OK and os.path.exists(EDGES):
            try:
                astar_g = get_graph(NODES, EDGES)
            except:
                astar_g = None
        
        if ALGO_OK and os.path.exists(EDGES):
            try:
                dijkstra_g = init_dijkstra(NODES, EDGES)
            except:
                dijkstra_g = None
        
        return True
        
    except:
        return False

# 后端（周永婷）：主页路由，返回HTML界面
@app.route('/')
def index():
    try:
        if not nodes:
            init_data()
        
        opts = ""
        for node in nodes:
            opts += f'<option value="{node["id"]}">{node["id"]}: {node["name"]}</option>'
        
        # 前端（林绮岚）：HTML界面，只包括地图显示、节点标记
        #后端（周永婷）：选择算法、路径显示、结果显示等功能
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>云南大学校园导航</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }}
                body {{ 
                    background: #f5f5f5; 
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }}
                .header {{
                    background: linear-gradient(to right, #2c3e50, #3498db);
                    color: white;
                    padding: 15px 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header h1 {{
                    font-size: 24px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .container {{
                    display: flex;
                    flex: 1;
                    height: calc(100vh - 70px);
                }}
                .sidebar {{
                    width: 350px;
                    background: white;
                    padding: 20px;
                    overflow-y: auto;
                    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                }}
                .map-container {{
                    flex: 1;
                    position: relative;
                }}
                #map {{
                    width: 100%;
                    height: 100%;
                }}
                .panel {{
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    border: 1px solid #ddd;
                }}
                .panel h3 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #3498db;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    color: #34495e;
                    font-weight: bold;
                }}
                select {{
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    font-size: 14px;
                }}
                select:focus {{
                    outline: none;
                    border-color: #3498db;
                }}
                .btn-group {{
                    display: flex;
                    gap: 10px;
                    margin-top: 20px;
                }}
                button {{
                    flex: 1;
                    padding: 12px;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }}
                .btn-calc {{
                    background: #3498db;
                    color: white;
                }}
                .btn-calc:hover {{
                    background: #2980b9;
                }}
                .btn-clear {{
                    background: #95a5a6;
                    color: white;
                }}
                .btn-clear:hover {{
                    background: #7f8c8d;
                }}
                .result-box {{
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 20px;
                    border-left: 4px solid #3498db;
                }}
                .algo-select {{
                    display: flex;
                    background: #ecf0f1;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }}
                .algo-btn {{
                    flex: 1;
                    padding: 10px;
                    text-align: center;
                    cursor: pointer;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                .algo-btn.active {{
                    background: #3498db;
                    color: white;
                }}
                .loading {{
                    display: none;
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.2);
                    text-align: center;
                    z-index: 1000;
                }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 10px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .map-legend {{
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background: white;
                    padding: 12px;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    font-size: 13px;
                    line-height: 1.8;
                }}
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #2c3e50;
                }}
                .status {{
                    padding: 10px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                    font-size: 12px;
                }}
                .status.success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1><i class="fas fa-map-marker-alt"></i> 云南大学校园导航系统</h1>
            </div>
            
            <div class="container">
                <div class="sidebar">
                    <div class="status success">
                        ✅ 系统已加载 {len(nodes)} 个校园地点
                    </div>
                    
                    <div class="panel">
                        <h3><i class="fas fa-route"></i> 路径规划</h3>
                        
                        <div class="form-group">
                            <label><i class="fas fa-map-pin"></i> 起点</label>
                            <select id="startNode">
                                <option value="">选择起点</option>
                                {opts}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label><i class="fas fa-flag"></i> 终点</label>
                            <select id="endNode">
                                <option value="">选择终点</option>
                                {opts}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label><i class="fas fa-code-branch"></i> 选择算法</label>
                            <div class="algo-select">
                                <div class="algo-btn active" data-algo="astar">A*算法</div>
                                <div class="algo-btn" data-algo="dijkstra">Dijkstra算法</div>
                            </div>
                        </div>
                        
                        <div class="btn-group">
                            <button class="btn-calc" onclick="calcPath()">
                                <i class="fas fa-calculator"></i> 计算路径
                            </button>
                            <button class="btn-clear" onclick="clearMap()">
                                <i class="fas fa-trash"></i> 清除
                            </button>
                        </div>
                    </div>
                    
                    <div id="resultBox" class="result-box" style="display: none;">
                        <h3><i class="fas fa-info-circle"></i> 计算结果</h3>
                        <div id="resultContent"></div>
                    </div>
                </div>
                
                <div class="map-container">
                    <div id="map"></div>
                    <div class="map-legend">
                        <div class="legend-title">图例</div>
                        <div><span style="color: #e74c3c;">●</span> 起点</div>
                        <div><span style="color: #27ae60;">●</span> 终点</div>
                        <div><span style="color: #3498db;">━━</span> 路径</div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>正在计算路径...</p>
            </div>
            
            <script>
                // 前端（林绮岚）：初始化地图和节点显示
                var map = L.map('map').setView([24.83, 102.85], 16);
                L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}', {{
                    attribution: '高德地图',
                    maxZoom: 19
                }}).addTo(map);
                
                var nodes = {json.dumps([{"id": n["id"], "name": n["name"], "lat": n["lat"], "lon": n["lon"]} for n in nodes])};
                
                var markers = L.layerGroup().addTo(map);
                var pathLayer = L.layerGroup().addTo(map);
                var algo = 'astar';
                
                function addMarkers() {{
                    markers.clearLayers();
                    nodes.forEach(function(node) {{
                        var marker = L.circleMarker([node.lat, node.lon], {{
                            radius: 6,
                            fillColor: '#3498db',
                            color: '#2c3e50',
                            weight: 1,
                            opacity: 0.8,
                            fillOpacity: 0.6
                        }}).bindPopup(`<strong>${{node.name}}</strong><br>ID: ${{node.id}}`);
                        markers.addLayer(marker);
                    }});
                }}
                
                // 前端（林绮岚）：算法切换功能
                document.querySelectorAll('.algo-btn').forEach(btn => {{
                    btn.addEventListener('click', function() {{
                        document.querySelectorAll('.algo-btn').forEach(b => b.classList.remove('active'));
                        this.classList.add('active');
                        algo = this.dataset.algo;
                    }});
                }});
                
                // 前端（林绮岚）：路径计算请求功能
                function calcPath() {{
                    var start = document.getElementById('startNode').value;
                    var end = document.getElementById('endNode').value;
                    
                    if (!start || !end) {{
                        alert('请选择起点和终点！');
                        return;
                    }}
                    
                    if (start == end) {{
                        alert('起点和终点不能相同！');
                        return;
                    }}
                    
                    document.getElementById('loading').style.display = 'block';
                    pathLayer.clearLayers();
                    
                    fetch('/calc', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            start: parseInt(start),
                            end: parseInt(end),
                            algo: algo
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('loading').style.display = 'none';
                        if (data.ok) {{
                            showResult(data);
                            drawPath(data);
                        }} else {{
                            alert('计算失败:' + (data.error || '未知错误'));
                        }}
                    }})
                    .catch(error => {{
                        document.getElementById('loading').style.display = 'none';
                        alert('请求失败:' + error.message);
                    }});
                }}
                
                // 前端（林绮岚）：结果显示功能
                function showResult(data) {{
                    var algoName = algo === 'astar' ? 'A*算法' : 'Dijkstra算法';
                    var color = algo === 'astar' ? '#e74c3c' : '#3498db';
                    var html = `
                        <div style="margin-bottom: 15px; padding: 10px; background: ${{color}}; color: white; border-radius: 5px; text-align: center;">
                            <strong>${{algoName}}</strong>
                        </div>
                        <p><strong>起点:</strong> ${{data.start_name}}</p>
                        <p><strong>终点:</strong> ${{data.end_name}}</p>
                        <p><strong>总距离:</strong> <span style="color: #27ae60; font-weight: bold;">${{data.dist}} 米</span></p>
                        <p><strong>计算时间:</strong> ${{data.time}} 毫秒</p>
                        <p><strong>访问节点数:</strong> ${{data.visited}} 个</p>
                    `;
                    
                    document.getElementById('resultContent').innerHTML = html;
                    document.getElementById('resultBox').style.display = 'block';
                }}
                
                // 前端（林绮岚）：路径绘制功能
                function drawPath(data) {{
                    var coords = data.coords;
                    var color = algo === 'astar' ? '#e74c3c' : '#3498db';
                    
                    var startNode = nodes.find(n => n.id == data.start_id);
                    var endNode = nodes.find(n => n.id == data.end_id);
                    
                    if (coords && coords.length > 1 && startNode && endNode) {{
                        var fullPath = [[startNode.lat, startNode.lon], ...coords, [endNode.lat, endNode.lon]];
                        
                        var line = L.polyline(fullPath, {{
                            color: color,
                            weight: 3,
                            opacity: 0.7,
                            lineCap: 'round',
                            lineJoin: 'round'
                        }}).bindPopup(`
                            <div style="padding: 10px;">
                                <strong>${{algo === 'astar' ? 'A*算法' : 'Dijkstra算法'}}</strong><br>
                                距离: ${{data.dist}}米<br>
                                访问节点: ${{data.visited}}个
                            </div>
                        `);
                        pathLayer.addLayer(line);
                        var bounds = line.getBounds();
                        map.fitBounds(bounds, {{ padding: [50, 50] }});
                    }}
                    
                    if (startNode) {{
                        L.circleMarker([startNode.lat, startNode.lon], {{
                            radius: 7,
                            color: '#e74c3c',
                            fillColor: '#e74c3c',
                            fillOpacity: 0.9,
                            weight: 2
                        }}).addTo(pathLayer);
                    }}
                    
                    if (endNode) {{
                        L.circleMarker([endNode.lat, endNode.lon], {{
                            radius: 7,
                            color: '#27ae60',
                            fillColor: '#27ae60',
                            fillOpacity: 0.9,
                            weight: 2
                        }}).addTo(pathLayer);
                    }}
                }}
                
                // 前端（林绮岚）：清除地图功能
                function clearMap() {{
                    pathLayer.clearLayers();
                    addMarkers();
                    document.getElementById('resultBox').style.display = 'none';
                }}
                
                window.onload = function() {{
                    addMarkers();
                }};
            </script>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f"<h1>错误</h1><p>页面渲染失败:{str(e)}</p>"

# 后端（周永婷）：路径计算接口，调用A*或Dijkstra算法
@app.route('/calc', methods=['POST'])
def calc():
    try:
        data = request.json
        start_id = int(data['start'])
        end_id = int(data['end'])
        algo_type = data['algo']
        
        start_node = next((n for n in nodes if n['id'] == start_id), None)
        end_node = next((n for n in nodes if n['id'] == end_id), None)
        
        if not start_node or not end_node:
            return jsonify({'ok': False, 'error': '节点不存在'})
        
        t0 = time.time()
        result = None
        visited = 0
        
        if algo_type == 'astar' and astar_g:
            try:
                res = run_astar(start_id, end_id, astar_g)
                if res and res.get('path') is not None:
                    result = res
                    visited = res.get('visited_nodes', 0)
            except:
                pass
        
        elif algo_type == 'dijkstra' and dijkstra_g:
            try:
                res = dijkstra_find_path(dijkstra_g, start_id, end_id)
                if res and res.get('path') is not None:
                    result = res
                    visited = res.get('visited_nodes', 0)
            except:
                pass
        
        exec_time = (time.time() - t0) * 1000
        
        if not result or result.get('path') is None:
            return jsonify({'ok': False, 'error': f'未找到从节点{start_id}到节点{end_id}的路径'})
        
        if not result.get('path_coords'):
            return jsonify({'ok': False, 'error': '路径坐标为空'})
        
        return jsonify({
            'ok': True,
            'algo': algo_type,
            'start_id': start_id,
            'end_id': end_id,
            'start_name': start_node['name'],
            'end_name': end_node['name'],
            'dist': result.get('distance'),
            'time': round(exec_time, 2),
            'visited': visited,
            'coords': result.get('path_coords', [])
        })
        
    except:
        return jsonify({'ok': False, 'error': '计算错误'})

if __name__ == '__main__':
    init_data()
    app.run(debug=True, host='0.0.0.0', port=5000)