from flask import Flask, request, jsonify
import win32com.client
import pythoncom
import os
import traceback
import json
import uuid
import base64
import logging
import time
import hashlib
from logging.handlers import RotatingFileHandler
from functools import lru_cache
from waitress import serve

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dwg_service')
handler = RotatingFileHandler('dwg_service.log', maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
CACHE_FOLDER = 'dwg_cache'
SECRET_KEY = '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85'  # 用于API认证
MAX_CACHE_SIZE = 50  # 最大缓存条目数
PORT = 5001  # 服务端口

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# DWG文件处理类
class DwgHandler:
    @staticmethod
    def update_dwg_attribute(template_path, output_path, data, use_cache=True):
        """更新DWG文件属性"""
        logger.info(f"处理DWG文件: {template_path} -> {output_path}")
        logger.info(f"属性数据: {data}")
        
        acad = None
        doc = None
        
        try:
            # 初始化COM环境
            pythoncom.CoInitialize()
            
            # 获取AutoCAD应用程序实例
            acad = win32com.client.Dispatch("AutoCAD.Application")
            logger.info("已连接到AutoCAD")
            
            # 打开模板文件
            doc = acad.Documents.Open(template_path)
            logger.info(f"已打开模板文件: {template_path}")
            
            # 处理数据格式
            if isinstance(data, list):
                data_dict = {}
                for item in data:
                    if isinstance(item, dict) and 'field' in item and 'value' in item:
                        data_dict[item['field']] = item['value']
                data = data_dict
            
            # 更新文本对象
            model_space = doc.ModelSpace
            updated_count = 0
            
            # 处理普通文本对象
            for i in range(model_space.Count):
                try:
                    obj = model_space.Item(i)
                    if obj.ObjectName == 'AcDbText':
                        text_string = obj.TextString.strip()
                        if text_string in data:
                            obj.TextString = data[text_string]
                            updated_count += 1
                    # 处理属性块
                    elif obj.ObjectName == "AcDbBlockReference" and hasattr(obj, 'HasAttributes') and obj.HasAttributes:
                        for attrib in obj.GetAttributes():
                            tag_name = attrib.TagString
                            if tag_name in data:
                                attrib.TextString = data[tag_name]
                                updated_count += 1
                except Exception as e:
                    pass
            
            logger.info(f"已更新 {updated_count} 个字段")
            
            # 保存文件
            doc.SaveAs(output_path)
            logger.info(f"文件已保存: {output_path}")
            
            return True, "更新成功"
            
        except Exception as e:
            logger.error(f"处理DWG文件失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False, str(e)
            
        finally:
            # 关闭文档但不退出AutoCAD
            try:
                if doc:
                    doc.Close(False)
                    logger.info("已关闭文档")
            except Exception:
                pass
            
            # 释放COM资源
            try:
                doc = None
                acad = None
                pythoncom.CoUninitialize()
            except:
                pass

# API端点
@app.route('/api/dwg/update', methods=['POST'])
def api_update_dwg():
    """API接口：更新DWG文件属性"""
    template_path = None
    output_path = None
    
    try:
        # 验证API密钥
        auth_key = request.headers.get('X-API-KEY')
        if auth_key != SECRET_KEY:
            return jsonify({'error': '认证失败'}), 401
        
        # 获取请求数据
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        # 解析JSON数据
        data_str = request.form.get('data', '{}')
        try:
            data = json.loads(data_str)
        except Exception as e:
            return jsonify({'error': f'无效的JSON数据: {str(e)}'}), 400
        
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 保存上传的文件
        temp_filename = f"{uuid.uuid4()}.dwg"
        template_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(template_path)
        
        # 设置输出路径
        output_filename = f"output_{uuid.uuid4()}.dwg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 更新DWG文件
        success, message = DwgHandler.update_dwg_attribute(
            template_path,
            output_path,
            data
        )
        
        # 返回结果
        if success:
            # 读取文件并编码
            with open(output_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'message': '更新成功',
                'filename': output_filename,
                'file_data': file_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f'更新失败: {message}'
            }), 500
            
    except Exception as e:
        logger.error(f"API处理出错: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        try:
            if template_path and os.path.exists(template_path):
                os.remove(template_path)
        except:
            pass

# 健康检查接口
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'dwg-service',
        'version': '1.0-simplified'
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print(" DWG服务 - 简化版")
    print("=" * 50)
    
    # 初始化COM环境
    try:
        pythoncom.CoInitialize()
        # 预启动AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad = None
        import gc
        gc.collect()
    except Exception as e:
        logger.warning(f"初始化AutoCAD失败: {str(e)}")
    
    # 启动服务器
    print(f"服务已启动，在 http://0.0.0.0:{PORT} 监听")
    serve(app, host='0.0.0.0', port=PORT, threads=1)  # 使用单线程模式避免COM冲突 