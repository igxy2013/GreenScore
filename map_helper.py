import os
import traceback
from flask import request, jsonify, Response

# 确保能访问app对象，需要通过参数传入而不是直接导入
def init_routes(app):
    """初始化地图相关的路由，将app对象作为参数传入"""
    # 给app添加全局变量access
    global logger
    logger = app.logger
    
    # 添加获取真实海拔数据的API端点
    def get_elevation():
        try:
            lat = request.args.get('lat')
            lng = request.args.get('lng')
            
            if not lat or not lng:
                return jsonify({'error': '缺少经纬度参数'}), 400
            
            # 调用Open-Elevation API获取真实海拔数据
            import requests
            
            # 使用Open-Elevation公共API
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lng}"
            
            logger.info(f"请求Open-Elevation API: {url}")
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'results' in data and len(data['results']) > 0:
                    elevation = data['results'][0]['elevation']
                    logger.info(f"获取到海拔数据: {elevation}米")
                    return jsonify({'elevation': elevation})
            
            # 如果Open-Elevation失败，尝试其他免费海拔API
            backup_url = f"https://elevation-api.io/api/elevation?points=({lat},{lng})"
            logger.info(f"请求备用海拔API: {backup_url}")
            
            backup_response = requests.get(backup_url, timeout=5)
            if backup_response.status_code == 200:
                backup_data = backup_response.json()
                if backup_data and 'elevations' in backup_data and len(backup_data['elevations']) > 0:
                    elevation = backup_data['elevations'][0]['elevation']
                    logger.info(f"从备用API获取到海拔数据: {elevation}米")
                    return jsonify({'elevation': elevation})
            
            # 如果所有API都失败，使用SRTM数据集（如果可用）
            try:
                from srtm import get_data
                srtm_data = get_data()
                elevation = srtm_data.get_elevation(float(lat), float(lng))
                if elevation is not None:
                    logger.info(f"从SRTM数据集获取到海拔数据: {elevation}米")
                    return jsonify({'elevation': elevation})
            except Exception as srtm_error:
                logger.error(f"SRTM数据获取失败: {str(srtm_error)}")
            
            # 所有方法都失败
            return jsonify({'error': '无法获取海拔数据'}), 500
        except Exception as e:
            logger.error(f"获取海拔数据时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500

    def get_google_elevation():
        try:
            lat = request.args.get('lat')
            lng = request.args.get('lng')
            
            if not lat or not lng:
                return jsonify({'error': '缺少经纬度参数'}), 400
            
            # 从环境变量获取Google Maps API密钥
            api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            
            if not api_key:
                return jsonify({'error': '未配置Google Maps API密钥'}), 500
            
            # 调用Google Maps Elevation API
            import requests
            
            url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lng}&key={api_key}"
            
            logger.info(f"请求Google Elevation API")
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and len(data['results']) > 0:
                    elevation = data['results'][0]['elevation']
                    logger.info(f"从Google API获取到海拔数据: {elevation}米")
                    return jsonify({'elevation': elevation})
            
            return jsonify({'error': '无法从Google获取海拔数据'}), 500
        except Exception as e:
            logger.error(f"获取Google海拔数据时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500

    # 获取百度地图API密钥的API端点
    def get_map_api_key():
        try:
            # 从环境变量获取百度地图API密钥
            api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')  # 使用环境变量中的密钥，提供一个默认值
            
            # 返回API密钥
            return jsonify({'api_key': api_key})
        except Exception as e:
            logger.error(f"获取地图API密钥时出错: {str(e)}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500

    # 获取高德地图API密钥的API端点
    def get_gaode_map_api_key():
        try:
            # 从环境变量获取高德地图API密钥和安全密钥
            api_key = os.environ.get('GAODE_MAP_AK')
            security_js_code = os.environ.get('GAODE_MAP_SEC_CODE')
            
            if not api_key or not security_js_code:
                return jsonify({'error': '高德地图API密钥未配置'}), 500
            
            # 返回API密钥和安全密钥
            return jsonify({
                'api_key': api_key,
                'security_js_code': security_js_code
            })
        except Exception as e:
            logger.error(f"获取高德地图API密钥时出错: {str(e)}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500

    # 百度地图API代理
    def map_api_proxy():
        try:
            logger.info(f"百度地图API代理请求: {request.url}")
            
            # 获取百度地图API密钥
            api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')
            
            # 获取所有请求参数
            params = request.args.to_dict()
            
            # 获取服务路径
            service_path = params.pop('service_path', 'api')
            
            # 判断是否是静态资源请求（图片等）
            is_static_resource = service_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js'))
            
            # 如果不是静态资源请求，则添加API密钥
            if not is_static_resource:
                params['ak'] = api_key
            
            # 构建百度地图API请求URL
            base_url = f"https://api.map.baidu.com/{service_path}"
            logger.info(f"代理到URL: {base_url}, 参数: {params}")
            
            # 发送请求
            import requests
            
            if request.method == 'GET':
                response = requests.get(base_url, params=params, timeout=10)
            else:  # POST请求
                post_data = request.get_data()
                headers = {'Content-Type': request.headers.get('Content-Type', 'application/x-www-form-urlencoded')}
                response = requests.post(base_url, params=params, data=post_data, headers=headers, timeout=10)
            
            # 根据不同的资源类型设置不同的Content-Type
            content_type = response.headers.get('Content-Type')
            if is_static_resource:
                if service_path.endswith('.png'):
                    content_type = 'image/png'
                elif service_path.endswith('.jpg') or service_path.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif service_path.endswith('.gif'):
                    content_type = 'image/gif'
                elif service_path.endswith('.css'):
                    content_type = 'text/css'
                elif service_path.endswith('.js'):
                    content_type = 'application/javascript'
            
            logger.info(f"代理响应状态码: {response.status_code}, Content-Type: {content_type}")
            
            # 返回百度地图API的响应
            return Response(
                response.content, 
                status=response.status_code,
                content_type=content_type or 'application/json'
            )
        except Exception as e:
            logger.error(f"百度地图API代理出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'代理请求失败: {str(e)}'}), 500

    # 百度地图JavaScript API代理
    def map_js_api_proxy():
        try:
            # 获取百度地图API密钥
            api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')
            
            # 获取请求参数
            params = request.args.to_dict()
            
            # 添加API密钥
            params['ak'] = api_key
            
            # 构建百度地图JavaScript API的URL
            url = "https://api.map.baidu.com/api"
            
            # 发送请求
            import requests
            response = requests.get(url, params=params, timeout=10)
            
            # 返回JavaScript内容
            return Response(
                response.content, 
                status=response.status_code,
                content_type='application/javascript'
            )
        except Exception as e:
            logger.error(f"百度地图JavaScript API代理出错: {str(e)}")
            return Response(
                f"console.error('加载地图API失败: {str(e)}');", 
                status=500,
                content_type='application/javascript'
            )

    # 代理百度静态地图API请求
    def get_static_map_proxy():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing request body'}), 400

            width = data.get('width')
            height = data.get('height')
            center_lng = data.get('center_lng')
            center_lat = data.get('center_lat')
            zoom = data.get('zoom')
            markers_param = data.get('markers', '') # 获取前端处理好的标记字符串

            if not all([width, height, center_lng, center_lat, zoom]):
                return jsonify({'error': 'Missing required parameters'}), 400

            # 从环境变量获取百度地图API密钥
            api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')

            # 构建百度静态地图API URL
            baidu_url = f"https://api.map.baidu.com/staticimage/v2"
            params = {
                'ak': api_key,
                'width': width,
                'height': height,
                'center': f"{center_lng},{center_lat}",
                'zoom': zoom,
                'copyright': 1,
                # 移除markers参数，避免与前端Canvas绘制的标记点重复
                # 注意：百度静态地图API可能无法完美渲染所有自定义标记和圆圈，这里仅传递基础信息
            }
            
            logger.info(f"代理请求百度静态地图: {baidu_url} with params: {params}")

            # 发送请求到百度服务器
            import requests
            response = requests.get(baidu_url, params=params, timeout=15, stream=True) # 使用stream=True处理图片

            # 检查百度服务器的响应
            if response.status_code == 200:
                # 获取 Content-Type，如果百度返回了的话
                content_type = response.headers.get('Content-Type', 'image/png') 
                # 返回图片数据
                return Response(response.content, status=200, content_type=content_type)
            else:
                logger.error(f"请求百度静态地图失败: Status {response.status_code}, Response: {response.text[:200]}")
                return jsonify({'error': f'Failed to fetch map image from Baidu: Status {response.status_code}'}), response.status_code

        except Exception as e:
            logger.error(f"代理百度静态地图时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Server error during map proxy: {str(e)}'}), 500
            
    # 注册路由
    app.add_url_rule('/api/elevation', view_func=get_elevation, methods=['GET'])
    app.add_url_rule('/api/google_elevation', view_func=get_google_elevation, methods=['GET'])
    app.add_url_rule('/api/map_api_key', view_func=get_map_api_key, methods=['GET'])
    app.add_url_rule('/api/gaode_map_api_key', view_func=get_gaode_map_api_key, methods=['GET'])
    app.add_url_rule('/api/map_proxy', view_func=map_api_proxy, methods=['GET', 'POST'])
    app.add_url_rule('/api/map_js_api', view_func=map_js_api_proxy, methods=['GET'])
    app.add_url_rule('/api/get_static_map', view_func=get_static_map_proxy, methods=['POST'])
    
    # 返回注册的路由函数，以便在需要时可以单独访问
    return {
        'get_elevation': get_elevation,
        'get_google_elevation': get_google_elevation,
        'get_map_api_key': get_map_api_key,
        'get_gaode_map_api_key': get_gaode_map_api_key,
        'map_api_proxy': map_api_proxy,
        'map_js_api_proxy': map_js_api_proxy,
        'get_static_map_proxy': get_static_map_proxy
    }