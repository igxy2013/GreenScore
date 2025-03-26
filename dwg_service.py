from flask import Flask, request, jsonify
import win32com.client
import pythoncom
import os
import traceback
import json
import uuid
import base64
import logging
from logging.handlers import RotatingFileHandler

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
SECRET_KEY = '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85'  # 用于API认证

# 确保上传和输出目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def update_dwg_attribute(template_path, output_path, data):
    """更新DWG文件属性"""
    try:
        pythoncom.CoInitialize()
        acad = win32com.client.Dispatch("AutoCAD.Application")
        logger.info(f"成功连接AutoCAD")
        
        # 打开模板文件
        doc = acad.Documents.Open(template_path)
        logger.info(f"成功打开模板文件: {template_path}")
        
        # 更新文本对象属性
        for item in data:
            field_name = item.get('field')
            field_value = item.get('value', '')
            
            # 查找对应文本对象
            for obj in doc.ModelSpace:
                if obj.ObjectName == 'AcDbText':
                    if obj.TextString.strip() == field_name:
                        obj.TextString = field_value
                        logger.info(f"已更新字段: {field_name} -> {field_value}")
        
        # 保存为新文件
        doc.SaveAs(output_path)
        logger.info(f"文件已保存至: {output_path}")
        
        # 关闭文档但不退出AutoCAD
        doc.Close()
        pythoncom.CoUninitialize()
        
        return True, "操作成功"
    except Exception as e:
        logger.error(f"更新DWG文件属性出错: {str(e)}")
        logger.error(traceback.format_exc())
        pythoncom.CoUninitialize()
        return False, str(e)

@app.route('/api/dwg/update', methods=['POST'])
def api_update_dwg():
    """API接口：更新DWG文件属性"""
    try:
        # 验证API密钥
        auth_key = request.headers.get('X-API-KEY')
        if auth_key != SECRET_KEY:
            return jsonify({'error': '认证失败'}), 401
        
        # 获取请求数据
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        data = json.loads(request.form.get('data', '[]'))
        
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
        success, message = update_dwg_attribute(
            os.path.abspath(template_path),
            os.path.abspath(output_path),
            data
        )
        
        # 返回结果
        if success:
            # 读取生成的文件并以base64编码返回
            with open(output_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 清理临时文件
            try:
                os.remove(template_path)
                os.remove(output_path)
            except:
                pass
                
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
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 添加host参数使其可以从外部访问
    app.run(host='0.0.0.0', port=5001, debug=True) 