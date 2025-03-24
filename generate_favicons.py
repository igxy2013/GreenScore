#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成多种尺寸的网站图标（favicon）和高分辨率显示图标
使用方法：python generate_favicons.py 原始图片路径
"""

import os
import sys
from PIL import Image

def generate_icons(source_image_path):
    """
    从原始图像生成多种尺寸的favicon和高分辨率显示图标
    
    参数:
        source_image_path: 原始图像的路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(source_image_path):
        print(f"错误：找不到源文件 {source_image_path}")
        return False
        
    # 目标尺寸和文件名(favicon)
    favicon_sizes = {
        16: "greenscore-sm.png",  # 基本favicon尺寸
        32: "greenscore-32.png",  # 高分辨率favicon
        48: "greenscore.png",     # 标准尺寸
        180: "greenscore-lg.png", # iOS/Safari图标
        192: "greenscore-192.png", # Android Chrome
        512: "greenscore-512.png"  # PWA图标
    }
    
    # 高分辨率显示图标尺寸
    display_icons = {
        # 格式：显示尺寸:(实际尺寸, 文件名)
        # 常规尺寸
        '48': (48, "image/greenscore.png"),
        '64': (64, "image/greenscore-64.png"),
        # 2x高分辨率
        '48@2x': (96, "image/greenscore@2x.png"),
        '64@2x': (128, "image/greenscore-64@2x.png"),
        # 3x高分辨率(苹果设备)
        '48@3x': (144, "image/greenscore@3x.png"),
        '64@3x': (192, "image/greenscore-64@3x.png"),
    }
    
    try:
        # 打开原始图像
        with Image.open(source_image_path) as img:
            # 创建输出目录（如果不存在）
            output_dir = "static"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"创建目录：{output_dir}")
            
            image_dir = os.path.join(output_dir, "image")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
                print(f"创建目录：{image_dir}")
            
            # 生成favicon
            for size, filename in favicon_sizes.items():
                output_path = os.path.join(output_dir, filename)
                # 调整图像大小并保存
                resized_img = img.resize((size, size), Image.LANCZOS)
                resized_img.save(output_path)
                print(f"已生成 {size}x{size} 图标：{output_path}")
            
            # 生成高分辨率显示图标
            for display_info, (actual_size, filename) in display_icons.items():
                output_path = os.path.join(output_dir, filename)
                # 调整图像大小并保存
                resized_img = img.resize((actual_size, actual_size), Image.LANCZOS)
                resized_img.save(output_path)
                print(f"已生成 {display_info} ({actual_size}x{actual_size}) 图标：{output_path}")
                
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
    generate_icons(source_image_path) 