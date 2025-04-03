import os
import re
from loguru import logger
import platform

def extract_project_info(file_path):
    """
    从规定性指标计算报告书Word文档中提取项目信息
    
    Args:
        file_path (str): Word文档的路径（.doc或.docx格式）
    
    Returns:
        dict: 包含提取出的项目信息
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    # 初始化结果字典
    project_info = {
        "项目名称": "",
        "项目地点": "",
        "气候分区": "",
        "建筑分类": "",
        "结构形式": "",
        "建筑朝向": "",
        "建筑面积": "",
        "建筑层数": "",
        "地下层数": "",
        "建筑高度": "",
        "设计单位": "",
        "建设单位": ""
    }
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.docx':
            # 使用python-docx处理.docx文件
            from docx import Document
            doc = Document(file_path)
            extract_from_docx(doc, project_info)
        elif file_ext == '.doc':
            # 使用pywin32处理.doc文件
            if platform.system() != 'Windows':
                logger.error("只有Windows系统可以处理.doc文件")
                return None
                
            try:
                import win32com.client
                import pythoncom
                
                # 初始化COM组件
                pythoncom.CoInitialize()
                
                try:
                    word = win32com.client.Dispatch("Word.Application")
                    word.Visible = False
                    doc = word.Documents.Open(os.path.abspath(file_path))
                    
                    # 提取段落信息
                    all_paragraphs = []
                    for i in range(1, doc.Paragraphs.Count + 1):
                        all_paragraphs.append(doc.Paragraphs(i).Range.Text.strip())
                    
                    # 提取表格信息
                    tables_data = []
                    for i in range(1, doc.Tables.Count + 1):
                        table = doc.Tables(i)
                        table_data = []
                        for row_idx in range(1, table.Rows.Count + 1):
                            row_data = []
                            for col_idx in range(1, table.Columns.Count + 1):
                                try:
                                    cell_text = table.Cell(row_idx, col_idx).Range.Text.strip()
                                    cell_text = cell_text.replace('\r', '').replace('\n', ' ').replace('\x07', '')
                                    row_data.append(cell_text)
                                except:
                                    row_data.append("")
                            table_data.append(row_data)
                        tables_data.append(table_data)
                    
                    # 关闭文档和Word应用
                    doc.Close(False)
                    word.Quit()
                    
                    # 处理提取的文本内容
                    extract_from_paragraphs(all_paragraphs, project_info)
                    extract_from_tables(tables_data, project_info)
                finally:
                    # 确保在函数结束时释放COM资源
                    pythoncom.CoUninitialize()
                
            except ImportError:
                logger.error("处理.doc文件需要pywin32和pythoncom库，请安装: pip install pywin32")
                return None
            except Exception as e:
                logger.error(f"处理.doc文件时出错: {str(e)}")
                return None
        else:
            logger.error(f"不支持的文件格式: {file_ext}")
            return None
        
        # 处理地下层数信息
        if "地下层数" not in project_info or not project_info["地下层数"]:
            # 尝试从建筑层数中提取地下层数信息
            if project_info["建筑层数"]:
                # 正确识别"地下X层"的模式
                underground_match = re.search(r"地下[：:\s]*(\d+)[层\s]", project_info["建筑层数"])
                if underground_match:
                    project_info["地下层数"] = underground_match.group(1)
        
        logger.info(f"从文件 {os.path.basename(file_path)} 提取到的项目信息: {project_info}")
        return project_info
    
    except Exception as e:
        logger.error(f"提取项目信息时出错: {str(e)}")
        return None

def extract_from_docx(doc, project_info):
    """从docx文档对象中提取信息"""
    # 提取段落信息
    paragraphs = [para.text.strip() for para in doc.paragraphs]
    extract_from_paragraphs(paragraphs, project_info)
    
    # 提取表格信息
    tables_data = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        tables_data.append(table_data)
    
    extract_from_tables(tables_data, project_info)

def extract_from_paragraphs(paragraphs, project_info):
    """从段落文本中提取项目信息"""
    for text in paragraphs:
        text = text.strip()
        if not text:
            continue
        
        # 项目名称通常出现在文档开头
        if "项目名称" in text and not project_info["项目名称"]:
            match = re.search(r"项目名称[：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["项目名称"] = match.group(1).strip()
        
        # 项目地点（城市）- 增加对"项目城市"的识别
        if "项目地点" in text or "建设地点" in text or "项目城市" in text:
            match = re.search(r"(?:项目地点|建设地点|项目城市)[：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                location = match.group(1).strip()
                # 提取城市名称
                city_match = re.search(r"([^\s省市区县]+?[市州])", location)
                if city_match:
                    project_info["项目地点"] = city_match.group(1)
                else:
                    project_info["项目地点"] = location
        
        # 气候分区
        if "气候分区" in text or "气候区划" in text:
            match = re.search(r"气候[分区|区划][：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["气候分区"] = match.group(1).strip()
        
        # 建筑分类
        if "建筑类型" in text or "建筑分类" in text:
            match = re.search(r"建筑[类型|分类][：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["建筑分类"] = match.group(1).strip()
        
        # 结构形式
        if "结构形式" in text or "结构类型" in text:
            match = re.search(r"结构[形式|类型][：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["结构形式"] = match.group(1).strip()
        
        # 建筑朝向
        if "建筑朝向" in text:
            match = re.search(r"建筑朝向[：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["建筑朝向"] = match.group(1).strip()
        
        # 建筑面积
        if "建筑面积" in text and "总建筑面积" not in text:
            match = re.search(r"建筑面积[：:]\s*([0-9,.]+)\s*(?:m²|平方米)?", text)
            if match:
                project_info["建筑面积"] = match.group(1).strip()
        elif "总建筑面积" in text:
            match = re.search(r"总建筑面积[：:]\s*([0-9,.]+)\s*(?:m²|平方米)?", text)
            if match:
                project_info["建筑面积"] = match.group(1).strip()
        
        # 建筑层数
        if "层数" in text and "建筑层数" not in text and "地下层数" not in text:
            match = re.search(r"(?:建筑)?层数[：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["建筑层数"] = match.group(1).strip()
                # 尝试提取地下层数 - 正确识别"地下X层"的模式
                underground_match = re.search(r"地下[：:\s]*(\d+)[层\s]", match.group(1))
                if underground_match:
                    project_info["地下层数"] = underground_match.group(1)
        elif "建筑层数" in text:
            match = re.search(r"建筑层数[：:]\s*(.+?)(?:\s|$|，|,)", text)
            if match:
                project_info["建筑层数"] = match.group(1).strip()
                # 尝试提取地下层数 - 正确识别"地下X层"的模式
                underground_match = re.search(r"地下[：:\s]*(\d+)[层\s]", match.group(1))
                if underground_match:
                    project_info["地下层数"] = underground_match.group(1)
        
        # 单独的地下层数
        if "地下层数" in text and not project_info["地下层数"]:
            match = re.search(r"地下层数[：:]\s*(\d+)", text)
            if match:
                project_info["地下层数"] = match.group(1).strip()
        
        # 建筑高度
        if "建筑高度" in text:
            match = re.search(r"建筑高度[：:]\s*([0-9,.]+)\s*(?:m|米)?", text)
            if match:
                project_info["建筑高度"] = match.group(1).strip()
        
        # 设计单位
        if "设计单位" in text and not project_info["设计单位"]:
            match = re.search(r"设计单位[：:]\s*(.+?)(?:\s|$|，|,|。)", text)
            if match:
                project_info["设计单位"] = match.group(1).strip()
        
        # 建设单位
        if "建设单位" in text and not project_info["建设单位"]:
            match = re.search(r"建设单位[：:]\s*(.+?)(?:\s|$|，|,|。)", text)
            if match:
                project_info["建设单位"] = match.group(1).strip()

def extract_from_tables(tables_data, project_info):
    """从表格数据中提取项目信息"""
    for table_data in tables_data:
        for row_data in table_data:
            if not row_data:
                continue
            
            # 将行中的所有单元格文本合并
            row_text = ' '.join([str(cell) for cell in row_data if cell])
            
            # 在表格中查找各类信息
            for i, cell_text in enumerate(row_data):
                if not cell_text:
                    continue
                
                # 项目名称
                if "项目名称" in cell_text and not project_info["项目名称"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["项目名称"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["项目名称"] = match.group(1).strip()
                
                # 项目地点（城市）- 增加对"项目城市"的识别
                if ("项目地点" in cell_text or "建设地点" in cell_text or "项目城市" in cell_text) and not project_info["项目地点"]:
                    location = ""
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        location = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            location = match.group(1).strip()
                    
                    if location:
                        city_match = re.search(r"([^\s省市区县]+?[市州])", location)
                        if city_match:
                            project_info["项目地点"] = city_match.group(1)
                        else:
                            project_info["项目地点"] = location
                
                # 气候分区
                if ("气候分区" in cell_text or "气候区划" in cell_text) and not project_info["气候分区"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["气候分区"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["气候分区"] = match.group(1).strip()
                
                # 建筑分类
                if ("建筑类型" in cell_text or "建筑分类" in cell_text) and not project_info["建筑分类"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["建筑分类"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["建筑分类"] = match.group(1).strip()
                
                # 结构形式
                if ("结构形式" in cell_text or "结构类型" in cell_text) and not project_info["结构形式"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["结构形式"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["结构形式"] = match.group(1).strip()
                
                # 建筑朝向
                if "建筑朝向" in cell_text and not project_info["建筑朝向"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["建筑朝向"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["建筑朝向"] = match.group(1).strip()
                
                # 建筑面积
                if "建筑面积" in cell_text and "总建筑面积" not in cell_text and not project_info["建筑面积"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        area_text = row_data[i + 1].strip()
                        match = re.search(r"([0-9,.]+)", area_text)
                        if match:
                            project_info["建筑面积"] = match.group(1)
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*([0-9,.]+)", cell_text)
                        if match:
                            project_info["建筑面积"] = match.group(1)
                
                # 总建筑面积
                if "总建筑面积" in cell_text and not project_info["建筑面积"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        area_text = row_data[i + 1].strip()
                        match = re.search(r"([0-9,.]+)", area_text)
                        if match:
                            project_info["建筑面积"] = match.group(1)
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*([0-9,.]+)", cell_text)
                        if match:
                            project_info["建筑面积"] = match.group(1)
                
                # 建筑层数
                if "层数" in cell_text and "地下层数" not in cell_text and not project_info["建筑层数"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["建筑层数"] = row_data[i + 1].strip()
                        # 尝试提取地下层数 - 正确识别"地下X层"的模式
                        underground_match = re.search(r"地下[：:\s]*(\d+)[层\s]", row_data[i + 1])
                        if underground_match:
                            project_info["地下层数"] = underground_match.group(1)
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["建筑层数"] = match.group(1).strip()
                            # 尝试提取地下层数 - 正确识别"地下X层"的模式
                            underground_match = re.search(r"地下[：:\s]*(\d+)[层\s]", match.group(1))
                            if underground_match:
                                project_info["地下层数"] = underground_match.group(1)
                
                # 地下层数
                if "地下层数" in cell_text and not project_info["地下层数"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        underground_text = row_data[i + 1].strip()
                        match = re.search(r"(\d+)", underground_text)
                        if match:
                            project_info["地下层数"] = match.group(1)
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(\d+)", cell_text)
                        if match:
                            project_info["地下层数"] = match.group(1)
                
                # 建筑高度
                if "建筑高度" in cell_text and not project_info["建筑高度"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        height_text = row_data[i + 1].strip()
                        match = re.search(r"([0-9,.]+)", height_text)
                        if match:
                            project_info["建筑高度"] = match.group(1)
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*([0-9,.]+)", cell_text)
                        if match:
                            project_info["建筑高度"] = match.group(1)
                
                # 设计单位
                if "设计单位" in cell_text and not project_info["设计单位"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["设计单位"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["设计单位"] = match.group(1).strip()
                
                # 建设单位
                if "建设单位" in cell_text and not project_info["建设单位"]:
                    if i + 1 < len(row_data) and row_data[i + 1]:
                        project_info["建设单位"] = row_data[i + 1].strip()
                    elif "：" in cell_text or ":" in cell_text:
                        match = re.search(r"[：:]\s*(.+?)(?:\s|$|，|,)", cell_text)
                        if match:
                            project_info["建设单位"] = match.group(1).strip()

def main():
    """
    测试函数
    """
    import sys
    if len(sys.argv) < 2:
        print("用法: python extract_word_info.py <word文件路径>")
        return
    
    file_path = sys.argv[1]
    info = extract_project_info(file_path)
    
    if info:
        print("\n提取到的项目信息:")
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("提取信息失败")

if __name__ == "__main__":
    main() 