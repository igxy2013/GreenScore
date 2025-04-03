#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import cv2
import pytesseract
import numpy as np
from PIL import Image
from loguru import logger

def preprocess_image(image):
    """预处理图像用于OCR识别"""
    # 转为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 应用自适应阈值处理增强对比度
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # 可选：降噪处理
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised

def extract_text_from_image(image_path):
    """从图像中提取文本"""
    try:
        # 读取图像
        if isinstance(image_path, str):
            # 从文件路径读取
            img = cv2.imread(image_path)
        else:
            # 从上传的文件对象读取
            img_array = np.frombuffer(image_path.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            # 重置文件指针
            if hasattr(image_path, 'seek'):
                image_path.seek(0)
                
        if img is None:
            logger.error(f"无法读取图像")
            return None
            
        # 预处理图像
        processed_img = preprocess_image(img)
        
        # 使用pytesseract进行OCR识别
        # 使用中文语言包 + 英文
        text = pytesseract.image_to_string(processed_img, lang='chi_sim+eng')
        
        return text
    except Exception as e:
        logger.error(f"处理图像时出错: {str(e)}")
        return None

def parse_project_info_from_text(text):
    """从提取的文本中解析项目信息"""
    
    # 定义要提取的关键信息字段和对应的正则表达式
    info_patterns = {
        "项目名称": r"(?:项目名称[：:]\s*)(.+?)(?:\n|$)",
        "建设单位": r"(?:建设单位[：:]\s*)(.+?)(?:\n|$)",
        "设计单位": r"(?:设计单位[：:]\s*)(.+?)(?:\n|$)",
        "项目地点": r"(?:项目地点|建设地点|工程地点)[：:]\s*(.+?)(?:\n|$)",
        "总用地面积": r"(?:总用地面积|用地面积)[：:]\s*([\d\.]+)\s*(?:平方米|㎡)?",
        "总建筑面积": r"(?:总建筑面积|建筑面积)[：:]\s*([\d\.]+)\s*(?:平方米|㎡)?",
        "地上建筑面积": r"(?:地上建筑面积)[：:]\s*([\d\.]+)\s*(?:平方米|㎡)?",
        "地下建筑面积": r"(?:地下建筑面积)[：:]\s*([\d\.]+)\s*(?:平方米|㎡)?",
        "建筑层数": r"(?:建筑层数)[：:]\s*(.+?)(?:\n|$)",
        "建筑高度": r"(?:建筑高度)[：:]\s*([\d\.]+)\s*(?:米|m)?",
        "容积率": r"(?:容积率)[：:]\s*([\d\.]+)",
        "建筑密度": r"(?:建筑密度)[：:]\s*([\d\.]+)\s*%?",
        "绿地率": r"(?:绿地率)[：:]\s*([\d\.]+)\s*%?",
        "停车位": r"(?:停车位|停车数量)[：:]\s*(\d+)\s*(?:个)?",
        "气候分区": r"(?:气候分区|气候区划)[：:]\s*(.+?)(?:\n|$)",
        "建筑分类": r"(?:建筑分类|建筑类型)[：:]\s*(.+?)(?:\n|$)",
        "结构形式": r"(?:结构形式|结构类型)[：:]\s*(.+?)(?:\n|$)",
    }
    
    # 存储提取的信息
    project_info = {key: "" for key in info_patterns.keys()}
    
    # 使用正则表达式提取信息
    for key, pattern in info_patterns.items():
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            project_info[key] = matches.group(1).strip()
    
    # 清理提取的数据
    # 如果项目名称太长或包含无关信息，进行清理
    if project_info["项目名称"]:
        # 移除可能混入的多余符号和空格
        project_info["项目名称"] = project_info["项目名称"].strip()
        project_info["项目名称"] = re.sub(r'^[：:、\s]+', '', project_info["项目名称"])
        project_info["项目名称"] = re.sub(r'[：:、\s]+$', '', project_info["项目名称"])
        
        # 清理常见词汇
        project_info["项目名称"] = re.sub(r'(节能设计|规定性指标|计算报告书|审图答复|专篇|设计说明|建筑节能|\(.*?\))', '', project_info["项目名称"]).strip()
        
        # 限制长度，过长可能是错误提取
        if len(project_info["项目名称"]) > 50:
            # 尝试截取合理部分
            name_parts = re.split(r'[,，。;；]', project_info["项目名称"])
            if name_parts and len(name_parts[0]) > 3 and len(name_parts[0]) < 50:
                project_info["项目名称"] = name_parts[0].strip()
    
    # 确保数值型数据转换正确
    number_fields = ["总用地面积", "总建筑面积", "地上建筑面积", "地下建筑面积", 
                    "建筑高度", "容积率", "建筑密度", "绿地率", "停车位"]
    
    for field in number_fields:
        if project_info[field]:
            try:
                if field in ["建筑密度", "绿地率"]:
                    # 百分比值去掉百分号
                    project_info[field] = re.sub(r'%', '', project_info[field])
                # 清理数值前后的无关字符
                project_info[field] = re.sub(r'[^0-9\.]', '', project_info[field])
            except:
                project_info[field] = ""
    
    # 转换字段名到与数据库模型匹配的名称
    field_mapping = {
        "项目名称": "name",
        "建设单位": "construction_unit",
        "设计单位": "design_unit",
        "项目地点": "location",
        "总用地面积": "total_land_area",
        "总建筑面积": "total_building_area",
        "地上建筑面积": "above_ground_area",
        "地下建筑面积": "underground_area",
        "建筑层数": "building_floors",
        "建筑高度": "building_height",
        "容积率": "plot_ratio",
        "建筑密度": "building_density",
        "绿地率": "green_ratio",
        "停车位": "ground_parking_spaces",
        "气候分区": "climate_zone",
        "建筑分类": "building_type",
        "结构形式": "construction_type",
    }
    
    # 使用转换后的字段名创建最终结果
    result = {}
    for old_key, new_key in field_mapping.items():
        if project_info[old_key]:
            result[old_key] = project_info[old_key]
            # 同时添加英文字段，用于API返回
            result[new_key] = project_info[old_key]
    
    return result

def extract_image_info(image_path):
    """从图像中提取项目信息的主函数"""
    try:
        # 提取文本
        text = extract_text_from_image(image_path)
        if not text:
            logger.error("无法从图像中提取文本")
            return None
            
        # 从文本中解析项目信息
        project_info = parse_project_info_from_text(text)
        
        return project_info
    except Exception as e:
        logger.error(f"从图像提取项目信息时出错: {str(e)}")
        return None 