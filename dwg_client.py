import requests
import base64
import os
import logging
import json
from flask import current_app

logger = logging.getLogger('dwg_client')

class DwgServiceClient:
    """DWG服务客户端"""
    
    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or os.environ.get('DWG_SERVICE_URL', 'http://aibim.xyz:5001')
        self.api_key = api_key or os.environ.get('DWG_SERVICE_KEY', '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85')
        
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
            # 准备API请求
            url = f"{self.api_url}/api/dwg/update"
            headers = {'X-API-KEY': self.api_key}
            
            # 准备文件和数据
            if isinstance(template_file, str):
                # 如果是文件路径，则打开文件
                files = {'file': open(template_file, 'rb')}
                close_file = True
            else:
                # 如果已经是文件对象
                files = {'file': template_file}
                close_file = False
                
            data = {'data': json.dumps(attribute_data)}
            
            # 发送请求
            logger.info(f"发送DWG更新请求到: {url}")
            response = requests.post(url, headers=headers, files=files, data=data)
            
            # 关闭文件（如果需要）
            if close_file:
                files['file'].close()
                
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # 解码文件数据
                    file_data = base64.b64decode(result.get('file_data', ''))
                    return True, {
                        'message': result.get('message', '更新成功'),
                        'filename': result.get('filename', ''),
                        'file_data': file_data
                    }
                else:
                    logger.error(f"DWG服务返回错误: {result.get('message')}")
                    return False, {'message': result.get('message', '服务端处理失败')}
            else:
                logger.error(f"DWG服务请求失败: HTTP {response.status_code}, {response.text}")
                return False, {'message': f"请求失败: HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"调用DWG服务出错: {str(e)}")
            return False, {'message': f"调用服务出错: {str(e)}"}

# 创建一个默认客户端实例，可以直接导入使用
dwg_client = DwgServiceClient() 