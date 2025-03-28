import requests
import base64
import os
import logging
import json
from flask import current_app
import platform
import socket

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查是否在WSL环境中
IS_WSL = 'WSL' in platform.uname().release or \
         (os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower())

# 获取服务主机IP
def get_service_host_ip():
    try:
        # 如果在WSL环境中，尝试获取Windows主机IP
        if IS_WSL:
            # 方法1：尝试读取/etc/resolv.conf获取WSL DNS服务器IP（通常是Windows主机IP）
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        return line.split()[1]
            
            # 方法2：尝试使用host.docker.internal域名
            try:
                return socket.gethostbyname('host.docker.internal')
            except socket.gaierror:
                pass
            
            # 方法3：尝试使用默认网关IP
            return '172.17.0.1'  # 常见的Docker默认网关IP
        else:
            # 在Windows环境中，直接使用localhost
            return 'localhost'
    except Exception as e:
        logger.error(f"获取主机IP失败: {str(e)}")
        return 'localhost'

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        # 根据环境选择合适的服务地址
        service_ip = get_service_host_ip()
        self.api_url = api_url or os.environ.get('DWG_SERVICE_URL', f'http://{service_ip}:5001')
        self.api_key = api_key or os.environ.get('DWG_SERVICE_KEY', '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85')
        self.timeout = 120  # 设置超时时间为120秒
        logger.info(f"DWG服务客户端初始化，API地址: {self.api_url}")
        
    def update_dwg_attributes(self, template_file, attribute_data):
        """
        通过API更新DWG文件属性
        
        Args:
            template_file: DWG模板文件对象或路径
            attribute_data: 属性数据列表，如 [{'field': '项目名称', 'value': 'XX项目'}]
            
        Returns:
            (success, result): 成功状态和结果数据
        """
        try:
            # 记录调用信息
            logger.info(f"调用DWG服务更新属性，模板: {template_file}")
            logger.info(f"属性数据数量: {len(attribute_data)}")
            
            # 准备API请求
            url = f"{self.api_url}/api/dwg/update"
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            # 准备文件和数据
            if isinstance(template_file, str):
                # 如果是文件路径，则打开文件
                if not os.path.exists(template_file):
                    logger.error(f"模板文件不存在: {template_file}")
                    return False, {'message': f"模板文件不存在: {template_file}"}
                    
                logger.info(f"打开模板文件: {template_file}")
                files = {'template_file': open(template_file, 'rb')}
                close_file = True
            else:
                # 如果已经是文件对象
                logger.info("使用提供的文件对象")
                files = {'template_file': template_file}
                close_file = False
            
            # 序列化属性数据
            try:
                data_json = json.dumps(attribute_data)
                logger.info(f"属性数据已序列化，长度: {len(data_json)}")
            except Exception as e:
                logger.error(f"序列化属性数据失败: {str(e)}")
                return False, {'message': f"序列化属性数据失败: {str(e)}"}
                
            data = {'attributes': data_json}
            
            # 发送请求
            logger.info(f"发送DWG更新请求到: {url}")
            try:
                response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
                logger.info(f"收到服务器响应，状态码: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败: {str(e)}")
                return False, {'message': f"请求失败: {str(e)}"}
            finally:
                # 关闭文件（如果需要）
                if close_file:
                    files['template_file'].close()
                    logger.info("已关闭模板文件")
                
            # 处理响应
            try:
                result = response.json()
                logger.info(f"服务器返回JSON数据，状态码: {response.status_code}")
                
                # 即使是错误状态码，也尝试从JSON中获取有用信息
                success = result.get('success', False) if response.status_code == 200 else False
                message = result.get('message', f"请求失败，状态码: {response.status_code}") 
                
                if not success:
                    error_msg = result.get('error', message)
                    logger.error(f"DWG服务返回错误: {error_msg}")
                    return False, {'message': error_msg}
                    
                # 如果是成功状态，检查文件数据
                if 'file_data' not in result:
                    logger.error("响应中缺少文件数据")
                    return False, {'message': "服务器响应中缺少文件数据"}
                    
                # 解码文件数据
                try:
                    file_data = result.get('file_data', b'')
                    logger.info(f"收到文件数据，大小: {len(file_data)} 字节")
                    
                    if not file_data:
                        logger.error("收到的文件数据为空")
                        return False, {'message': "收到的文件数据为空"}
                    
                    return True, {
                        'message': result.get('message', '更新成功'),
                        'filename': result.get('filename', 'output.dwg'),
                        'file_data': file_data
                    }
                except Exception as e:
                    logger.error(f"处理文件数据失败: {str(e)}")
                    return False, {'message': f"处理文件数据失败: {str(e)}"}
                
            except ValueError:
                # 如果不是JSON格式，尝试获取文本内容
                logger.error(f"响应不是有效的JSON格式: {response.text[:200]}")
                return False, {'message': f"服务器返回的数据不是有效的JSON格式: {response.text[:200]}..."}
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接DWG服务失败: {str(e)}")
            return False, {"message": f"连接DWG服务失败: 请确保DWG服务已在主机 ({self.api_url}) 上启动"}
        except requests.exceptions.Timeout as e:
            logger.error(f"请求DWG服务超时: {str(e)}")
            return False, {"message": "请求DWG服务超时，请稍后再试"}
        except Exception as e:
            logger.error(f"调用DWG服务出错: {str(e)}")
            logger.error("详细错误信息:", exc_info=True)
            return False, {'message': f"调用服务出错: {str(e)}"}

# 创建一个默认客户端实例，可以直接导入使用
dwg_client = DwgServiceClient() 