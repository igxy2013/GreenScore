import requests
import base64
import os
import logging
import json
from flask import current_app
import platform
import socket
from dotenv import load_dotenv
import traceback  # 添加traceback模块

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查是否在WSL环境中
IS_WSL = 'WSL' in platform.uname().release or \
         (os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower())

# 获取服务主机IP
def get_service_host_ip():
    # 只有WSL环境才需要获取主机IP
    if not IS_WSL:
        logger.info("非WSL环境，不需要远程DWG服务")
        return '127.0.0.1'  # 在Windows环境中返回本地地址
    
    try:
        # 从环境变量中获取DWG主机IP，直接使用os.environ
        host_ip = os.environ.get('DWG_HOST_IP')
        if host_ip:
            logger.info(f"使用环境变量中的DWG主机IP: {host_ip}")
            return host_ip
        
        # 如果环境变量中没有，尝试获取WSL主机IP
        try:
            # 方法1: 直接查找192.168.x.x网段的IP
            import subprocess
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout.strip()
                # 查找192.168开头的路由条目
                for line in output.split('\n'):
                    if '192.168.' in line and 'via' in line:
                        parts = line.split()
                        via_index = parts.index('via') if 'via' in parts else -1
                        if via_index >= 0 and via_index + 1 < len(parts):
                            host_ip = parts[via_index + 1]
                            logger.info(f"从ip route获取到Windows主机IP: {host_ip}")
                            return host_ip

            # 方法2: 尝试使用特殊的hostname获取
            try:
                host_ip = socket.gethostbyname('host.docker.internal')
                logger.info(f"通过host.docker.internal获取到Windows主机IP: {host_ip}")
                return host_ip
            except:
                pass
            
            # 方法3: 在WSL环境中尝试获取Windows主机IP - /etc/resolv.conf
            # 但忽略已知的错误IP
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
            
            # 方法4: 尝试读取/etc/hosts
            if os.path.exists('/etc/hosts'):
                with open('/etc/hosts', 'r') as f:
                    for line in f:
                        if 'host.docker.internal' in line or 'windows' in line.lower():
                            parts = line.strip().split()
                            if parts and parts[0] != '127.0.0.1' and parts[0] != '::1':
                                host_ip = parts[0]
                                logger.info(f"从/etc/hosts获取到Windows主机IP: {host_ip}")
                                return host_ip
            
            # 方法5: 使用内置变量(WSL2特有)
            host_ip = '192.168.0.80'  # 这里使用已知的正确IP地址
            logger.info(f"使用已知的Windows主机IP: {host_ip}")
            return host_ip
            
        except Exception as e:
            logger.warning(f"自动获取主机IP失败: {str(e)}")
        
        # 以上方法都失败，则使用默认值
        default_ip = '192.168.0.80'  # 已知的正确Windows主机IP
        logger.info(f"未能自动获取主机IP，使用'{default_ip}'作为默认值")
        return default_ip
    except Exception as e:
        logger.error(f"获取主机IP失败: {str(e)}")
        return '192.168.0.80'  # 出错时使用指定的IP

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        # 标记当前环境
        self.is_wsl = IS_WSL
        
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
        
    def check_health(self):
        """
        检查DWG服务的健康状态
        
        Returns:
            (success, result): 成功状态和结果数据
        """
        # 如果不在WSL环境中且使用本地地址，则不执行远程健康检查
        if not self.is_wsl and '127.0.0.1' in self.api_url:
            logger.info("非WSL环境，本地DWG服务，跳过健康检查")
            return True, {"status": "ok", "service": "dwg-service", "version": "local"}
        
        try:
            url = f"{self.api_url}/api/health"
            logger.info(f"检查DWG服务健康状态: {url}")
            
            response = requests.get(url, timeout=10)
            logger.info(f"健康检查响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"健康检查结果: {result}")
                return True, result
            else:
                logger.error(f"健康检查失败，状态码: {response.status_code}")
                return False, {"message": f"健康检查失败，状态码: {response.status_code}"}
                
        except requests.exceptions.Timeout as e:
            logger.error(f"健康检查超时: {str(e)}")
            return False, {"message": f"健康检查超时: {str(e)}"}
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"无法连接到DWG服务: {str(e)}")
            return False, {"message": f"无法连接到DWG服务: {str(e)}"}
            
        except Exception as e:
            logger.error(f"健康检查出错: {str(e)}")
            return False, {"message": f"健康检查出错: {str(e)}"}
        
    def update_dwg_attributes(self, template_file, attribute_data):
        """
        通过API更新DWG文件属性
        
        Args:
            template_file: DWG模板文件对象或路径
            attribute_data: 属性数据列表，如 [{'field': '项目名称', 'value': 'XX项目'}]
            
        Returns:
            (success, result): 成功状态和结果数据
        """
        # 非WSL环境不使用远程服务
        if not self.is_wsl:
            logger.info("非WSL环境，应直接使用本地AutoCAD处理DWG文件，而不是通过远程服务")
            logger.info("请在Windows环境中使用update_dwg_attribute模块直接处理")
            return False, {'message': '非WSL环境，请使用本地AutoCAD处理DWG文件'}
        
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
                logger.info(f"已打开文件: {template_file}, 大小: {os.path.getsize(template_file)} 字节")
            else:
                # 如果已经是文件对象
                files = {'file': template_file}
                logger.info("使用提供的文件对象")
            
            # 序列化属性数据
            try:
                data_json = json.dumps(attribute_data)
                logger.info(f"已序列化属性数据，JSON长度: {len(data_json)} 字符")
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
                    logger.info(f"正在发送POST请求到 {url}, 请求头: {headers}, 文件数量: {len(files)}, 数据长度: {len(data_json)}")
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
                    
                    # 只在调试级别记录详细响应信息
                    if response.status_code != 200:
                        logger.warning(f"服务器响应状态码: {response.status_code}")
                    else:
                        logger.info(f"请求成功，状态码: {response.status_code}")
                    
                    # 添加额外响应内容调试
                    try:
                        content_type = response.headers.get('Content-Type', '')
                        logger.info(f"响应Content-Type: {content_type}")
                        # 尝试打印响应内容的前200个字符
                        response_text = response.text[:200] + ('...' if len(response.text) > 200 else '')
                        logger.info(f"响应内容前200个字符: {response_text}")
                    except:
                        pass
                    
                    # 处理响应
                    try:
                        result = response.json()
                    except ValueError as json_err:
                        logger.error(f"响应不是有效的JSON格式: {response.text[:200] if len(response.text) > 0 else '响应为空'}")
                        logger.error(f"JSON解析错误: {str(json_err)}")
                        logger.error(f"错误详情: {traceback.format_exc()}")
                        # 检查是否是HTML响应
                        if 'text/html' in content_type and '<html' in response.text.lower():
                            logger.error("服务器返回了HTML页面，可能是因为路由配置错误或服务端出现异常")
                        elif response.status_code == 404:
                            logger.error("404错误，URL可能不正确或服务未正确配置")
                        return False, {'message': f"服务器返回的数据不是有效的JSON格式"}
                    
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