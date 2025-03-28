import requests
import base64
import os
import logging
import json
from flask import current_app

logger = logging.getLogger('dwg_client')
# 确保日志级别设置正确
logger.setLevel(logging.INFO)
# 添加处理程序如果还没有
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or os.environ.get('DWG_SERVICE_URL', 'http://localhost:5001')
        self.api_key = api_key or os.environ.get('DWG_SERVICE_KEY', '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85')
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
            headers = {'X-API-KEY': self.api_key}
            
            # 准备文件和数据
            if isinstance(template_file, str):
                # 如果是文件路径，则打开文件
                if not os.path.exists(template_file):
                    logger.error(f"模板文件不存在: {template_file}")
                    return False, {'message': f"模板文件不存在: {template_file}"}
                    
                logger.info(f"打开模板文件: {template_file}")
                files = {'file': open(template_file, 'rb')}
                close_file = True
            else:
                # 如果已经是文件对象
                logger.info("使用提供的文件对象")
                files = {'file': template_file}
                close_file = False
            
            # 序列化属性数据
            try:
                data_json = json.dumps(attribute_data)
                logger.info(f"属性数据已序列化，长度: {len(data_json)}")
            except Exception as e:
                logger.error(f"序列化属性数据失败: {str(e)}")
                return False, {'message': f"序列化属性数据失败: {str(e)}"}
                
            data = {'data': data_json}
            
            # 发送请求
            logger.info(f"发送DWG更新请求到: {url}")
            try:
                response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
                logger.info(f"收到服务器响应，状态码: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败: {str(e)}")
                return False, {'message': f"请求失败: {str(e)}"}
            finally:
                # 关闭文件（如果需要）
                if close_file:
                    files['file'].close()
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
                    file_data_str = result.get('file_data', '')
                    logger.info(f"收到编码后的文件数据，长度: {len(file_data_str)}")
                    
                    if not file_data_str:
                        logger.error("收到的文件数据为空")
                        return False, {'message': "收到的文件数据为空"}
                        
                    file_data = base64.b64decode(file_data_str)
                    logger.info(f"文件数据解码成功，大小: {len(file_data)} 字节")
                    
                    return True, {
                        'message': result.get('message', '更新成功'),
                        'filename': result.get('filename', ''),
                        'file_data': file_data
                    }
                except Exception as e:
                    logger.error(f"解码文件数据失败: {str(e)}")
                    return False, {'message': f"解码文件数据失败: {str(e)}"}
                
            except ValueError:
                # 如果不是JSON格式，尝试获取文本内容
                logger.error(f"响应不是有效的JSON格式: {response.text[:200]}")
                return False, {'message': f"服务器返回的数据不是有效的JSON格式: {response.text[:200]}..."}
                
        except Exception as e:
            logger.error(f"调用DWG服务出错: {str(e)}")
            logger.error("详细错误信息:", exc_info=True)
            return False, {'message': f"调用服务出错: {str(e)}"}

# 创建一个默认客户端实例，可以直接导入使用
dwg_client = DwgServiceClient() 