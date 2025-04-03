#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import cv2
import numpy as np
import logging
import json
from PIL import Image
from loguru import logger
import subprocess
import sys

# 检查PaddleOCR是否可用
PADDLE_OCR_AVAILABLE = False
paddle_ocr = None

try:
    logger.info("正在初始化PaddleOCR...")
    from paddleocr import PaddleOCR
    # 使用国内源加速下载
    paddle_ocr = PaddleOCR(
        use_angle_cls=True, 
        lang="ch", 
        show_log=False,
        use_gpu=False,
        enable_mkldnn=True,
        # 使用国内镜像加速
        download_from_url=True,
        locale='ch'
    )
    PADDLE_OCR_AVAILABLE = True
    logger.info("PaddleOCR已成功加载")
except ImportError as e:
    logger.error(f"导入PaddleOCR时出错: {str(e)}")
    logger.warning("请安装PaddleOCR: pip install paddleocr")
except Exception as e:
    logger.error(f"初始化PaddleOCR时出错: {str(e)}")
    logger.error(f"错误类型: {type(e).__name__}")
    
    # 尝试查看详细错误
    import traceback
    error_details = traceback.format_exc()
    logger.error(f"详细错误信息:\n{error_details}")

def check_paddle_ocr_available():
    """检查PaddleOCR是否可用"""
    global PADDLE_OCR_AVAILABLE, paddle_ocr
    try:
        if PADDLE_OCR_AVAILABLE and paddle_ocr:
            # 执行一个简单操作验证PaddleOCR是否可用
            try:
                logger.info("测试PaddleOCR是否正常工作...")
                # 尝试获取模型信息
                model_info = paddle_ocr.model_info
                logger.info("PaddleOCR状态正常")
                return True
            except Exception as e:
                logger.error(f"PaddleOCR初始化成功但测试失败: {str(e)}")
                # 尝试重新初始化
                try:
                    paddle_ocr = PaddleOCR(
                        use_angle_cls=True, 
                        lang="ch", 
                        show_log=False,
                        use_gpu=False,
                        enable_mkldnn=True
                    )
                    logger.info("PaddleOCR重新初始化成功")
                    return True
                except Exception as re_init_error:
                    logger.error(f"PaddleOCR重新初始化失败: {str(re_init_error)}")
                    PADDLE_OCR_AVAILABLE = False
                    return False
        else:
            logger.warning("PaddleOCR不可用")
            return False
    except Exception as e:
        logger.error(f"检查PaddleOCR可用性时出错: {str(e)}")
        return False

# 启动时检查PaddleOCR是否可用
if not PADDLE_OCR_AVAILABLE:
    logger.warning("⚠️ PaddleOCR不可用，图像识别功能将无法正常工作")
    logger.warning("请安装PaddleOCR: pip install paddleocr")
else:
    logger.info("✅ PaddleOCR已就绪，图像识别功能可以正常使用")

def preprocess_image(image):
    """预处理图像用于OCR识别，特别针对中文文档优化"""
    # 转为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 增强对比度 - 使用CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 应用高斯模糊减少噪点
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # 使用自适应阈值处理增强文本轮廓
    # 对中文字符，使用稍大的block size以更好地处理复杂字符
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 8
    )
    
    # 应用形态学操作清理噪点
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # 可选：降噪处理
    denoised = cv2.fastNlMeansDenoising(opening, None, 10, 7, 21)
    
    # 增加一些缩放以便更好地识别
    # 对中文文本，适当放大可以提高识别率
    scaled = cv2.resize(denoised, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    
    # 记录预处理完成状态
    logger.info("图像预处理完成: 灰度化、对比度增强、降噪和缩放")
    
    return scaled

def extract_text_using_paddle_ocr(image_path):
    """
    仅使用PaddleOCR从图像中提取文本
    
    Args:
        image_path: 图像路径
        
    Returns:
        提取的文本字符串，如果提取失败则返回空字符串
    """
    logger = logging.getLogger('GreenScore')
    
    # 检查PaddleOCR是否可用
    if not PADDLE_OCR_AVAILABLE:
        error_msg = "PaddleOCR未正确安装或初始化失败"
        logger.error(error_msg)
        raise RuntimeError(f"PaddleOCR: {error_msg}")
    
    try:
        logger.info(f"使用PaddleOCR处理图像: {type(image_path)}")
        
        # 使用PaddleOCR处理图像
        if hasattr(image_path, 'read'):
            # 如果是文件对象，获取字节数据
            image_data = image_path.read()
            image_path.seek(0)  # 重置文件指针
            
            # 保存到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(image_data)
            
            logger.info(f"将图像数据保存到临时文件: {temp_path}")
            result = paddle_ocr.ocr(temp_path, cls=True)
            
            # 处理完成后删除临时文件
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"删除临时文件时出错: {str(e)}")
        else:
            # 直接处理图像路径
            result = paddle_ocr.ocr(image_path, cls=True)
        
        # 检查结果
        if not result or len(result) == 0:
            logger.warning("PaddleOCR未返回任何结果")
            return ""
            
        # 提取文本
        extracted_text = ""
        for line in result:
            if not line:
                continue
                
            for word_info in line:
                if len(word_info) < 2:
                    continue
                    
                # word_info结构: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)]
                try:
                    text = word_info[1][0]  # 提取文本内容
                    if text:
                        extracted_text += text + " "
                except (IndexError, TypeError) as e:
                    logger.warning(f"处理OCR结果时出错: {str(e)}, word_info: {word_info}")
                    continue
        
        # 去除多余空格并整理文本
        extracted_text = extracted_text.strip()
        
        # 记录提取文本的字符数
        char_count = len(extracted_text)
        logger.info(f"成功从图像提取文本，共{char_count}个字符")
        
        if char_count == 0:
            logger.warning("提取的文本为空，可能识别失败")
            return ""
            
        return extracted_text
        
    except Exception as e:
        logger.error(f"使用PaddleOCR提取文本时出错: {str(e)}")
        return ""

def detect_table_structure(text_blocks):
    """检测文本块是否构成表格结构"""
    if not text_blocks or len(text_blocks) < 5:
        return False
        
    # 1. 计算相邻文本块的y坐标差异
    y_diffs = []
    for i in range(1, len(text_blocks)):
        y_diff = abs(text_blocks[i]['y_center'] - text_blocks[i-1]['y_center'])
        y_diffs.append(y_diff)
    
    if not y_diffs:
        return False
        
    # 2. 检查是否有一组接近的y坐标（表格行）
    # 计算标准差，标准差小表示y坐标分布集中，可能是表格行
    mean_y = sum(y_diffs) / len(y_diffs)
    std_y = (sum((y - mean_y) ** 2 for y in y_diffs) / len(y_diffs)) ** 0.5
    
    # 3. 检查是否有数字/单位模式（表格特征）
    number_count = 0
    unit_pattern = re.compile(r'[㎡|m²|平方米|%]')
    units_count = 0
    
    for block in text_blocks:
        if re.search(r'\d+\.?\d*', block['text']):
            number_count += 1
        if unit_pattern.search(block['text']):
            units_count += 1
    
    # 如果数字和单位比例高，可能是表格
    number_ratio = number_count / len(text_blocks)
    
    # 4. 检查文本长度分布
    text_lengths = [len(block['text']) for block in text_blocks]
    mean_len = sum(text_lengths) / len(text_lengths)
    
    # 表格一般有较短的文本长度
    short_text_ratio = len([l for l in text_lengths if l < 15]) / len(text_lengths)
    
    # 综合判断
    is_table = (std_y < 20 and number_ratio > 0.3) or (short_text_ratio > 0.6 and number_ratio > 0.25)
    
    if is_table:
        logger.info(f"表格特征: 标准差={std_y:.2f}, 数字比例={number_ratio:.2f}, 短文本比例={short_text_ratio:.2f}")
    
    return is_table

def process_table_text(text_blocks):
    """处理表格文本，尝试保留表格结构"""
    if not text_blocks:
        return ""
        
    # 1. 检测行
    # 按y坐标将文本块分组为行
    rows = []
    current_row = [text_blocks[0]]
    y_threshold = 20  # 同一行的y坐标差异阈值
    
    for i in range(1, len(text_blocks)):
        if abs(text_blocks[i]['y_center'] - current_row[0]['y_center']) < y_threshold:
            # 同一行
            current_row.append(text_blocks[i])
        else:
            # 新行
            rows.append(current_row)
            current_row = [text_blocks[i]]
    
    # 添加最后一行
    if current_row:
        rows.append(current_row)
    
    # 2. 处理每一行
    processed_text = ""
    for row in rows:
        # 按x坐标排序，从左到右
        row.sort(key=lambda block: block['box'][0][0])  # 左上角x坐标
        
        # 合并行文本
        row_text = " ".join(block['text'] for block in row)
        processed_text += row_text + "\n"
    
    return processed_text

def extract_text(image):
    """
    从图像中提取文本，仅使用PaddleOCR
    
    Args:
        image: 图像路径、PIL图像对象或OpenCV图像数组
        
    Returns:
        str: 提取的文本，如果提取失败返回空字符串
    """
    logger = logging.getLogger('GreenScore')
    
    try:
        # 检查PaddleOCR是否可用
        if not PADDLE_OCR_AVAILABLE:
            error_msg = "PaddleOCR不可用，OCR功能无法使用"
            logger.error(error_msg)
            raise RuntimeError(f"PaddleOCR: {error_msg}")
            
        # 使用PaddleOCR提取文本
        text = extract_text_using_paddle_ocr(image)
        if text:
            return text
        else:
            logger.error("PaddleOCR提取文本失败")
            return ""
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"提取文本时出错: {error_msg}")
        
        if "PaddleOCR" in error_msg:
            logger.error(f"PaddleOCR错误: {error_msg}")
            raise RuntimeError(f"PaddleOCR: {error_msg}")
        
        return ""

def parse_project_info_from_text(text):
    """从OCR文本内容中提取项目相关信息"""
    if not text:
        return None
    
    # 记录OCR文本长度
    logger.info(f"开始从文本内容中解析项目信息, 文本长度: {len(text)}")
    
    # 定义需要提取的信息模式
    info_patterns = {
        "总建筑面积": [
            r"总建筑面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"建筑总面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总计[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "地上建筑面积": [
            r"地上(?:建筑)?面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?", 
            r"地上部分[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "地下建筑面积": [
            r"地下(?:建筑)?面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?", 
            r"地下部分[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"地下室面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"地下室建筑面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "建筑层数": [
            r"(?:建筑层数|层数)[:：]?\s*(.+?)(?:\n|$)",
            r"地上(\d+)层[,，]?地下(\d+)层",
            r"(\d+)(?:层|F)(?:/|、|-)?(?:地下)?(\d+)(?:层|F)"
        ],
        "建筑高度": [
            r"(?:建筑高度|建筑物高度)[:：]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"高度[:：]?\s*([0-9,.]+)\s*(?:米|m)?"
        ],
        "容积率": [
            r"容积率[:：]?\s*([0-9,.]+)",
            r"容积率[:：]?\s*约?([0-9,.]+)"
        ],
        "建筑密度": [
            r"建筑密度[:：]?\s*([0-9,.]+)\s*%?",
            r"建筑密度[:：]?\s*约?([0-9,.]+)\s*%?"
        ],
        "基底面积": [
            r"基底面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"建筑基底面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"基底面积\s*([0-9,.]+)(?:m²|m2|㎡|平方米)?",
            r"地上建筑基底面积\s*[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "绿地面积": [
            r"绿地面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"绿地面积\s*([0-9,.]+)(?:m²|m2|㎡|平方米)?",
            r"绿化面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ]
    }
    
    # 表格样式匹配模式（处理表格中的数据）
    table_patterns = {
        "总建筑面积": [
            r"总[计建]?[筑建]?面积\D+(\d+[,.\d]*)",
            r"规划总建筑面积\D+(\d+[,.\d]*)",
            r"总建筑面积\D+(\d+[,.\d]*)",
            r"总面积\D+(\d+[,.\d]*)",
        ],
        "地上建筑面积": [
            r"地上[总计建筑]*面积\D+(\d+[,.\d]*)",
            r"计容建筑面积\D+(\d+[,.\d]*)",
        ],
        "地下建筑面积": [
            r"地下[总计建筑]*面积\D+(\d+[,.\d]*)",
            r"地下室面积\D+(\d+[,.\d]*)",

        ],
        "建筑层数": [
            r"地上(\d+)层[,，]?地下(\d+)层",
            r"(\d+)(?:层|F)(?:/|、|-)?(?:地下)?(\d+)(?:层|F)"
        ],
        "容积率": [

            r"容积率\D+(\d+[,.\d]*)"
        ],
        "建筑密度": [
            r"建筑密度\D+(\d+[,.\d]*)"
        ],
        "绿地率": [

            r"绿地率\D+(\d+[,.\d]*)"
        ],
        "基底面积": [

            r"基底面积\D+(\d+[,.\d]*)"
        ],
        "绿地面积": [

            r"绿地面积\D+(\d+[,.\d]*)"
        ]
    }
    
    # 提取项目信息
    project_info = {}
    
    # 使用标准正则表达式匹配
    for key, patterns in info_patterns.items():
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 0:
                        project_info[key] = value
                        logger.debug(f"通过标准模式提取到{key}: {value}")
                        break
            except Exception as e:
                logger.warning(f"匹配{key}的模式{pattern}出错: {str(e)}")
    
    # 使用表格样式匹配
    for key, patterns in table_patterns.items():
        if key not in project_info:  # 如果标准模式没有提取到，尝试表格模式
            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip().replace(',', '')
                        if value and len(value) > 0:
                            project_info[key] = value
                            logger.debug(f"通过表格模式提取到{key}: {value}")
                            break
                except Exception as e:
                    logger.warning(f"匹配表格中{key}的模式{pattern}出错: {str(e)}")
    
    # 使用通用模式提取键值对
    # 寻找"xxxx: yyyy"或"xxxx：yyyy"模式的文本
    general_patterns = [
        r'([^:：\n]{2,10})[:：]\s*([^:：\n]{2,30})',
        r'([^:：\n]{2,15})\s+(\d+\.?\d*)\s*(?:平方米|㎡|m²|m2)'
    ]
    
    for pattern in general_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # 跳过已提取的键或值太短的情况
                if key in project_info or len(value) < 2:
                    continue
                    
                # 过滤不相关的键
                if any(x in key for x in ['http', 'www', '时间', '日期', '查询', '页码', '预览', '打印']):
                    continue
                    
                # 对于疑似面积的键，检查值是否为数字
                if any(x in key for x in ['面积', '用地', '容积', '建筑']):
                    try:
                        # 尝试解析为数字
                        float(value.replace(',', ''))
                        project_info[key] = value
                        logger.debug(f"通过通用模式提取到{key}: {value}")
                    except ValueError:
                        pass
                else:
                    project_info[key] = value
                    logger.debug(f"通过通用模式提取到{key}: {value}")
            except Exception as e:
                logger.warning(f"提取通用键值对时出错: {str(e)}")
    
    logger.info(f"成功解析出项目信息 {len(project_info)} 项")
    logger.debug(f"提取的项目信息: {project_info}")
    
    # 特别匹配文档示例中的"五、建筑密度"后面的基底面积表示方式
    if '基底面积' not in project_info:
        # 根据示例中的"四、基底面积 4376.50m"格式匹配
        specific_base_match = re.search(r'四[、.．,，]\s*基底面积\s+(\d+\.?\d*)', text)
        if specific_base_match:
            project_info['基底面积'] = specific_base_match.group(1) + " 平方米"
            logger.debug(f"成功从特定格式提取基底面积: {project_info['基底面积']}")
        
    # 特别匹配文档示例中的"六、绿地面积 6573.72m"格式
    if '绿地面积' not in project_info:
        specific_green_match = re.search(r'六[、.．,，]\s*绿地面积\s+(\d+\.?\d*)', text)
        if specific_green_match:
            project_info['绿地面积'] = specific_green_match.group(1) + " 平方米"
            logger.debug(f"成功从特定格式提取绿地面积: {project_info['绿地面积']}")
            
    # 查找更宽泛的模式
    if '基底面积' not in project_info:
        general_base_match = re.search(r'基底面积\D+(\d+\.?\d*)', text)
        if general_base_match:
            project_info['基底面积'] = general_base_match.group(1) + " 平方米"
            logger.debug(f"成功从一般格式提取基底面积: {project_info['基底面积']}")
            
    if '绿地面积' not in project_info:
        general_green_match = re.search(r'绿地面积\D+(\d+\.?\d*)', text)
        if general_green_match:
            project_info['绿地面积'] = general_green_match.group(1) + " 平方米"
            logger.debug(f"成功从一般格式提取绿地面积: {project_info['绿地面积']}")
            
    # 最后尝试从原始文本中直接提取数字
    if '基底面积' not in project_info and '五、建筑密度' in text and '六、绿地' in text:
        # 在"五、建筑密度"和"六、绿地"之间查找数字
        density_to_green = re.search(r'五、建筑密度[^六]+六、绿地', text)
        if density_to_green:
            section_text = density_to_green.group(0)
            # 查找这段文本中的数字
            numbers = re.findall(r'(\d+\.?\d*)\s*(?:m²|㎡|平方米)?', section_text)
            if numbers and len(numbers) >= 2:  # 假设第二个数字可能是基底面积
                project_info['基底面积'] = numbers[1] + " 平方米"
                logger.debug(f"从上下文推断基底面积: {project_info['基底面积']}")
                
    # 同样尝试为绿地面积
    if '绿地面积' not in project_info and '六、绿地' in text and '七、' in text:
        green_to_next = re.search(r'六、绿地[^七]+七、', text)
        if green_to_next:
            section_text = green_to_next.group(0)
            numbers = re.findall(r'(\d+\.?\d*)\s*(?:m²|㎡|平方米)?', section_text)
            if numbers and len(numbers) >= 1:
                project_info['绿地面积'] = numbers[0] + " 平方米"
                logger.debug(f"从上下文推断绿地面积: {project_info['绿地面积']}")
    
    return project_info

def extract_image_info(image_path):
    """
    仅使用PaddleOCR从图像中提取项目信息
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        dict: 从图像中提取的项目信息字典，提取失败返回空字典
    """
    logger = logging.getLogger('GreenScore')
    
    # 检查PaddleOCR是否可用
    if not PADDLE_OCR_AVAILABLE:
        error_msg = "PaddleOCR未正确安装或初始化失败"
        logger.error(error_msg)
        # 不抛出异常，返回空字典
        return {}
    
    try:
        # 使用新的函数提取文本和项目信息
        result = extract_image_info_with_raw_text(image_path)
        
        # 如果结果为None或者不是字典，返回空字典
        if not result or not isinstance(result, dict) or 'project_info' not in result:
            logger.error("提取项目信息格式错误")
            return {}
            
        # 返回项目信息
        return result['project_info'] or {}
        
    except Exception as e:
        logger.error(f"提取图像信息时出错: {str(e)}")
        return {}

# 辅助函数：评估提取的文本质量
def evaluate_text_quality(text):
    """简单评估文本质量的函数"""
    if not text:
        return 0
        
    # 计算中文字符比例
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    text_length = len(text.strip())
    
    if text_length == 0:
        return 0
        
    chinese_ratio = chinese_chars / text_length
    
    # 评分标准：考虑文本长度和中文比例
    score = text_length * 0.3 + chinese_ratio * 100
    
    # 加分：如果包含关键词
    keywords = ["项目名称", "建设单位", "设计单位", "总建筑面积", "地址", "容积率", "面积"]
    for keyword in keywords:
        if keyword in text:
            score += 20
            
    return score

# 辅助函数：仅应用CLAHE对比度增强
def clahe_only(image):
    """仅应用CLAHE对比度增强"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)
    
# 辅助函数：二值化处理
def binarize_only(image):
    """仅应用二值化处理"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def extract_image_info_with_raw_text(image_path):
    """
    仅使用PaddleOCR从图像中提取项目信息和原始文本
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        包含项目信息和原始文本的字典，格式为:
        {
            'project_info': {提取的项目信息字典},
            'raw_text': 原始提取的文本
        }
        如果提取失败，返回空字典 {'project_info': {}, 'raw_text': ''}
    """
    logger = logging.getLogger('GreenScore')
    
    # 防止返回None导致的解包错误
    default_return = {'project_info': {}, 'raw_text': ''}
    
    # 检查PaddleOCR是否可用
    if not PADDLE_OCR_AVAILABLE:
        error_msg = "PaddleOCR未正确安装或初始化失败"
        logger.error(error_msg)
        # 不抛出异常，而是返回默认值
        return default_return
    
    try:
        # 使用PaddleOCR提取文本
        extracted_text = extract_text_using_paddle_ocr(image_path)
        
        if not extracted_text:
            logger.warning("文本提取失败，无法提取项目信息")
            return default_return
            
        # 记录字符统计信息
        char_count = len(extracted_text)
        chinese_count = sum(1 for c in extracted_text if '\u4e00' <= c <= '\u9fff')
        
        logger.info(f"成功提取文本 - 总字符数: {char_count}, 中文字符数: {chinese_count}")
        logger.debug(f"提取的文本前500字符: {extracted_text[:500]}")
        
        # 解析文本中的项目信息
        project_info = parse_project_info_from_text(extracted_text)
        
        # 检查提取的项目信息是否足够
        if not project_info:
            logger.warning("无法从文本中提取有效的项目信息")
            return {
                'project_info': {},
                'raw_text': extracted_text
            }
        
        logger.info(f"成功从文本中提取项目信息: {len(project_info)}项")
        
        # 特别提取总建筑面积、地上面积、地下面积
        if '建筑面积' in extracted_text:
            # 尝试提取总建筑面积
            total_area_match = re.search(r'总建筑面积[：:]\s*(\d+\.?\d*)\s*(?:平方米|㎡)?', extracted_text)
            if total_area_match:
                project_info['总建筑面积'] = total_area_match.group(1) + " 平方米"
                
            # 尝试提取地上建筑面积
            above_area_match = re.search(r'地上(?:建筑)?面积[：:]\s*(\d+\.?\d*)\s*(?:平方米|㎡)?', extracted_text)
            if above_area_match:
                project_info['地上建筑面积'] = above_area_match.group(1) + " 平方米"
                
            # 尝试提取地下建筑面积
            under_area_match = re.search(r'地下(?:建筑)?面积[：:]\s*(\d+\.?\d*)\s*(?:平方米|㎡)?', extracted_text)
            if under_area_match:
                project_info['地下建筑面积'] = under_area_match.group(1) + " 平方米"
                
        # 特别提取基底面积
        base_area_patterns = [
            r'[^规划]*基底面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?',
            r'四[、.．,，]\s*基底面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?',
            r'建筑基底面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?'
        ]
        for pattern in base_area_patterns:
            base_area_match = re.search(pattern, extracted_text)
            if base_area_match:
                project_info['基底面积'] = base_area_match.group(1) + " 平方米"
                logger.debug(f"成功提取基底面积: {project_info['基底面积']}")
                break
                
        # 特别提取绿地面积
        green_area_patterns = [
            r'[^绿][^地][^率]*绿地面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?',
            r'六[、.．,，]\s*绿地面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?',
            r'绿化面积[：:]*\s*(\d+\.?\d*)\s*(?:平方米|㎡|m²)?'
        ]
        for pattern in green_area_patterns:
            green_area_match = re.search(pattern, extracted_text)
            if green_area_match:
                project_info['绿地面积'] = green_area_match.group(1) + " 平方米"
                logger.debug(f"成功提取绿地面积: {project_info['绿地面积']}")
                break
        
        # 添加原始文本到结果中
        result = {
            'project_info': project_info,
            'raw_text': extracted_text
        }
        
        return result
        
    except Exception as e:
        logger.error(f"提取图像信息时出错: {str(e)}")
        # 返回默认值而不是None，避免解包错误
        return default_return 