#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成多种尺寸的网站图标（favicon）
使用方法：python generate_favicons.py 原始图片路径
"""

import os
import sys
from PIL import Image

def generate_favicons(source_image_path):
    """
    从原始图像生成多种尺寸的favicon
    
    参数:
        source_image_path: 原始图像的路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(source_image_path):
        print(f"错误：找不到源文件 {source_image_path}")
        return False
        
    # 目标尺寸和文件名
    sizes = {
        16: "greenscore-sm.png",  # 基本favicon尺寸
        32: "greenscore-32.png",  # 高分辨率favicon
        48: "greenscore.png",     # 标准尺寸
        180: "greenscore-lg.png", # iOS/Safari图标
        192: "greenscore-192.png", # Android Chrome
        512: "greenscore-512.png"  # PWA图标
    }
    
    try:
        # 打开原始图像
        with Image.open(source_image_path) as img:
            # 创建输出目录（如果不存在）
            output_dir = "static"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"创建目录：{output_dir}")
            
            # 生成各种尺寸的图像
            for size, filename in sizes.items():
                output_path = os.path.join(output_dir, filename)
                # 调整图像大小并保存
                resized_img = img.resize((size, size), Image.LANCZOS)
                resized_img.save(output_path)
                print(f"已生成 {size}x{size} 图标：{output_path}")
                
        print("所有图标已成功生成！")
        return True
        
    except Exception as e:
        print(f"处理图像时出错：{e}")
        return False

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法：python generate_favicons.py 原始图片路径")
        sys.exit(1)
        
    source_image_path = sys.argv[1]
    generate_favicons(source_image_path) 