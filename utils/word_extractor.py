import os
from loguru import logger
from .extract_word_info import extract_project_info

def extract_doc_info(file_path):
    """
    从Word文档中提取项目信息的简易封装
    
    Args:
        file_path (str): Word文档的路径（.doc或.docx格式）
    
    Returns:
        dict: 包含提取出的项目信息
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    try:
        # 检查文件类型
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.doc', '.docx']:
            logger.error(f"不支持的文件格式: {file_ext}")
            return None
        
        # 调用详细提取函数
        info = extract_project_info(file_path)
        
        if info:
            # 标准化数据
            clean_info = {}
            for key, value in info.items():
                # 移除数字中的逗号
                if key in ["建筑面积", "建筑高度"]:
                    clean_info[key] = value.replace(',', '')
                else:
                    clean_info[key] = value
            
            # 地下层数处理：如果没有地下层数，设为"0"
            if "地下层数" in clean_info and (not clean_info["地下层数"] or clean_info["地下层数"].strip() == ""):
                clean_info["地下层数"] = "0"
            
            return clean_info
        else:
            return None
    
    except Exception as e:
        logger.error(f"提取文档信息时出错: {str(e)}")
        return None

# 示例用法
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python word_extractor.py <word文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = extract_doc_info(file_path)
    
    if result:
        print("\n提取到的项目信息:")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("提取信息失败") 