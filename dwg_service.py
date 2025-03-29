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

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# 文件缓存实现
class DwgFileCache:
    """DWG文件处理结果缓存"""
    
    def __init__(self, cache_dir=CACHE_FOLDER, max_size=MAX_CACHE_SIZE):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.cache_index = {}
        self._load_cache_index()
    
    def _load_cache_index(self):
        """加载缓存索引"""
        index_file = os.path.join(self.cache_dir, 'cache_index.json')
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
                logger.info(f"已加载缓存索引，包含 {len(self.cache_index)} 个条目")
            except Exception as e:
                logger.error(f"加载缓存索引失败: {str(e)}")
                self.cache_index = {}
    
    def _save_cache_index(self):
        """保存缓存索引"""
        index_file = os.path.join(self.cache_dir, 'cache_index.json')
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f)
            logger.info(f"已保存缓存索引，包含 {len(self.cache_index)} 个条目")
        except Exception as e:
            logger.error(f"保存缓存索引失败: {str(e)}")
    
    def _generate_cache_key(self, template_path, data):
        """生成缓存键"""
        try:
            # 计算模板文件的MD5
            with open(template_path, 'rb') as f:
                template_md5 = hashlib.md5(f.read()).hexdigest()
            
            # 计算数据的MD5
            data_str = json.dumps(data, sort_keys=True)
            data_md5 = hashlib.md5(data_str.encode('utf-8')).hexdigest()
            
            # 组合成缓存键
            return f"{template_md5}_{data_md5}"
        except Exception as e:
            logger.error(f"生成缓存键失败: {str(e)}")
            return None
    
    def get(self, template_path, data):
        """获取缓存结果"""
        cache_key = self._generate_cache_key(template_path, data)
        if not cache_key or cache_key not in self.cache_index:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.dwg")
        if not os.path.exists(cache_file):
            # 缓存文件不存在，删除索引条目
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        logger.info(f"找到缓存文件: {cache_file}")
        return cache_file
    
    def put(self, template_path, data, output_path):
        """添加缓存结果"""
        cache_key = self._generate_cache_key(template_path, data)
        if not cache_key:
            return None
        
        # 检查输出文件是否存在
        if not os.path.exists(output_path):
            logger.error(f"输出文件不存在，无法缓存: {output_path}")
            return None
        
        # 复制输出文件到缓存目录
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.dwg")
        try:
            import shutil
            shutil.copy2(output_path, cache_file)
            
            # 更新缓存索引
            self.cache_index[cache_key] = {
                'created_at': time.time(),
                'file_path': cache_file
            }
            
            # 如果缓存超过最大大小，删除最旧的条目
            if len(self.cache_index) > self.max_size:
                self._cleanup_cache()
            
            # 保存缓存索引
            self._save_cache_index()
            
            logger.info(f"已添加缓存文件: {cache_file}")
            return cache_file
        except Exception as e:
            logger.error(f"添加缓存失败: {str(e)}")
            return None
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        # 按创建时间排序
        sorted_cache = sorted(self.cache_index.items(), 
                              key=lambda x: x[1]['created_at'])
        
        # 删除最旧的条目，直到缓存大小符合要求
        while len(sorted_cache) > self.max_size:
            oldest_key, oldest_entry = sorted_cache.pop(0)
            try:
                # 删除缓存文件
                cache_file = oldest_entry['file_path']
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    logger.info(f"已删除过期缓存文件: {cache_file}")
                
                # 从索引中删除
                del self.cache_index[oldest_key]
            except Exception as e:
                logger.error(f"删除过期缓存失败: {str(e)}")
        
        # 保存更新后的索引
        self._save_cache_index()

# 创建缓存实例
dwg_file_cache = DwgFileCache()

def update_dwg_attribute(template_path, output_path, data, use_cache=True):
    """更新DWG文件属性
    
    优化版本：改进了AutoCAD COM对象的获取和管理方式，优化了文本对象的查找和更新算法，
    实现了更高效的批量属性更新，添加了更健壮的错误处理机制，优化了文件缓存策略。
    
    Args:
        template_path: DWG模板文件路径
        output_path: 输出文件路径
        data: 属性数据字典或列表
        use_cache: 是否使用缓存
        
    Returns:
        (success, message): 成功状态和消息
    """
    # 检查缓存
    if use_cache:
        cached_file = dwg_file_cache.get(template_path, data)
        if cached_file:
            logger.info(f"使用缓存文件: {cached_file}")
            try:
                # 复制缓存文件到输出路径
                import shutil
                shutil.copy2(cached_file, output_path)
                logger.info(f"已从缓存复制到输出路径: {output_path}")
                return True, "使用缓存文件操作成功"
            except Exception as e:
                logger.error(f"使用缓存文件失败: {str(e)}")
                # 继续处理，不使用缓存
    
    acad = None
    doc = None
    success = False
    message = ""
    try:
        # 确保COM初始化在主线程运行
        logger.info("开始COM初始化")
        # 初始化COM安全设置
        try:
            pythoncom.CoInitialize()
        except:
            pass
        
        # 定义内部函数，用于获取AutoCAD实例
        def get_acad_application(max_retries=3, retry_delay=2.0):
            """获取AutoCAD应用程序实例，支持重试机制"""
            for attempt in range(max_retries):
                try:
                    # 尝试获取已运行的AutoCAD实例
                    acad = win32com.client.GetActiveObject("AutoCAD.Application")
                    logger.info("成功连接到现有的AutoCAD实例")
                    return acad
                except Exception:
                    try:
                        # 如果没有运行的实例，尝试启动新实例
                        acad = win32com.client.Dispatch("AutoCAD.Application")
                        acad.Visible = True  # 设置为可见
                        time.sleep(3)  # 增加等待时间确保应用程序完全初始化
                        # 尝试访问Documents集合以确保应用程序已准备就绪
                        try:
                            _ = acad.Documents
                        except:
                            time.sleep(2)  # 如果失败，额外等待
                        logger.info("成功启动新的AutoCAD实例")
                        return acad
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"尝试连接AutoCAD失败 ({attempt + 1}/{max_retries})，等待 {retry_delay} 秒后重试...")
                            time.sleep(retry_delay)
                        else:
                            logger.error(f"无法连接到AutoCAD应用程序: {str(e)}")
                            logger.error("请确保：\n1. AutoCAD已正确安装且以管理员权限运行\n2. AutoCAD没有处于未响应状态\n3. 您有足够的权限运行AutoCAD\n4. DCOM设置允许程序访问AutoCAD")
                            return None
            return None
            
        # 使用改进的AutoCAD实例获取函数
        acad = get_acad_application(max_retries=3, retry_delay=2.0)
        if not acad:
            raise Exception("无法连接到AutoCAD应用程序，请确保AutoCAD已正确安装且以管理员权限运行")
            
        logger.info(f"成功连接AutoCAD")
        
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
        
        # 验证文件是否为有效的DWG文件
        try:
            with open(template_path, 'rb') as f:
                # 读取文件头部字节
                header = f.read(6)
                # 检查DWG文件头部标识
                if not (header.startswith(b'AC10') or header.startswith(b'AC18') or header.startswith(b'AC24')):
                    logger.error(f"文件不是有效的DWG文件: {template_path}")
                    raise ValueError(f"文件不是有效的DWG文件: {template_path}")
            logger.info(f"文件验证通过: {template_path}")
        except Exception as e:
            logger.error(f"验证DWG文件失败: {str(e)}")
            raise ValueError(f"验证DWG文件失败: {str(e)}")
        
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
        
        # 更新文本对象属性 - 优化版本
        updated_count = 0
        start_time = time.time()
        
        # 预处理所有字段值，确保都是字符串
        processed_data = {}
        for field_name, field_value in data.items():
            if field_value is None:
                processed_data[field_name] = ""
            elif not isinstance(field_value, str):
                processed_data[field_name] = str(field_value)
            else:
                processed_data[field_name] = field_value
        
        try:
            # 只获取一次模型空间
            model_space = doc.ModelSpace
            
            # 创建两个索引：文本对象索引和属性块索引
            text_objects_index = {}
            block_refs = []
            logger.info(f"开始索引对象，总对象数: {model_space.Count}")
            
            # 减少日志输出频率，提高性能
            log_interval = max(1, model_space.Count // 20)
            batch_size = 100  # 批处理大小
            
            # 第一阶段：快速索引所有对象
            for i in range(model_space.Count):
                try:
                    obj = model_space.Item(i)
                    obj_name = obj.ObjectName
                    
                    # 处理文本对象
                    if obj_name == 'AcDbText':
                        try:
                            text_string = obj.TextString.strip()
                            # 只索引需要更新的字段
                            if text_string in processed_data:
                                text_objects_index[text_string] = obj
                        except Exception:
                            # 减少错误日志，提高性能
                            pass
                    # 处理块引用（属性块）
                    elif obj_name == "AcDbBlockReference" and hasattr(obj, 'HasAttributes') and obj.HasAttributes:
                        block_refs.append(obj)
                except Exception:
                    # 减少错误日志，提高性能
                    pass
                
                # 每处理batch_size个对象，更新一次进度
                if i > 0 and i % batch_size == 0:
                    logger.info(f"已索引 {i}/{model_space.Count} 个对象，找到 {len(text_objects_index)} 个文本对象和 {len(block_refs)} 个块引用")
            
            # 第二阶段：处理属性块
            logger.info(f"开始处理 {len(block_refs)} 个块引用的属性")
            block_attribs_processed = 0
            
            # 记录所有可用的属性标签
            all_tags = set()
            attrib_objects_index = {}
            
            # 批量处理块引用
            for i, entity in enumerate(block_refs):
                try:
                    for attrib in entity.GetAttributes():
                        tag_name = attrib.TagString
                        all_tags.add(tag_name)
                        
                        # 如果是需要更新的属性，加入索引
                        if tag_name in processed_data:
                            attrib_objects_index[tag_name] = attrib
                            block_attribs_processed += 1
                except Exception:
                    # 减少错误日志，提高性能
                    pass
                
                # 每处理batch_size个块引用，更新一次进度
                if i > 0 and i % batch_size == 0:
                    logger.info(f"已处理 {i}/{len(block_refs)} 个块引用，找到 {block_attribs_processed} 个可更新的属性")
            
            # 合并两种索引的统计信息
            logger.info(f"索引完成，找到 {len(text_objects_index)} 个可更新的文本对象和 {len(attrib_objects_index)} 个可更新的属性")
            
            # 第三阶段：批量更新所有对象
            # 更新文本对象
            for field_name, field_value in processed_data.items():
                # 更新文本对象
                if field_name in text_objects_index:
                    try:
                        text_objects_index[field_name].TextString = field_value
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"更新文本对象 {field_name} 时出错: {str(e)}")
                
                # 更新属性对象
                if field_name in attrib_objects_index:
                    try:
                        attrib_objects_index[field_name].TextString = field_value
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"更新属性对象 {field_name} 时出错: {str(e)}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"共更新了 {updated_count} 个字段，耗时: {elapsed_time:.2f}秒")
        except Exception as e:
            logger.error(f"访问或更新模型空间时出错: {str(e)}")
            raise
        
        # 保存为新文件（优化保存策略）
        logger.info(f"开始保存DWG文件到: {output_path}")
        save_start_time = time.time()
        
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
                # 尝试使用不同的文件名
                original_output_path = output_path
                output_path = f"{os.path.splitext(output_path)[0]}_{int(time.time())}.dwg"
                logger.info(f"将使用新的输出路径: {output_path}")
        
        # 保存文件（添加重试机制）
        max_save_attempts = 3
        for save_attempt in range(1, max_save_attempts + 1):
            try:
                # 使用SaveAs方法保存文件
                doc.SaveAs(output_path)
                save_time = time.time() - save_start_time
                logger.info(f"文件保存成功，耗时: {save_time:.2f}秒")
                success = True
                break  # 保存成功，跳出循环
            except Exception as e:
                logger.error(f"保存文件尝试 {save_attempt}/{max_save_attempts} 失败: {str(e)}")
                if save_attempt == max_save_attempts:
                    raise  # 重试次数用尽，重新抛出异常
                time.sleep(1)  # 等待一秒后重试
        
        # 添加到缓存
        if success and use_cache:
            try:
                dwg_file_cache.put(template_path, data, output_path)
                logger.info("文件已添加到缓存")
            except Exception as e:
                logger.warning(f"添加文件到缓存失败: {str(e)}")
        
        return True, output_path
        
    except Exception as e:
        logger.error(f"处理DWG文件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)
    finally:
        # 关闭文档但不退出AutoCAD
        try:
            if doc:
                doc.Close(False)  # False表示不保存
                logger.info("已关闭文档")
        except Exception as e:
            logger.error(f"关闭文档失败: {str(e)}")
        
        # 释放COM资源
        try:
            doc = None
            acad = None
            pythoncom.CoUninitialize()
            logger.info("COM资源已释放")
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
        
        # 获取缓存控制参数
        use_cache = request.form.get('use_cache', 'true').lower() != 'false'
        logger.info(f"缓存控制: {'启用' if use_cache else '禁用'}")
        
        # 更新DWG文件
        success, message = update_dwg_attribute(
            os.path.abspath(template_path),
            os.path.abspath(output_path),
            data,
            use_cache=use_cache
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