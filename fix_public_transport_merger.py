import os
import re
import shutil
import tempfile
from datetime import datetime

def backup_original_file(file_path):
    """
    创建原始文件的备份
    """
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"已创建备份文件: {backup_path}")
    return backup_path

def apply_fixes_to_public_transport_analytics(file_path="public_transport_analytics.py"):
    """
    将修复应用到原始的公共交通分析文件中
    """
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return False
    
    # 创建备份
    backup_path = backup_original_file(file_path)
    
    # 读取原始文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用修复
    modified_content = content
    
    # 1. 修复表格创建和填充逻辑
    # 查找公交站点列表占位符处理代码段
    table_pattern = r"(\s+# 处理公交站点列表占位符\s+if '\{公交站点列表\}' in paragraph\.text:[\s\S]+?try:[\s\S]+?parent\.remove\(paragraph\._p\)[\s\S]+?stations_table_added = True[\s\S]+?app\.logger\.info\(f\"成功用表格替换了占位符段落\"\)[\s\S]+?except Exception as e:[\s\S]+?return jsonify\(\{'success': False, 'message': f'替换段落为表格失败: \{str\(e\)\}'\}\), 500)"
    
    # 替换为改进的版本
    table_replacement = '''    # 处理公交站点列表占位符
    if '{公交站点列表}' in original_text:
        app.logger.info(f"找到公交站点列表占位符")
        placeholder_found = True
        
        # 创建表格
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        app.logger.info(f"创建表格: 行数={len(table.rows)}, 列数={len(table.rows[0].cells) if table.rows else 0}")
        
        # 设置表头
        header_cells = table.rows[0].cells
        header_cells[0].text = "序号"
        header_cells[1].text = "站点名称"
        header_cells[2].text = "类型"
        header_cells[3].text = "距离（米）"
        header_cells[4].text = "详细信息"
        app.logger.info(f"设置表头: {[cell.text for cell in header_cells]}")
        
        # 在后端也进行站点数据的标准化，确保字段格式一致
        standardized_stations = []
        for idx, station in enumerate(stations):
            # 标准化站点数据格式
            standardized_station = {
                'index': station.get('index', idx + 1),
                'name': station.get('name', '未知站点'),
                'type': station.get('type', '公交站'),
                'distance': str(station.get('distance', '0')),  # 确保距离为字符串
                'detail': station.get('detail', station.get('address', station.get('description', '无详细信息'))),
                'location': station.get('location', {"lng": 0, "lat": 0})
            }
            standardized_stations.append(standardized_station)
        
        # 使用标准化后的站点数据
        standardized_data = standardized_stations
        app.logger.info(f"站点数据已标准化，共 {len(standardized_data)} 个站点")
        
        # 添加数据行
        for idx, station in enumerate(standardized_data):
            row = table.add_row()
            cells = row.cells
            
            app.logger.info(f"\\n处理表格行 {idx+1}:")
            app.logger.info(f"站点数据: {json.dumps(station, ensure_ascii=False)}")
            
            # 逐个单元格填充并记录
            app.logger.info("开始填充单元格:")
            
            # 序号列
            cells[0].text = str(idx + 1)
            app.logger.info(f"单元格[0](序号): 已填充值 '{cells[0].text}'")
            
            # 站点名称列
            name_value = station.get('name', '')
            cells[1].text = name_value
            app.logger.info(f"单元格[1](站点名称): 从字段'name'获取值 '{name_value}'")
            
            # 类型列
            type_value = station.get('type', '')
            app.logger.info(f"字段'type'的值: '{type_value}'")
            cells[2].text = type_value
            app.logger.info(f"单元格[2](类型): 已填充值 '{cells[2].text}'")
            
            # 距离列
            distance_value = station.get('distance', '')
            app.logger.info(f"字段'distance'的值: '{distance_value}'")
            cells[3].text = str(distance_value)
            app.logger.info(f"单元格[3](距离): 已填充值 '{cells[3].text}'")
            
            # 详细信息列
            detail_value = station.get('detail', station.get('address', '无详细信息'))
            app.logger.info(f"详细信息使用值: '{detail_value}'")
            cells[4].text = detail_value
            app.logger.info(f"单元格[4](详细信息): 已填充值 '{cells[4].text}'")
            
            # 验证填充结果
            app.logger.info(f"行 {idx+1} 填充结果:")
            for i, cell in enumerate(cells):
                app.logger.info(f"  单元格[{i}]: '{cell.text}'")
            
            # 最终表格行的实际内容
            app.logger.info(f"表格行 {idx+1} 最终内容: {[cell.text for cell in cells]}")
        
        # 直接用表格替换段落，而不是添加到段落后面
        try:
            # 获取段落的父元素
            parent = paragraph._p.getparent()
            # 获取段落在父元素中的索引
            index = parent.index(paragraph._p)
            # 在段落的位置插入表格
            parent.insert(index, table._tbl)
            # 移除原始段落
            parent.remove(paragraph._p)
            
            stations_table_added = True
            app.logger.info(f"成功用表格替换了占位符段落")
        except Exception as e:
            app.logger.error(f"替换段落为表格时出错: {str(e)}")
            app.logger.error(traceback.format_exc())
            os.remove(output_path)  # 删除临时文件
            return jsonify({'success': False, 'message': f'替换段落为表格失败: {str(e)}'}), 500
            
        continue  # 处理完占位符后，跳过后续处理'''
    
    # 应用表格创建修复
    modified_content = re.sub(table_pattern, table_replacement, modified_content)
    
    # 2. 添加表格单元格占位符处理
    # 查找最后一个检查点（在查找完所有占位符后）
    last_check_pattern = r"# 如果找到占位符但无法插入表格，返回错误\s+if placeholder_found and not stations_table_added:"
    
    # 要插入的表格单元格处理代码
    table_placeholders_code = '''
        # 处理表格中的占位符
        app.logger.info("\\n开始处理表格中的占位符")
        
        for t_idx, table in enumerate(doc.tables):
            app.logger.info(f"处理表格 #{t_idx+1}")
            
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    original_text = cell.text
                    
                    if '{' in original_text and '}' in original_text:
                        app.logger.info(f"表格 #{t_idx+1}, 行 #{r_idx+1}, 列 #{c_idx+1} 包含占位符: '{original_text}'")
                        
                        # 特殊处理日期占位符
                        if '{设计日期}' in original_text:
                            date_value = datetime.now().strftime('%Y年%m月%d日')
                            new_text = original_text.replace('{设计日期}', date_value)
                            
                            # 替换单元格文本
                            cell.text = new_text
                            app.logger.info(f"替换表格中的日期占位符: '{original_text}' -> '{new_text}'")
                            continue
                        
                        # 替换其他占位符
                        new_text = original_text
                        text_changed = False
                        
                        for placeholder, value in extended_project_info.items():
                            if placeholder in ['地图截图', '公交站点列表', '结论']:
                                continue  # 跳过特殊占位符
                            
                            placeholder_text = '{' + placeholder + '}'
                            if placeholder_text in new_text:
                                if value is not None:
                                    new_text = new_text.replace(placeholder_text, str(value))
                                    text_changed = True
                                    app.logger.info(f"替换了表格中的占位符 {placeholder_text} -> {value}")
                        
                        if text_changed:
                            cell.text = new_text
                            app.logger.info(f"表格单元格文本已更改: '{original_text}' -> '{new_text}'")
        
        '''
    
    # 插入表格单元格处理代码
    modified_content = modified_content.replace(last_check_pattern, table_placeholders_code + "\n        " + last_check_pattern)
    
    # 3. 改进结论占位符处理
    # 查找结论占位符处理代码段
    conclusion_pattern = r"(# 特别检查是否包含结论占位符\s+if '\{结论\}' in original_text:[\s\S]+?app\.logger\.info\(f\"段落 \{i\+1\} 包含结论占位符\"\))"
    
    # 替换为改进的版本
    conclusion_replacement = '''# 替换结论占位符
                if '{结论}' in original_text:
                    app.logger.info(f"找到结论占位符")
                    conclusion_value = extended_project_info.get('结论', '未提供结论')
                    
                    # 清空段落中所有runs，但保持段落本身
                    p = paragraph._p
                    for run in list(paragraph.runs):
                        p.remove(run._r)
                    
                    # 分行添加结论文本
                    lines = conclusion_value.split('\\n')
                    for line_idx, line in enumerate(lines):
                        if line_idx > 0:  # 非首行添加换行
                            paragraph.add_run().add_break()
                        if line.strip():  # 只添加非空行
                            paragraph.add_run(line)
                    
                    app.logger.info(f"替换结论占位符完成")
                    continue  # 处理完占位符后，跳过后续处理'''
    
    # 应用结论占位符处理修复
    modified_content = re.sub(conclusion_pattern, conclusion_replacement, modified_content)
    
    # 4. 修复当结论是特殊占位符时的处理逻辑
    # 查找结论占位符的特殊处理（在替换项目信息占位符的循环内）
    conclusion_in_loop_pattern = r"(# 如果是结论占位符，使用换行符进行替换\s+if placeholder == '结论':[\s\S]+?# 分割结论文本为多行[\s\S]+?lines = value\.split\('\\n'\)[\s\S]+?# 清空段落中所有runs，但保持段落本身[\s\S]+?p = paragraph\._p[\s\S]+?for run in list\(paragraph\.runs\):[\s\S]+?p\.remove\(run\._r\)[\s\S]+?# 添加每一行，用换行符分隔[\s\S]+?for line_idx, line in enumerate\(lines\):[\s\S]+?if line_idx > 0 and line: # 对于非首行且非空行，添加换行[\s\S]+?paragraph\.add_run\(\)\.add_break\(\)[\s\S]+?if line: # 只添加非空行[\s\S]+?paragraph\.add_run\(line\)[\s\S]+?app\.logger\.info\(f\"替换了结论占位符，应用多行格式: \{value\}\"\)[\s\S]+?text_changed = True[\s\S]+?# 跳过后续对该段落的处理[\s\S]+?break)"
    
    # 由于我们已经在之前添加了特殊处理结论占位符的代码，这里我们需要移除旧的处理逻辑
    conclusion_in_loop_replacement = "# 结论占位符已在单独的逻辑中处理，此处跳过\n                    continue"
    
    # 应用修复
    modified_content = re.sub(conclusion_in_loop_pattern, conclusion_in_loop_replacement, modified_content)
    
    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"已应用修复到 {file_path}")
    print(f"原始文件备份在 {backup_path}")
    return True

if __name__ == "__main__":
    print("公共交通站点分析报告文件修复器")
    print("----------------------------")
    
    # 默认文件路径
    file_path = "public_transport_analytics.py"
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        exit(1)
    
    # 应用修复
    print(f"开始修复文件: {file_path}")
    result = apply_fixes_to_public_transport_analytics(file_path)
    
    if result:
        print("\n✅ 修复成功!")
        print("以下是主要修复内容:")
        print("1. 改进了公交站点表格的创建和填充逻辑")
        print("2. 添加了表格单元格中占位符的处理")
        print("3. 改进了结论占位符的处理，确保换行格式正确")
        print("4. 添加了站点数据标准化处理，确保字段格式一致")
    else:
        print("\n❌ 修复失败!") 