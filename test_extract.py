import os
import sys
from utils.extract_word_info import extract_project_info

def main():
    file_path = os.path.abspath("规定性指标计算报告书_建筑1_公建.doc")
    print(f"正在分析文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    info = extract_project_info(file_path)
    
    if info:
        print("\n提取到的项目信息:")
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("提取信息失败")

if __name__ == "__main__":
    main() 