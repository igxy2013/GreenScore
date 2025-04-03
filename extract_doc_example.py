import os
import sys
from utils.word_extractor import extract_doc_info

def main():
    """
    示例：如何使用extract_doc_info函数从Word文档中提取项目信息
    """
    # 检查命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 默认示例文件
        file_path = os.path.abspath("规定性指标计算报告书_建筑1_公建.doc")
    
    print(f"正在分析文件: {file_path}")
    
    # 调用提取函数
    project_info = extract_doc_info(file_path)
    
    if project_info:
        print("\n=== 成功提取项目信息 ===")
        # 打印提取到的各项信息
        for key, value in project_info.items():
            print(f"{key}: {value}")
        
        # 示例：如何使用提取的信息
        print("\n=== 信息使用示例 ===")
        print(f"项目 '{project_info['项目名称']}' 位于 {project_info['项目地点']}，")
        print(f"由 {project_info['建设单位']} 建设，{project_info['设计单位']} 设计，")
        print(f"气候分区为 {project_info['气候分区']}，")
        print(f"建筑类型为 {project_info['建筑分类']}，结构为 {project_info['结构形式']}，")
        print(f"建筑朝向 {project_info['建筑朝向']}，")
        print(f"建筑面积为 {project_info['建筑面积']} 平方米，")
        print(f"地上 {project_info['建筑层数']}，地下 {project_info['地下层数']} 层，")
        print(f"建筑高度为 {project_info['建筑高度']} 米。")
    else:
        print("提取信息失败")

if __name__ == "__main__":
    main() 