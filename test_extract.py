import os
import sys
from utils.extract_word_info import extract_project_info
from docx import Document
import shutil
from utils.word_extractor import extract_doc_info

def main():
    # 源文件路径
    source_file = '建筑节能设计报告书(审图答复).docx'
    # 目标文件路径
    target_file = '建筑节能设计报告书.docx'
    
    # 检查源文件是否存在
    print(f"检查源文件是否存在: {source_file}")
    if not os.path.exists(source_file):
        print(f"错误: 源文件不存在 - {os.path.abspath(source_file)}")
        return
    
    # 创建目标文件的副本（如果不存在）
    if not os.path.exists(target_file):
        print(f"创建文件副本: {source_file} -> {target_file}")
        try:
            shutil.copy2(source_file, target_file)
            print(f"已成功创建文件副本")
        except Exception as e:
            print(f"创建文件副本失败: {str(e)}")
            return
    
    # 测试extract_doc_info函数 (这是实际系统中使用的函数)
    print("\n测试extract_doc_info函数...")
    doc_info = extract_doc_info(target_file)
    
    if doc_info:
        print("\n使用extract_doc_info提取到的项目信息:")
        for key, value in doc_info.items():
            print(f"{key}: {value}")
    else:
        print("使用extract_doc_info提取信息失败")
    
    # 测试extract_project_info函数 (这是基础函数)
    print("\n测试extract_project_info函数...")
    project_info = extract_project_info(target_file)
    
    if project_info:
        print("\n使用extract_project_info提取到的项目信息:")
        for key, value in project_info.items():
            print(f"{key}: {value}")
    else:
        print("使用extract_project_info提取信息失败")

if __name__ == "__main__":
    main() 