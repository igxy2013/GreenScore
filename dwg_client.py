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
        # 首先检查环境变量中是否手动设置了DWG主机IP
        manual_host_ip = os.environ.get('DWG_HOST_IP')
        if manual_host_ip:
            logger.info(f"使用环境变量中设置的DWG主机IP: {manual_host_ip}")
            # 验证手动设置的IP是否可用
            try:
                test_url = f"http://{manual_host_ip}:5001/api/health"
                logger.info(f"测试手动设置的IP是否可用: {test_url}")
                response = requests.get(test_url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"手动设置的IP {manual_host_ip} 可用")
                    return manual_host_ip
                else:
                    logger.warning(f"手动设置的IP {manual_host_ip} 不可用，状态码: {response.status_code}")
                    # 继续尝试其他方法
            except Exception as e:
                logger.warning(f"手动设置的IP {manual_host_ip} 不可用: {str(e)}")
                # 继续尝试其他方法
            # 即使验证失败，仍然优先使用手动设置的IP
            return manual_host_ip
            
        # 如果在WSL环境中，尝试获取Windows主机IP
        if IS_WSL:
            detected_ip = None
            valid_ip = None
            
            # 方法1：直接使用.env中配置的默认IP（最可靠的方法）
            default_ip = '192.168.0.80'  # 使用.env中配置的默认IP
            try:
                test_url = f"http://{default_ip}:5001/api/health"
                logger.info(f"测试默认IP是否可用: {test_url}")
                response = requests.get(test_url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"默认IP {default_ip} 可用")
                    return default_ip
                else:
                    logger.warning(f"默认IP {default_ip} 不可用，状态码: {response.status_code}")
            except Exception as e:
                logger.warning(f"默认IP {default_ip} 不可用: {str(e)}")
            
            # 方法2：尝试读取/etc/resolv.conf获取WSL DNS服务器IP（通常是Windows主机IP）
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            detected_ip = line.split()[1]
                            # 排除特殊IP地址，如10.255.255.254
                            if detected_ip.startswith('10.255.255.'):
                                logger.warning(f"跳过特殊IP地址: {detected_ip}")
                                continue
                            logger.info(f"从/etc/resolv.conf获取到Windows主机IP: {detected_ip}")
                            # 验证IP是否可用
                            try:
                                test_url = f"http://{detected_ip}:5001/api/health"
                                logger.info(f"测试检测到的IP是否可用: {test_url}")
                                response = requests.get(test_url, timeout=2)
                                if response.status_code == 200:
                                    logger.info(f"检测到的IP {detected_ip} 可用")
                                    valid_ip = detected_ip
                                    break
                                else:
                                    logger.warning(f"检测到的IP {detected_ip} 不可用，状态码: {response.status_code}")
                            except Exception as e:
                                logger.warning(f"检测到的IP {detected_ip} 不可用: {str(e)}")
            except Exception as e:
                logger.warning(f"无法从/etc/resolv.conf获取IP: {str(e)}")
            
            # 如果找到有效IP，直接返回
            if valid_ip:
                return valid_ip
            
            # 方法3：如果方法2失败，尝试使用host.docker.internal域名
            if not valid_ip:
                try:
                    detected_ip = socket.gethostbyname('host.docker.internal')
                    logger.info(f"从host.docker.internal获取到Windows主机IP: {detected_ip}")
                    # 验证IP是否可用
                    try:
                        test_url = f"http://{detected_ip}:5001/api/health"
                        logger.info(f"测试检测到的IP是否可用: {test_url}")
                        response = requests.get(test_url, timeout=2)
                        if response.status_code == 200:
                            logger.info(f"检测到的IP {detected_ip} 可用")
                            return detected_ip
                        else:
                            logger.warning(f"检测到的IP {detected_ip} 不可用，状态码: {response.status_code}")
                    except Exception as e:
                        logger.warning(f"检测到的IP {detected_ip} 不可用: {str(e)}")
                except socket.gaierror:
                    logger.warning("无法从host.docker.internal获取IP")
            
            # 方法4：最后使用默认IP
            logger.info(f"使用默认IP: {default_ip}")
            return default_ip
        else:
            # 在Windows环境中，默认使用localhost
            logger.info("在Windows环境中使用localhost作为服务主机")
            return 'localhost'
    except Exception as e:
        logger.error(f"获取主机IP失败: {str(e)}")
        return '192.168.0.80'  # 出错时使用默认IP

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        # 根据环境选择合适的服务地址
        # 优先使用传入的api_url参数
        if api_url:
            self.api_url = api_url
            logger.info(f"使用传入的API地址: {self.api_url}")
        else:
            # 其次检查环境变量中是否直接设置了完整的服务URL
            env_service_url = os.environ.get('DWG_SERVICE_URL')
            if env_service_url:
                self.api_url = env_service_url
                logger.info(f"使用环境变量中的DWG服务URL: {self.api_url}")
            else:
                # 最后使用自动检测的IP地址
                service_ip = get_service_host_ip()
                self.api_url = f'http://{service_ip}:5001'
                logger.info(f"使用自动检测的服务地址: {self.api_url} (IP: {service_ip})")
        
        # 设置API密钥
        self.api_key = api_key or os.environ.get('DWG_SERVICE_KEY', '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85')
        # 设置请求参数
        self.timeout = int(os.environ.get('DWG_REQUEST_TIMEOUT', '120'))  # 设置超时时间，默认120秒
        self.max_retries = int(os.environ.get('DWG_MAX_RETRIES', '3'))  # 最大重试次数，默认3次
        self.retry_delay = int(os.environ.get('DWG_RETRY_DELAY', '2'))  # 重试延迟，默认2秒
        # 初始化模板缓存
        self.template_cache = {}
        logger.info(f"DWG服务客户端初始化完成，API地址: {self.api_url}, 超时: {self.timeout}秒, 最大重试: {self.max_retries}次")
        
    def update_dwg_attributes(self, template_file, attribute_data):
        """
        通过API更新DWG文件属性
        
        Args:
            template_file: DWG模板文件对象或路径
            attribute_data: 属性数据列表，如 [{'field': '项目名称', 'value': 'XX项目'}]
            
        Returns:
            (success, result): 成功状态和结果数据
        """
        # 检查缓存
        cache_key = None
        if isinstance(template_file, str):
            # 如果是文件路径，使用文件路径和属性数据的哈希作为缓存键
            try:
                attr_hash = hash(json.dumps(attribute_data, sort_keys=True))
                cache_key = f"{template_file}:{attr_hash}"
                
                # 检查缓存中是否有结果
                if cache_key in self.template_cache:
                    logger.info(f"使用缓存结果，缓存键: {cache_key}")
                    return True, self.template_cache[cache_key]
            except Exception as e:
                logger.warning(f"创建缓存键失败，将不使用缓存: {str(e)}")
        
        # 记录调用信息（减少日志详细程度）
        logger.info(f"调用DWG服务更新属性，模板: {template_file}, 属性数据数量: {len(attribute_data)}")
        
        # 准备API请求
        url = f"{self.api_url}/api/dwg/update"
        headers = {'X-API-KEY': self.api_key}
        file_obj = None
        
        try:
            # 准备文件和数据
            if isinstance(template_file, str):
                # 如果是文件路径，则打开文件
                if not os.path.exists(template_file):
                    logger.error(f"模板文件不存在: {template_file}")
                    return False, {'message': f"模板文件不存在: {template_file}"}
                
                # 打开文件但不立即关闭，使用with语句确保正确关闭
                file_obj = open(template_file, 'rb')
                files = {'file': file_obj}
            else:
                # 如果已经是文件对象
                files = {'file': template_file}
            
            # 序列化属性数据
            try:
                data_json = json.dumps(attribute_data)
            except Exception as e:
                logger.error(f"序列化属性数据失败: {str(e)}")
                if file_obj:
                    file_obj.close()
                return False, {'message': f"序列化属性数据失败: {str(e)}"}
                
            data = {'data': data_json}
            
            # 实现重试机制
            retry_count = 0
            last_error = None
            
            while retry_count <= self.max_retries:
                try:
                    if retry_count > 0:
                        logger.info(f"第 {retry_count} 次重试发送请求...")
                        import time
                        time.sleep(self.retry_delay)  # 重试前等待
                    
                    # 发送请求
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
                    
                    # 只在调试级别记录详细响应信息
                    if response.status_code != 200:
                        logger.warning(f"服务器响应状态码: {response.status_code}")
                    else:
                        logger.info(f"请求成功，状态码: {response.status_code}")
                    
                    # 处理响应
                    result = response.json()
                    
                    # 即使是错误状态码，也尝试从JSON中获取有用信息
                    success = result.get('success', False) if response.status_code == 200 else False
                    message = result.get('message', f"请求失败，状态码: {response.status_code}") 
                    
                    if not success:
                        error_msg = result.get('error', message)
                        logger.error(f"DWG服务返回错误: {error_msg}")
                        last_error = {'message': error_msg}
                        # 如果是服务器错误，尝试重试
                        if response.status_code >= 500 and retry_count < self.max_retries:
                            retry_count += 1
                            continue
                        return False, {'message': error_msg}
                    
                    # 如果是成功状态，检查文件数据
                    if 'file_data' not in result:
                        logger.error("响应中缺少文件数据")
                        return False, {'message': "服务器响应中缺少文件数据"}
                    
                    # 处理文件数据
                    file_data = result.get('file_data', b'')
                    
                    # 确保file_data是字节类型
                    if isinstance(file_data, str):
                        try:
                            # 尝试将Base64字符串解码为字节
                            if file_data.startswith('data:'):
                                # 处理Data URL格式
                                file_data = base64.b64decode(file_data.split(',')[1])
                            else:
                                # 尝试直接解码Base64字符串
                                file_data = base64.b64decode(file_data)
                            logger.info("已将字符串类型的文件数据转换为字节类型")
                        except Exception as e:
                            logger.error(f"转换文件数据为字节类型失败: {str(e)}")
                            return False, {'message': f"文件数据格式错误: {str(e)}"}
                    
                    if not file_data:
                        logger.error("收到的文件数据为空")
                        return False, {'message': "收到的文件数据为空"}
                    
                    # 构建结果
                    success_result = {
                        'message': result.get('message', '更新成功'),
                        'filename': result.get('filename', 'output.dwg'),
                        'file_data': file_data
                    }
                    
                    # 存入缓存
                    if cache_key:
                        self.template_cache[cache_key] = success_result
                        logger.info(f"结果已存入缓存，缓存键: {cache_key}")
                    
                    return True, success_result
                    
                except requests.exceptions.Timeout as e:
                    logger.warning(f"请求超时 (尝试 {retry_count+1}/{self.max_retries+1}): {str(e)}")
                    last_error = {"message": f"请求DWG服务超时: {str(e)}"}
                    if retry_count < self.max_retries:
                        retry_count += 1
                        continue
                    return False, last_error
                    
                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"连接错误 (尝试 {retry_count+1}/{self.max_retries+1}): {str(e)}")
                    last_error = {"message": f"连接DWG服务失败: 请确保DWG服务已在主机 ({self.api_url}) 上启动"}
                    if retry_count < self.max_retries:
                        retry_count += 1
                        continue
                    return False, last_error
                    
                except ValueError as e:
                    # JSON解析错误，可能是服务器返回了非JSON格式
                    logger.error(f"响应不是有效的JSON格式: {response.text[:200] if 'response' in locals() else '无响应'}")
                    return False, {'message': f"服务器返回的数据不是有效的JSON格式"}
                    
                except Exception as e:
                    logger.error(f"请求处理出错 (尝试 {retry_count+1}/{self.max_retries+1}): {str(e)}")
                    last_error = {'message': f"请求处理出错: {str(e)}"}
                    if retry_count < self.max_retries:
                        retry_count += 1
                        continue
                    return False, last_error
        
        except Exception as e:
            logger.error(f"调用DWG服务出错: {str(e)}")
            logger.error("详细错误信息:", exc_info=True)
            return False, {'message': f"调用服务出错: {str(e)}"}
        
        finally:
            # 确保文件对象被关闭
            if file_obj:
                file_obj.close()

# 创建一个默认客户端实例，可以直接导入使用
dwg_client = DwgServiceClient()