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
import base64
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查百度OCR API是否可用
BAIDU_OCR_AVAILABLE = False
baidu_ocr_client = None

# 获取百度OCR API配置
BAIDU_API_KEY = os.getenv('BAIDU_API_KEY', '')
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

def get_baidu_access_token():
    """
    获取百度AI开放平台的access_token
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    try:
        response = requests.post(url, params=params)
        result = response.json()
        if 'access_token' in result:
            return result['access_token']
        else:
            logger.error(f"获取百度access_token失败: {result}")
            return None
    except Exception as e:
        logger.error(f"获取百度access_token异常: {str(e)}")
        return None

# 初始化百度OCR客户端
try:
    logger.info("正在初始化百度OCR API...")
    if BAIDU_API_KEY and BAIDU_SECRET_KEY:
        access_token = get_baidu_access_token()
        if access_token:
            baidu_ocr_client = {
                'access_token': access_token,
                'expires_time': None  # 可以添加过期时间管理
            }
            BAIDU_OCR_AVAILABLE = True
            logger.info("百度OCR API已成功加载")
        else:
            logger.error("获取百度access_token失败")
    else:
        logger.error("百度OCR API密钥未配置")
except Exception as e:
    logger.error(f"初始化百度OCR API时出错: {str(e)}")
    logger.error(f"错误类型: {type(e).__name__}")
    
    # 尝试查看详细错误
    import traceback
    error_details = traceback.format_exc()
    logger.error(f"详细错误信息:\n{error_details}")

def check_baidu_ocr_available():
    """检查百度OCR API是否可用"""
    global BAIDU_OCR_AVAILABLE, baidu_ocr_client
    try:
        if BAIDU_OCR_AVAILABLE and baidu_ocr_client:
            # 验证access_token是否有效
            # 如果需要，可以在这里添加token过期检查和刷新逻辑
            return True
        else:
            logger.warning("百度OCR API不可用")
            return False
    except Exception as e:
        logger.error(f"检查百度OCR API可用性时出错: {str(e)}")
        return False

# 启动时检查百度OCR API是否可用
if not BAIDU_OCR_AVAILABLE:
    logger.warning("⚠️ 百度OCR API不可用，图像识别功能将无法正常工作")
    logger.warning("请在.env文件中配置BAIDU_API_KEY和BAIDU_SECRET_KEY")
else:
    logger.info("✅ 百度OCR API已就绪，图像识别功能可以正常使用")

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

def extract_text_using_baidu_ocr(image_path):
    """
    使用百度OCR API从图像中提取文本
    
    Args:
        image_path: 图像路径或文件对象
        
    Returns:
        提取的文本字符串，如果提取失败则返回空字符串
    """
    logger = logging.getLogger('GreenScore')
    
    # 检查百度OCR API是否可用
    if not BAIDU_OCR_AVAILABLE:
        error_msg = "百度OCR API未正确配置或初始化失败"
        logger.error(error_msg)
        raise RuntimeError(f"百度OCR API: {error_msg}")
    
    try:
        logger.info(f"使用百度OCR API处理图像: {type(image_path)}")
        
        # 准备图像数据
        if hasattr(image_path, 'read'):
            # 如果是文件对象，获取字节数据
            image_data = image_path.read()
            image_path.seek(0)  # 重置文件指针
        else:
            # 如果是文件路径，读取文件内容
            with open(image_path, 'rb') as f:
                image_data = f.read()
        
        # 进行Base64编码
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 调用百度OCR API
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={baidu_ocr_client['access_token']}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'image': image_base64,
            'language_type': 'CHN_ENG',  # 中英文混合
            'detect_direction': 'true',  # 检测文字方向
            'paragraph': 'true',         # 输出段落信息
            'probability': 'true'        # 返回识别结果中每一行的置信度
        }
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        # 检查结果
        if 'error_code' in result:
            logger.error(f"百度OCR API返回错误: {result['error_code']} - {result.get('error_msg', '')}")
            return ""
            
        if 'words_result' not in result or len(result['words_result']) == 0:
            logger.warning("百度OCR API未返回任何结果")
            return ""
            
        # 提取文本
        extracted_text = ""
        for word_info in result['words_result']:
            if 'words' in word_info:
                extracted_text += word_info['words'] + " "
        
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
        logger.error(f"使用百度OCR API提取文本时出错: {str(e)}")
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
    从图像中提取文本，使用百度OCR API
    
    Args:
        image: 图像路径、PIL图像对象或OpenCV图像数组
        
    Returns:
        str: 提取的文本，如果提取失败返回空字符串
    """
    logger = logging.getLogger('GreenScore')
    
    try:
        # 检查百度OCR API是否可用
        if not BAIDU_OCR_AVAILABLE:
            error_msg = "百度OCR API不可用，OCR功能无法使用"
            logger.error(error_msg)
            raise RuntimeError(f"百度OCR API: {error_msg}")
            
        # 使用百度OCR API提取文本
        text = extract_text_using_baidu_ocr(image)
        if text:
            return text
        else:
            logger.error("百度OCR API提取文本失败")
            return ""
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"提取文本时出错: {error_msg}")
        
        if "百度OCR API" in error_msg:
            logger.error(f"百度OCR API错误: {error_msg}")
            raise RuntimeError(f"百度OCR API: {error_msg}")
        
        return ""

def parse_project_info_from_text(text):
    """从OCR文本内容中提取项目相关信息"""
    if not text:
        return None
    
    # 记录OCR文本长度
    logger.info(f"开始从文本内容中解析项目信息, 文本长度: {len(text)}")
    
    # 提取项目信息
    project_info = {}
    
    # 新增表格特有字段匹配模式
    table_specific_fields = {
        "项目名称": [
            r"项目名称[：:]*\s*(.+?)(?:\s+建筑类型|\s+公共建筑|\s*$)",
            r"项目名称\s*(.+?)(?:\s*$|\n)"
        ],
        "建筑类型": [
            r"建筑类型[：:]*\s*([^:：\n]{2,15})(?:\s+公建类型|\s*$)",
            r"建筑类型\s*([^:：\n]{2,15})(?:\s+公建类型|\s*$)",
            r"建筑类型[：:]*\s*(居住建筑|公共建筑)"
        ],
        "公建类型": [
            r"公建类型[：:]*\s*([^:：\n]{2,15})(?:\s+气候区划|\s*$)",
            r"公建类型\s*([^:：\n]{2,15})(?:\s+气候区划|\s*$)",
            r"公共建筑类型[：:]*\s*([^:：\n]{2,15})(?:\s+气候区划|\s*$)",
            r"公建类型[：:]*\s*(办公|商业|医疗|教育|文化|体育|交通|其他)"
        ],
        "气候区划": [
            r"气候区划[：:]*\s*([IVX]{1,3})(?:\s|$)",
            r"建筑气候区划[：:]*\s*([IVX]{1,3})(?:\s|$)",
            r"气候分区[：:]*\s*([IVX]{1,3})(?:\s|$)",
            r"区划\s*([IVX]{1,3})(?:\s|$)"
        ],
        "集中绿地面积": [
            r"集中绿地面积[：:]*\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"集中绿地\s*([0-9,.]+)(?:m²|m2|㎡|平方米)?"
        ],
        "建筑层数": [
            r"建筑层数\s*(\d+)(?:层)?(?:/地下)?",
            r"建筑层数[：:]*\s*(\d+)(?:层)?(?:/地下)?",
            r"层数[：:]*\s*(\d+)(?:层)?(?:/地下)?"
        ],
        "绿地率": [
            r"绿地率[：:]*\s*([0-9,.]+)\s*%?(?:\s|$)",
            r"绿地率\s*([0-9,.]+)%?(?:\s|$)",
            r"绿化率[：:]*\s*([0-9,.]+)\s*%?(?:\s|$)"
        ],
        "规划绿地率指标要求": [
            r"规划绿地率指标要求[：:]*\s*([0-9,.]+)\s*%?",
            r"规划绿地率指标\s*([0-9,.]+)%?"
        ],
        "有无电梯": [
            r"有无电梯[：:]*\s*([有无是否])(?:\s|$)",
            r"电梯[：:]*\s*([有无是否])(?:\s|$)",
            r"有无电梯\s+([有无是否])(?:\s|$)"
        ],
        "有无地下车库": [
            r"有无地下车库[：:]*\s*([有无是否])(?:\s|$)",
            r"地下车库[：:]*\s*([有无是否])(?:\s|$)"
        ],
        "有无景观水体": [
            r"有无景观水体[：:]*\s*([有无是否])(?:\s|$)",
            r"景观水体[：:]*\s*([有无是否])(?:\s|$)",
            r"水体\s*([有无是否])(?:\s|$)"
        ],
        "绿地向公众开放": [
            r"绿地向公众开放[：:]*\s*([有无是否])(?:\s|$)",
            r"公众开放[：:]*\s*([有无是否])(?:\s|$)"
        ],
        "是否为全装修项目": [
            r"是否为全装修项目[：:]*\s*([有无是否])(?:\s|$)",
            r"全装修项目[：:]*\s*([有无是否])(?:\s|$)",
            r"全装修[：:]*\s*([有无是否])(?:\s|$)"
        ],
        "空调形式": [
            r"空调形式[：:]*\s*([^:：\n]{2,15})(?:\s+有无电梯|\s*$)",
            r"空调[：:]*\s*([^:：\n]{2,15})(?:\s+有无电梯|\s*$)",
            r"空调形式[：:]*\s*(集中式|分体式|中央|风冷|水冷|无|分体式空调)"
        ],
        "项目建设情况": [
            r"项目建设情况[：:]*\s*([^:：\n]{2,15})(?:\s+水体|\s*$)",
            r"建设情况[：:]*\s*([^:：\n]{2,15})(?:\s+水体|\s*$)",
            r"项目建设情况[：:]*\s*(新区建设|改建|扩建|旧区改建)"
        ]
    }
    
    # 首先处理表格特有字段
    for key, patterns in table_specific_fields.items():
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 0:
                        # 对提取的值进行清理和检查
                        # 检查是否包含其他字段的关键词(如"建筑气候"中混入了"办公")
                        if key == "气候区划" and len(value) > 3:
                            # 只保留罗马数字部分
                            roman_match = re.search(r'([IVX]{1,3})', value)
                            if roman_match:
                                value = roman_match.group(1)
                        elif key == "公建类型" and "气候" in value:
                            # 去除混入的"气候"关键词
                            value = re.sub(r'气候.*', '', value).strip()
                        elif key == "建筑类型" and "公建类型" in value:
                            # 去除混入的"公建类型"关键词
                            value = re.sub(r'公建类型.*', '', value).strip()
                        elif key == "空调形式" and "有无电梯" in value:
                            # 去除混入的"有无电梯"关键词
                            value = re.sub(r'有无电梯.*', '', value).strip()
                        elif key == "项目建设情况" and "水体" in value:
                            # 去除混入的"水体"关键词
                            value = re.sub(r'水体.*', '', value).strip()
                        
                        # 进一步针对有无景观水体进行优化
                        if key == "有无景观水体" and value in ["无", "是", "否"]:
                            project_info[key] = value
                            logger.debug(f"通过表格特定模式提取到{key}: {value}")
                            break
                        
                        # 其他通用的清理逻辑 
                        if value and len(value) > 0:
                            project_info[key] = value
                            logger.debug(f"通过表格特定模式提取到{key}: {value}")
                            break
            except Exception as e:
                logger.warning(f"匹配表格中{key}的模式{pattern}出错: {str(e)}")
    
    # 表格后处理：处理混合在一起的字段
    mixed_fields = {
        "公建类型": ["建筑气候", "办公"],
        "气候区划": ["III", "I", "II", "IV", "V", "VI", "VII"],
        "建筑类型": ["公共建筑", "居住建筑"],
        "有无电梯": ["有", "无"],
        "有无景观水体": ["有", "无"]
    }
    
    # 检查并纠正混合的字段
    for field, keywords in mixed_fields.items():
        # 跳过已经正确处理的字段
        if field in project_info and len(project_info[field]) <= 5:
            continue
            
        # 创建待处理字段列表，避免在遍历时修改字典
        fields_to_process = list(project_info.keys())
        
        # 处理混合在一起的字段
        for other_field in fields_to_process:
            if other_field != field and field not in project_info:
                for keyword in keywords:
                    if keyword in project_info[other_field]:
                        # 将关键词提取出来作为单独的字段
                        project_info[field] = keyword
                        logger.debug(f"从混合字段 {other_field} 中提取 {field}: {keyword}")
                        # 从原字段中移除这个关键词
                        project_info[other_field] = re.sub(r'\s*' + re.escape(keyword) + r'\s*', ' ', project_info[other_field]).strip()
                        break
    
    # 特殊处理：如果公建类型只提取到了"办公"
    if "公建类型" in project_info and project_info["公建类型"] == "办公":
        project_info["公建类型"] = "办公建筑"
        
    # 特殊处理：如果水体被提取为独立字段但值是"无"
    if "水体" in project_info and project_info["水体"] == "无":
        project_info["有无景观水体"] = "无"
        del project_info["水体"]
        
    # 特殊处理：如果提取到工程地点但没有有效内容，删除它
    if "工程地点" in project_info and len(project_info["工程地点"].strip()) < 2:
        del project_info["工程地点"]
    
    # 定义需要提取的信息模式
    info_patterns = {
        "总用地面积": [
            r"规划用地面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总用地面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"用地面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"净用地面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总用地面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"用地总面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"项目用地面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总用地\D*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"用地面积约\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"用地范围内面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"占地面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "总建筑面积": [
            r"总建筑面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"建筑总面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总计[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ],
        "地上建筑面积": [
            r"地上(?:建筑)?面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?", 
            r"地上部分[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"地上建筑面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"计容建筑面积[:：]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
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
            r"高度[:：]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"建筑高度[为是]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"建筑[物的]?高度约[为]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"设计高度[为]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"(?:建筑|楼|建筑物)?高(?:度)?[为是约]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"建筑物(?:高度)?[为是]?\s*([0-9,.]+)\s*(?:米|m)?",
            r"建筑高度\D+(\d+[,.\d]*)",
            r"(?:^|\s)高度\D*([0-9,.]+)\s*(?:米|m)?"
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
        ],
        "地面停车位": [
            r"地面停车位[数量个]?[:：]?\s*(\d+)\s*(?:个|辆)?",
            r"地面停车位[数量个]?[为是]?\s*(\d+)\s*(?:个|辆)?",
            r"(?:地面|室外)停车位?[数量个]?[:：]?\s*(\d+)\s*(?:个|辆)?",
            r"停车位[数量个]?[:：]?\s*(\d+)\s*(?:个|辆)?",
            r"实际建设车位\s*(\d+)\s*(?:个|辆)?",
            r"地面机动车停车位\s*(\d+)\s*(?:个|辆)?",
            r"地上停车位\s*(\d+)\s*(?:个|辆)?",
            r"地面规划停车位\s*(\d+)\s*(?:个|辆)?",
            r"(?:配置|配建|设置)(?:地面)?停车位\s*(\d+)\s*(?:个|辆)?",
            r"停车位共[计]?(\d+)[个辆]",
            r"机动车停车位[数量个]?[:：]?\s*(\d+)\s*(?:个|辆)?"
        ]
    }
    
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
    
    # 表格样式匹配模式（处理表格中的数据）
    table_patterns = {
        "总用地面积": [
            r"规划用地面积\D+(\d+[,.\d]*)",
            r"总用地面积\D+(\d+[,.\d]*)",
            r"用地面积\D+(\d+[,.\d]*)",
            r"净用地面积\D+(\d+[,.\d]*)",
            r"公共建筑用地面积\D+(\d+[,.\d]*)"
        ],
        "总建筑面积": [
            r"总[计建]?[筑建]?面积\D+(\d+[,.\d]*)",
            r"规划总建筑面积\D+(\d+[,.\d]*)",
            r"总建筑面积\D+(\d+[,.\d]*)",
            r"总面积\D+(\d+[,.\d]*)",
            r"公共建筑总建筑面积\D+(\d+[,.\d]*)"
        ],
        "地上建筑面积": [
            r"地上[总计建筑]*面积\D+(\d+[,.\d]*)",
            r"计容建筑面积\D+(\d+[,.\d]*)",
            r"地上\D+(\d+[,.\d]*)"
        ],
        "地下建筑面积": [
            r"地下[总计建筑]*面积\D+(\d+[,.\d]*)",
            r"地下室面积\D+(\d+[,.\d]*)",
            r"地下\D+(\d+[,.\d]*)"
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
        ],
        "建筑高度": [
            r"建筑高度\D+(\d+[,.\d]*)",
            r"m\s+(\d+[,.\d]*)",  # 匹配表格中的 m 23.7 格式
            r"建筑高度.*?(\d+\.\d+)\s*米?",
            r"高度\D+(\d+[,.\d]*)"
        ]
    }
    
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
    
    # 特别处理表格中的建筑高度（通常位于表格末尾）
    if '建筑高度' not in project_info:
        try:
            # 查找类似"建筑高度 m 23.7"这样的模式
            height_match = re.search(r'建筑高度\s*m\s*(\d+\.?\d*)', text, re.IGNORECASE)
            if height_match:
                value = height_match.group(1).strip()
                project_info['建筑高度'] = value + " 米"
                logger.debug(f"从表格末尾提取到建筑高度: {project_info['建筑高度']}")
            # 针对特定表格格式：最后一行包含"建筑高度" "m" "23.7"的格式
            elif "建筑高度" in text and "m" in text:
                # 尝试查找建筑高度附近的数字
                height_lines = [line for line in text.split('\n') if '建筑高度' in line or ('高度' in line and 'm' in line)]
                for height_line in height_lines:
                    number_match = re.search(r'(\d+\.?\d*)', height_line)
                    if number_match:
                        value = number_match.group(1).strip()
                        project_info['建筑高度'] = value + " 米"
                        logger.debug(f"从包含'建筑高度'的行提取到: {project_info['建筑高度']}")
                        break
            # 最后尝试直接搜索表格样式
            else:
                # 寻找数字+m的组合，通常在表格的数据列
                table_value_match = re.search(r'(\d+\.\d+)\s*(?:米|m)', text, re.IGNORECASE)
                if table_value_match:
                    value = table_value_match.group(1).strip()
                    project_info['建筑高度'] = value + " 米"
                    logger.debug(f"从表格数据列提取到建筑高度: {project_info['建筑高度']}")
        except Exception as e:
            logger.warning(f"特别处理表格中的建筑高度时出错: {str(e)}")
    
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
    
    # 特别处理总用地面积
    if '总用地面积' not in project_info:
        # 尝试从更复杂的描述中提取
        land_area_patterns = [
            r"本项目用地面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"项目总用地[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"规划总用地[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总占地面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"总用地面积约[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?",
            r"用地红线面积[为是]?\s*([0-9,.]+)\s*(?:平方米|㎡|m²|m2)?"
        ]
        for pattern in land_area_patterns:
            match = re.search(pattern, text)
            if match:
                project_info['总用地面积'] = match.group(1) + " 平方米"
                logger.debug(f"从复杂描述中提取到总用地面积: {project_info['总用地面积']}")
                break

    # 特别处理停车位信息
    if '地面停车位' not in project_info:
        # 尝试从更复杂的描述中提取
        parking_patterns = [
            r"实际建设车位\s*(\d+)\s*(?:个|辆)?",
            r"停车位共[计]?(\d+)[个辆]",
            r"地面停车(\d+)[个辆]",
            r"室外停车(\d+)[个辆]",
            r"地面机动车停车位(\d+)[个辆]",
            r"地上停车位(\d+)[个辆]",
            r"地面规划停车位(\d+)[个辆]",
            r"(?:配置|配建|设置)(?:地面)?停车位(\d+)[个辆]",
            r"机动车停车位[数量个]?[:：]?\s*(\d+)\s*(?:个|辆)?",
            r"(?:其中)?地面停车位?数[为是]?(\d+)[个辆]",
            r"地面设置停车位(\d+)[个辆]"
        ]
        
        # 首先尝试匹配"实际建设车位"
        actual_parking_match = re.search(r"实际建设车位\s*(\d+)\s*(?:个|辆)?", text)
        if actual_parking_match:
            project_info['地面停车位'] = actual_parking_match.group(1)
            logger.debug(f"从实际建设车位提取到地面停车位: {project_info['地面停车位']}")
        else:
            # 如果没有找到实际建设车位，尝试其他模式
            for pattern in parking_patterns:
                match = re.search(pattern, text)
                if match:
                    project_info['地面停车位'] = match.group(1)
                    logger.debug(f"从复杂描述中提取到地面停车位: {project_info['地面停车位']}")
                    break

        # 如果还是没有找到，尝试从段落中提取
        if '地面停车位' not in project_info:
            # 查找包含"停车"的段落
            parking_sections = re.findall(r'[^。]*停车[^。]*。', text)
            for section in parking_sections:
                # 优先查找实际建设车位
                actual_match = re.search(r"实际建设车位\s*(\d+)\s*(?:个|辆)?", section)
                if actual_match:
                    project_info['地面停车位'] = actual_match.group(1)
                    logger.debug(f"从段落中提取到实际建设车位: {project_info['地面停车位']}")
                    break
                    
                # 如果没有实际建设车位，查找其他数字
                numbers = re.findall(r'(\d+)[个辆]', section)
                if numbers and '地面' in section:
                    project_info['地面停车位'] = numbers[0]
                    logger.debug(f"从段落中提取到地面停车位: {project_info['地面停车位']}")
                    break

    # 确保数值的完整性
    for key in ['总用地面积', '地上建筑面积', '地下建筑面积', '总建筑面积']:
        if key in project_info:
            value = project_info[key]
            # 处理末尾有小数点但没有小数位的情况
            if value.endswith('.'):
                value = value + '0'
            # 添加单位（如果没有）
            if not any(unit in str(value) for unit in ['平方米', '㎡', 'm²', 'm2']):
                value = str(value) + ' 平方米'
            project_info[key] = value
            logger.debug(f"处理后的{key}: {value}")

    # 字段名称映射（双向映射）
    field_mapping = {
        '总用地面积': 'total_land_area',
        '总建筑面积': 'total_building_area',
        '地上建筑面积': 'above_ground_area',
        '地下建筑面积': 'underground_area',
        '建筑高度': 'building_height',
        '容积率': 'plot_ratio',
        '建筑密度': 'building_density',
        '绿地面积': 'green_area',
        '绿地率': 'green_ratio',
        '地面停车位': 'ground_parking_spaces',
        # 新增表格特有字段映射
        '建筑类型': 'building_type',
        '公建类型': 'public_building_type',
        '气候区划': 'climate_zone',
        '有无电梯': 'has_elevator',
        '有无地下车库': 'has_underground_garage',
        '有无景观水体': 'has_water_landscape',
        '绿地向公众开放': 'public_green_space',
        '是否为全装修项目': 'is_fully_decorated',
        '空调形式': 'air_conditioning_type',
        '项目建设情况': 'construction_type'
    }

    # 直接添加总用地面积
    if '总用地面积' not in project_info:
        logger.warning("未找到总用地面积，将使用替代方法")
        # 尝试从其他字段推断
        for key in project_info.keys():
            if ('用地' in key or '占地' in key) and '面积' in key and key != '总用地面积':
                logger.info(f"使用替代字段作为总用地面积: {key}={project_info[key]}")
                project_info['总用地面积'] = project_info[key]
                break
        
        # 如果仍然找不到，添加默认值
        if '总用地面积' not in project_info:
            logger.warning("无法找到任何相关字段，添加默认总用地面积")
            project_info['总用地面积'] = "0 平方米"

    # 创建新的字典，只保存中文键
    mapped_info = {}
    
    # 确保总用地面积一定会被处理
    if '总用地面积' in project_info:
        total_land_area_value = project_info['总用地面积']
        logger.info(f"处理总用地面积: 原始值={total_land_area_value}")
        
        # 提取数值部分
        number_match = re.search(r'([-+]?\d*\.?\d+)', str(total_land_area_value))
        if number_match:
            clean_value = number_match.group(1)
            logger.info(f"总用地面积数值提取: {clean_value}")
            
            try:
                # 转换为数值
                numeric_value = float(clean_value)
                # 格式化
                if numeric_value.is_integer():
                    clean_value = str(int(numeric_value))
                else:
                    clean_value = str(numeric_value)
                    
                # 直接添加到结果中
                mapped_info['total_land_area'] = clean_value
                mapped_info['总用地面积'] = f"{clean_value} 平方米"
                logger.info(f"总用地面积处理完成: {mapped_info['总用地面积']}")
            except Exception as e:
                logger.error(f"处理总用地面积数值时出错: {str(e)}")
                # 即使出错，也添加一个默认值
                mapped_info['total_land_area'] = "0" 
                mapped_info['总用地面积'] = "0 平方米"
        else:
            logger.error(f"无法从总用地面积中提取数值: {total_land_area_value}")
            # 添加默认值
            mapped_info['total_land_area'] = "0"
            mapped_info['总用地面积'] = "0 平方米"
    else:
        logger.error("总用地面积字段不存在")
        # 添加默认值
        mapped_info['total_land_area'] = "0"
        mapped_info['总用地面积'] = "0 平方米"
    
    # 处理提取的信息
    for key, value in project_info.items():
        try:
            # 跳过已处理的总用地面积和无效键
            if key == '总用地面积' or not isinstance(key, str) or not value:
                continue
                
            # 跳过不规范的键（包含异常文本）
            if len(key) > 20 or '注' in key or '备注' in key:
                continue
            
            # 获取中文键
            cn_key = key if key in field_mapping else None
            if not cn_key:
                # 如果找不到对应的中文键，跳过此字段
                continue

            # 获取英文键
            eng_key = field_mapping.get(cn_key)
            if not eng_key:
                continue
                
            # 检查是否为文本类字段，不需要数值转换的字段
            text_fields = ['building_type', 'public_building_type', 'climate_zone', 
                          'has_elevator', 'has_underground_garage', 'has_water_landscape',
                          'public_green_space', 'is_fully_decorated', 'air_conditioning_type',
                          'construction_type']
                
            if eng_key in text_fields:
                # 文本字段直接保存，不尝试转换为数值
                clean_value = value.strip()
                mapped_info[eng_key] = clean_value
                mapped_info[cn_key] = clean_value
                logger.debug(f"处理文本字段 '{key}': {clean_value}")
                continue
                    
            # 处理数值字段
            if isinstance(value, str):
                # 提取数值部分
                number_match = re.search(r'([-+]?\d*\.?\d+)', value)
                if number_match:
                    clean_value = number_match.group(1)
                else:
                    clean_value = value.replace('平方米', '').replace('㎡', '').replace('m²', '').replace('m2', '').replace('%', '').replace('个', '').replace('辆', '').strip()
                
                try:
                    # 转换为数值
                    numeric_value = float(clean_value)
                    # 如果是整数，去掉小数部分
                    if numeric_value.is_integer():
                        clean_value = str(int(numeric_value))
                    else:
                        clean_value = str(numeric_value)
                except ValueError:
                    # 如果无法转换为数值，跳过此字段
                    logger.warning(f"无法将值 '{clean_value}' 转换为数值，跳过字段 '{key}'")
                    continue
                    
                try:
                    # 添加英文键和中文键的映射
                    if eng_key in ['total_land_area', 'total_building_area', 'above_ground_area', 'underground_area']:
                        # 面积字段保留原始精度
                        mapped_info[eng_key] = clean_value
                        mapped_info[cn_key] = f"{clean_value} 平方米"
                        # 特别处理总用地面积
                        if eng_key == 'total_land_area':
                            logger.debug(f"处理总用地面积: 原始值={value}, 清理后={clean_value}")
                            mapped_info['total_land_area'] = clean_value
                            mapped_info['总用地面积'] = f"{clean_value} 平方米"
                    elif eng_key == 'ground_parking_spaces':
                        # 停车位转为整数
                        try:
                            parking_value = str(int(float(clean_value)))
                            mapped_info[eng_key] = parking_value
                            mapped_info[cn_key] = f"{parking_value} 个"
                        except ValueError:
                            mapped_info[eng_key] = "0"
                            mapped_info[cn_key] = "0 个"
                    else:
                        # 其他字段
                        mapped_info[eng_key] = clean_value
                        # 添加适当的单位
                        if '高度' in cn_key:
                            mapped_info[cn_key] = f"{clean_value} 米"
                        elif eng_key in ['building_density', 'green_ratio']:
                            mapped_info[cn_key] = f"{clean_value}%"
                        else:
                            mapped_info[cn_key] = clean_value
                except Exception as e:
                    logger.warning(f"处理字段 '{key}' 时出错: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"处理字段 '{key}' 时出错: {str(e)}")
            continue

    # 记录最终映射结果并再次确认总用地面积存在
    valid_fields = len(mapped_info) // 2  # 因为每个字段都有中英文两个键
    logger.info(f"成功提取并映射了 {valid_fields} 个有效字段")
    logger.info(f"最终映射的总用地面积: {mapped_info.get('总用地面积', '未找到')}")  
    logger.info(f"最终映射的total_land_area: {mapped_info.get('total_land_area', '未找到')}")
    logger.debug(f"最终映射结果: {mapped_info}")
    
    # 最终检查并确保总用地面积存在
    if '总用地面积' not in mapped_info or 'total_land_area' not in mapped_info:
        logger.error("最终检查时发现总用地面积缺失，添加默认值")
        mapped_info['总用地面积'] = "0 平方米"
        mapped_info['total_land_area'] = "0"
    
    return mapped_info

def extract_image_info(image_path):
    """
    使用百度OCR API从图像中提取项目信息
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        dict: 从图像中提取的项目信息字典，提取失败返回空字典
    """
    logger = logging.getLogger('GreenScore')
    
    # 检查百度OCR API是否可用
    if not BAIDU_OCR_AVAILABLE:
        error_msg = "百度OCR API未正确配置或初始化失败"
        logger.error(error_msg)
        # 不抛出异常，返回空字典
        return {}
    
    try:
        # 使用新的函数提取文本和项目信息
        result = extract_image_info_with_raw_text(image_path)
        
        # 如果结果为None或者不是字典，返回空字典
        if not result or not isinstance(result, dict) or 'project_info' not in result:
            logger.error("提取项目信息格式错误")
            return {'总用地面积': '0 平方米', 'total_land_area': '0'}
            
        project_info = result['project_info'] or {}
        
        # 确保总用地面积存在于结果中
        if '总用地面积' not in project_info or 'total_land_area' not in project_info:
            logger.warning("返回前发现总用地面积缺失，添加默认值")
            project_info['总用地面积'] = '0 平方米'
            project_info['total_land_area'] = '0'
        
        logger.info(f"最终返回项目信息包含字段: {list(project_info.keys())}")
        logger.info(f"总用地面积: {project_info.get('总用地面积', '未找到')}; 英文键: {project_info.get('total_land_area', '未找到')}")
        
        # 返回项目信息
        return project_info
        
    except Exception as e:
        logger.error(f"提取图像信息时出错: {str(e)}")
        return {'总用地面积': '0 平方米', 'total_land_area': '0'}

def extract_image_info_with_raw_text(image_path):
    """
    使用百度OCR API从图像中提取项目信息和原始文本
    
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
    
    # 检查百度OCR API是否可用
    if not BAIDU_OCR_AVAILABLE:
        error_msg = "百度OCR API未正确配置或初始化失败"
        logger.error(error_msg)
        # 不抛出异常，而是返回默认值
        return default_return
    
    try:
        # 使用百度OCR API提取文本
        extracted_text = extract_text_using_baidu_ocr(image_path)
        
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