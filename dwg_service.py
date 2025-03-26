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
    acad = None
    doc = None
    try:
        # 确保COM初始化在主线程运行
        logger.info("开始COM初始化")
        pythoncom.CoInitialize()
        
        # 尝试多次连接AutoCAD
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"尝试连接AutoCAD (尝试 {attempt}/{max_attempts})")
                acad = win32com.client.Dispatch("AutoCAD.Application")
                logger.info(f"成功连接AutoCAD")
                break
            except Exception as e:
                logger.error(f"连接AutoCAD失败 (尝试 {attempt}/{max_attempts}): {str(e)}")
                if attempt == max_attempts:
                    raise
                import time
                time.sleep(2)  # 等待2秒后重试
        
        # 检查AutoCAD是否已正确初始化
        if not acad:
            raise Exception("无法连接到AutoCAD应用程序")
            
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
            
        # 确保路径是绝对路径
        template_path = os.path.abspath(template_path)
        output_path = os.path.abspath(output_path)
        
        logger.info(f"模板文件绝对路径: {template_path}")
        logger.info(f"输出文件绝对路径: {output_path}")
        
        # 打开模板文件
        try:
            doc = acad.Documents.Open(template_path)
            logger.info(f"成功打开模板文件: {template_path}")
        except Exception as e:
            logger.error(f"打开模板文件失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"打开DWG文件失败: {str(e)}")
        
        # 确保data是字典类型
        if isinstance(data, list):
            # 转换数据格式
            data_dict = {}
            for item in data:
                if isinstance(item, dict) and 'field' in item and 'value' in item:
                    data_dict[item['field']] = item['value']
                elif isinstance(item, str):
                    # 如果是字符串，尝试解析为JSON
                    try:
                        item_dict = json.loads(item)
                        if isinstance(item_dict, dict) and 'field' in item_dict and 'value' in item_dict:
                            data_dict[item_dict['field']] = item_dict['value']
                    except:
                        logger.warning(f"无法解析数据项: {item}")
            data = data_dict
        elif not isinstance(data, dict):
            # 如果不是字典或列表，尝试转换为字典
            try:
                data = dict(data)
            except:
                logger.error(f"无法将数据转换为字典: {type(data)}")
                data = {}
                
        logger.info(f"处理数据: {data}")
        
        # 更新文本对象属性
        updated_count = 0
        for field_name, field_value in data.items():
            # 将field_value转换为字符串
            if field_value is None:
                field_value = ""
            elif not isinstance(field_value, str):
                field_value = str(field_value)
                
            # 查找对应文本对象
            try:
                model_space = doc.ModelSpace
                for i in range(model_space.Count):
                    obj = model_space.Item(i)
                    if obj.ObjectName == 'AcDbText':
                        try:
                            text_string = obj.TextString.strip()
                            if text_string == field_name:
                                obj.TextString = field_value
                                updated_count += 1
                                logger.info(f"已更新字段: {field_name} -> {field_value}")
                        except Exception as e:
                            logger.error(f"处理文本对象时出错: {str(e)}")
            except Exception as e:
                logger.error(f"访问模型空间时出错: {str(e)}")
        
        logger.info(f"共更新了 {updated_count} 个字段")
        
        # 保存为新文件
        logger.info(f"开始保存DWG文件到: {output_path}")
        try:
            # 如果输出目录不存在，则创建
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
                
            # 确保目标文件不存在
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"删除已存在的输出文件: {output_path}")
                except Exception as e:
                    logger.warning(f"删除已存在文件时出错: {str(e)}")
            
            # 保存文件
            doc.SaveAs(output_path)
            logger.info(f"文件已成功保存至: {output_path}")
        except Exception as e:
            logger.error(f"保存文件时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        # 关闭文档但不退出AutoCAD
        try:
            if doc:
                doc.Close(False)  # False表示不保存
                logger.info("文档已成功关闭")
                doc = None
        except Exception as e:
            logger.error(f"关闭文档时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 检查文件是否存在
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"输出文件存在，大小为: {file_size} 字节")
        else:
            logger.error(f"输出文件不存在: {output_path}")
            raise FileNotFoundError(f"输出文件不存在: {output_path}")
            
        return True, "操作成功"
    except Exception as e:
        logger.error(f"更新DWG文件属性出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)
    finally:
        # 清理资源
        try:
            if doc:
                doc.Close(False)
                logger.info("文档已在finally块中关闭")
        except:
            pass
            
        try:
            # 释放COM资源
            pythoncom.CoUninitialize()
            logger.info("COM接口已释放")
        except:
            pass

@app.route('/api/dwg/update', methods=['POST'])
def api_update_dwg():
    """API接口：更新DWG文件属性"""
    template_path = None
    output_path = None
    
    try:
        # 验证API密钥
        auth_key = request.headers.get('X-API-KEY')
        if auth_key != SECRET_KEY:
            logger.error("API密钥认证失败")
            return jsonify({'error': '认证失败'}), 401
        
        # 获取请求数据
        if 'file' not in request.files:
            logger.error("请求中没有文件")
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        # 解析JSON数据
        data_str = request.form.get('data', '{}')
        try:
            data = json.loads(data_str)
            logger.info(f"接收到的数据类型: {type(data)}")
            logger.info(f"数据项数: {len(data) if isinstance(data, list) else 'Not a list'}")
        except Exception as e:
            logger.error(f"解析JSON数据失败: {str(e)}")
            return jsonify({'error': f'无效的JSON数据: {str(e)}'}), 400
        
        if file.filename == '':
            logger.error("文件名为空")
            return jsonify({'error': '未选择文件'}), 400
        
        # 保存上传的文件
        temp_filename = f"{uuid.uuid4()}.dwg"
        template_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(template_path)
        logger.info(f"上传的文件已保存到: {template_path}")
        
        # 设置输出路径
        output_filename = f"output_{uuid.uuid4()}.dwg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        logger.info(f"设置输出路径: {output_path}")
        
        # 尝试关闭所有可能挂起的AutoCAD进程或COM对象
        try:
            logger.info("确保COM环境干净")
            import gc
            gc.collect()  # 强制垃圾回收
            pythoncom.CoUninitialize()  # 确保之前的COM会话已关闭
        except:
            pass
            
        # 确保输出目录存在
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        logger.info(f"确保输出目录存在: {OUTPUT_FOLDER}")
        
        # 更新DWG文件
        success, message = update_dwg_attribute(
            os.path.abspath(template_path),
            os.path.abspath(output_path),
            data
        )
        
        # 返回结果
        if success:
            # 读取生成的文件并以base64编码返回
            try:
                if not os.path.exists(output_path):
                    logger.error(f"输出文件不存在: {output_path}")
                    return jsonify({'success': False, 'message': '文件生成失败：无法找到输出文件'}), 500
                
                file_size = os.path.getsize(output_path)
                logger.info(f"准备读取输出文件，大小: {file_size} 字节")
                
                if file_size == 0:
                    logger.error("输出文件大小为0")
                    return jsonify({'success': False, 'message': '文件生成失败：文件大小为0'}), 500
                
                # 读取并编码文件
                try:
                    with open(output_path, 'rb') as f:
                        file_data = base64.b64encode(f.read()).decode('utf-8')
                    logger.info(f"文件已读取并编码，编码后长度: {len(file_data)} 字符")
                except Exception as read_error:
                    logger.error(f"读取文件时出错: {str(read_error)}")
                    return jsonify({'success': False, 'message': f'读取文件时出错: {str(read_error)}'}), 500
                
                # 检查编码后的数据是否为空
                if not file_data:
                    logger.error("文件编码后为空")
                    return jsonify({'success': False, 'message': '文件编码后为空'}), 500
                
                # 清理临时文件
                try:
                    if template_path and os.path.exists(template_path):
                        os.remove(template_path)
                        logger.info(f"已删除模板文件: {template_path}")
                        template_path = None
                except Exception as e:
                    logger.warning(f"删除模板文件失败: {str(e)}")
                
                # 暂时保留输出文件用于调试
                # try:
                #     os.remove(output_path)
                #     logger.info(f"已删除输出文件: {output_path}")
                # except Exception as e:
                #     logger.warning(f"删除输出文件失败: {str(e)}")
                
                logger.info("API调用成功完成，准备返回数据")
                
                return jsonify({
                    'success': True,
                    'message': '更新成功',
                    'filename': output_filename,
                    'file_data': file_data
                })
            except Exception as e:
                logger.error(f"读取或编码文件时出错: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'success': False, 'message': f'文件处理出错: {str(e)}'}), 500
        else:
            logger.error(f"更新DWG属性失败: {message}")
            return jsonify({
                'success': False,
                'message': f'更新失败: {message}'
            }), 500
            
    except Exception as e:
        logger.error(f"API处理出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        try:
            if template_path and os.path.exists(template_path):
                os.remove(template_path)
                logger.info(f"已在finally块中删除模板文件: {template_path}")
        except Exception as e:
            logger.warning(f"删除模板文件失败: {str(e)}")
            
        # 强制COM资源释放
        try:
            pythoncom.CoUninitialize()
            logger.info("已在finally块中释放COM资源")
        except:
            pass

# 尝试重启AutoCAD的函数
def restart_autocad():
    """尝试关闭现有AutoCAD实例并启动一个新的实例"""
    try:
        logger.info("尝试重启AutoCAD")
        # 尝试终止现有的AutoCAD进程
        import subprocess
        subprocess.run(["taskkill", "/f", "/im", "acad.exe"], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                       shell=True)
        logger.info("已尝试关闭现有AutoCAD进程")
        
        # 初始化COM环境
        pythoncom.CoUninitialize()
        pythoncom.CoInitialize()
        
        # 等待几秒钟
        import time
        time.sleep(3)
        
        # 启动新的AutoCAD实例
        acad = win32com.client.Dispatch("AutoCAD.Application")
        logger.info("已成功重启AutoCAD")
        
        # 释放引用
        acad = None
        import gc
        gc.collect()
        
        return True
    except Exception as e:
        logger.error(f"重启AutoCAD失败: {str(e)}")
        return False

if __name__ == '__main__':
    # 初始化COM环境
    try:
        pythoncom.CoInitialize()
        logger.info("COM环境初始化成功")
    except Exception as e:
        logger.error(f"COM环境初始化失败: {str(e)}")
    
    try:
        # 设置适当的权限
        import win32api
        import win32con
        import win32security
        
        # 提升进程权限
        logger.info("尝试提升进程权限")
        handle = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY)
        win32security.AdjustTokenPrivileges(
            handle, 0, [(win32security.LookupPrivilegeValue(None, "SeDebugPrivilege"), win32con.SE_PRIVILEGE_ENABLED)]
        )
        logger.info("进程权限已提升")
    except Exception as e:
        logger.warning(f"提升进程权限失败: {str(e)}")
    
    # 尝试预启动AutoCAD以避免第一次请求超时
    try:
        logger.info("尝试预启动AutoCAD")
        acad = win32com.client.Dispatch("AutoCAD.Application")
        logger.info("AutoCAD已预启动")
        
        # 释放引用但不关闭AutoCAD
        acad = None
        import gc
        gc.collect()
        logger.info("AutoCAD引用已释放")
    except Exception as e:
        logger.warning(f"预启动AutoCAD失败: {str(e)}")
        # 尝试重启AutoCAD
        restart_autocad()
    
    # 添加host参数使其可以从外部访问
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=False)  # 使用单线程模式避免COM冲突 