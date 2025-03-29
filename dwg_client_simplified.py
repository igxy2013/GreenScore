import requests
import base64
import os
import logging
import json
import platform
import socket
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查是否在WSL环境中
IS_WSL = 'WSL' in platform.uname().release or \
         (os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower())

def get_service_host_ip():
    """获取DWG服务主机IP地址"""
    # 非WSL环境直接返回本地地址
    if not IS_WSL:
        return '127.0.0.1'
    
    # 从环境变量获取
    host_ip = os.environ.get('DWG_HOST_IP')
    if host_ip:
        logger.info(f"使用环境变量指定的主机IP: {host_ip}")
        return host_ip
    
    try:
        # 方法1: 查找192.168网段的IP
        import subprocess
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '192.168.' in line and 'via' in line:
                    parts = line.split()
                    via_index = parts.index('via') if 'via' in parts else -1
                    if via_index >= 0 and via_index + 1 < len(parts):
                        host_ip = parts[via_index + 1]
                        logger.info(f"通过ip route获取到主机IP: {host_ip}")
                        return host_ip
        
        # 方法2: 使用Docker特殊主机名
        try:
            host_ip = socket.gethostbyname('host.docker.internal')
            logger.info(f"通过host.docker.internal获取到主机IP: {host_ip}")
            return host_ip
        except:
            pass
        
        # 方法3: 读取/etc/resolv.conf
        if os.path.exists('/etc/resolv.conf'):
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        parts = line.strip().split()
                        if len(parts) > 1:
                            host_ip = parts[1]
                            # 跳过已知的错误IP
                            if host_ip not in ['127.0.0.1', '10.255.255.254']:
                                logger.info(f"从/etc/resolv.conf获取到主机IP: {host_ip}")
                                return host_ip
        
        # 默认IP地址
        default_ip = '192.168.0.80'
        logger.info(f"未能自动获取主机IP，使用默认IP: {default_ip}")
        return default_ip
        
    except Exception as e:
        logger.error(f"获取主机IP失败: {str(e)}")
        return '192.168.0.80'  # 出错时返回默认IP

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        # 记录当前环境
        self.is_wsl = IS_WSL
        
        # 确定API URL
        if api_url:
            self.api_url = api_url
        else:
            env_service_url = os.environ.get('DWG_SERVICE_URL')
            if env_service_url:
                self.api_url = env_service_url
            else:
                service_ip = get_service_host_ip()
                self.api_url = f'http://{service_ip}:5001'
                
        # API密钥和请求设置
        self.api_key = api_key or os.environ.get('DWG_SERVICE_KEY', '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85')
        self.timeout = int(os.environ.get('DWG_REQUEST_TIMEOUT', '120'))
        self.max_retries = int(os.environ.get('DWG_MAX_RETRIES', '3'))
        
        logger.info(f"DWG服务客户端初始化，API地址: {self.api_url}")
    
    def check_health(self):
        """检查DWG服务健康状态"""
        # 非WSL环境使用本地地址时，跳过远程检查
        if not self.is_wsl and '127.0.0.1' in self.api_url:
            return True, {"status": "ok", "service": "dwg-service", "version": "local"}
        
        try:
            url = f"{self.api_url}/api/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"message": f"健康检查失败，状态码: {response.status_code}"}
                
        except Exception as e:
            return False, {"message": f"健康检查出错: {str(e)}"}
    
    def update_dwg_attributes(self, template_file, attribute_data):
        """更新DWG文件属性"""
        # 非WSL环境不使用远程服务
        if not self.is_wsl:
            logger.info("非WSL环境，应直接使用本地AutoCAD处理DWG文件")
            return False, {'message': '非WSL环境，请使用本地AutoCAD处理DWG文件'}
        
        url = f"{self.api_url}/api/dwg/update"
        headers = {'X-API-KEY': self.api_key}
        file_obj = None
        
        try:
            # 准备文件
            if isinstance(template_file, str):
                if not os.path.exists(template_file):
                    return False, {'message': f"模板文件不存在: {template_file}"}
                file_obj = open(template_file, 'rb')
                files = {'file': file_obj}
            else:
                files = {'file': template_file}
            
            # 准备数据
            data_json = json.dumps(attribute_data)
            data = {'data': data_json}
            
            # 发送请求
            for attempt in range(self.max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"第 {attempt} 次重试...")
                        import time
                        time.sleep(2)  # 重试前等待
                    
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
                    
                    # 检查响应
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('success', False):
                            # 提取文件数据
                            file_data = result.get('file_data', '')
                            if not file_data:
                                return False, {'message': "服务器响应中缺少文件数据"}
                            
                            # 解码Base64数据
                            if isinstance(file_data, str):
                                try:
                                    file_data = base64.b64decode(file_data)
                                except Exception as e:
                                    return False, {'message': f"文件数据格式错误: {str(e)}"}
                            
                            # 返回成功结果
                            return True, {
                                'message': result.get('message', '更新成功'),
                                'filename': result.get('filename', 'output.dwg'),
                                'file_data': file_data
                            }
                        else:
                            error_msg = result.get('message', '未知错误')
                            return False, {'message': error_msg}
                    else:
                        # 服务器错误时重试
                        if response.status_code >= 500 and attempt < self.max_retries:
                            continue
                        try:
                            error_info = response.json()
                            error_msg = error_info.get('message', error_info.get('error', f"请求失败，状态码: {response.status_code}"))
                        except:
                            error_msg = f"请求失败，状态码: {response.status_code}"
                        return False, {'message': error_msg}
                
                except requests.exceptions.RequestException as e:
                    if attempt < self.max_retries:
                        continue
                    return False, {'message': f"请求DWG服务失败: {str(e)}"}
                
                except Exception as e:
                    if attempt < self.max_retries:
                        continue
                    return False, {'message': f"处理请求时出错: {str(e)}"}
            
            return False, {'message': "超过最大重试次数"}
            
        except Exception as e:
            return False, {'message': f"调用DWG服务出错: {str(e)}"}
            
        finally:
            if file_obj:
                file_obj.close()

# 创建默认客户端实例
dwg_client = DwgServiceClient() 