"""
此文件包含对 public_transport_analytics.py 的修复补丁
主要解决了占位符替换和表格创建的问题
"""

def apply_fix_to_fill_transport_report_template(app):
    """
    此函数包含对 fill_transport_report_template 路由函数的修复
    要应用此修复，请替换原始函数中的相关代码段
    """
    
    # 修复点1: 在处理段落占位符时，使用更可靠的方法处理特殊占位符
    # 查找以下代码段:
    """
    # 遍历所有段落查找占位符
    for i, paragraph in enumerate(doc.paragraphs):
        original_text = paragraph.text
        app.logger.info(f"检查段落 {i+1}: \"{original_text}\"")
        
        # 替换地址占位符
        if '{地址}' in original_text:
            # 获取整个段落的文本并替换占位符
            new_text = original_text.replace('{地址}', address)
            app.logger.info(f"替换地址占位符: '{original_text}' -> '{new_text}'")
            
            # 清空段落中所有runs，但保持段落本身
            p = paragraph._p
            for run in list(paragraph.runs):  # 使用列表复制，因为我们在修改集合
                p.remove(run._r)
                
            # 添加新的文本
            paragraph.add_run(new_text)
        
        # 替换日期占位符
        if '{设计日期}' in paragraph.text:
            # 获取整个段落的文本并替换占位符
            new_text = paragraph.text.replace('{设计日期}', datetime.now().strftime('%Y年%m月%d日'))
            app.logger.info(f"替换日期占位符: '{paragraph.text}' -> '{new_text}'")
            
            # 清空段落中所有runs，但保持段落本身
            p = paragraph._p
            for run in list(paragraph.runs):  # 使用列表复制，因为我们在修改集合
                p.remove(run._r)
                
            # 添加新的文本
            paragraph.add_run(new_text)
    """
    
    # 替换为以下改进版本:
    """
    # 遍历所有段落查找占位符
    for i, paragraph in enumerate(doc.paragraphs):
        original_text = paragraph.text
        app.logger.info(f"检查段落 {i+1}: \"{original_text}\"")
        
        # 替换地址占位符
        if '{地址}' in original_text:
            # 获取地址，优先使用项目地址，如果没有则使用项目地点
            address_value = project_info.get('项目地址', '') or project_info.get('location', '')
            new_text = original_text.replace('{地址}', address_value)
            app.logger.info(f"替换地址占位符: '{original_text}' -> '{new_text}'")
            
            # 清空段落中所有runs，但保持段落本身
            p = paragraph._p
            for run in list(paragraph.runs):  # 使用列表复制，因为我们在修改集合
                p.remove(run._r)
                
            # 添加新的文本
            paragraph.add_run(new_text)
            continue  # 处理完占位符后，跳过后续处理
        
        # 替换日期占位符
        if '{设计日期}' in original_text:
            # 获取整个段落的文本并替换占位符
            new_text = original_text.replace('{设计日期}', datetime.now().strftime('%Y年%m月%d日'))
            app.logger.info(f"替换日期占位符: '{original_text}' -> '{new_text}'")
            
            # 清空段落中所有runs，但保持段落本身
            p = paragraph._p
            for run in list(paragraph.runs):  # 使用列表复制，因为我们在修改集合
                p.remove(run._r)
                
            # 添加新的文本
            paragraph.add_run(new_text)
            continue  # 处理完占位符后，跳过后续处理
    """

    # 修复点2: 改进结论占位符处理，确保换行格式正确
    # 查找以下代码段:
    """
    # 检查是否包含结论占位符
    if '{结论}' in original_text:
        app.logger.info(f"段落 {i+1} 包含结论占位符")
        
    # 检查是否包含任何项目信息占位符
    for placeholder, value in extended_project_info.items():
        placeholder_text = '{' + placeholder + '}'
        if placeholder_text in new_text:
            # 如果是结论占位符，使用换行符进行替换
            if placeholder == '结论':
                # 分割结论文本为多行
                lines = value.split('\n')
                # 清空段落中所有runs，但保持段落本身
                p = paragraph._p
                for run in list(paragraph.runs):
                    p.remove(run._r)
                
                # 添加每一行，用换行符分隔
                for line_idx, line in enumerate(lines):
                    if line_idx > 0 and line: # 对于非首行且非空行，添加换行
                        paragraph.add_run().add_break()
                    if line: # 只添加非空行
                        paragraph.add_run(line)
                
                app.logger.info(f"替换了结论占位符，应用多行格式: {value}")
                text_changed = True
                # 跳过后续对该段落的处理
                break
    """
    
    # 替换为以下改进版本:
    """
    # 替换结论占位符
    if '{结论}' in original_text:
        app.logger.info(f"找到结论占位符")
        conclusion_value = extended_project_info.get('结论', '未提供结论')
        
        # 清空段落中所有runs，但保持段落本身
        p = paragraph._p
        for run in list(paragraph.runs):
            p.remove(run._r)
        
        # 分行添加结论文本
        lines = conclusion_value.split('\n')
        for line_idx, line in enumerate(lines):
            if line_idx > 0:  # 非首行添加换行
                paragraph.add_run().add_break()
            if line.strip():  # 只添加非空行
                paragraph.add_run(line)
        
        app.logger.info(f"替换结论占位符完成")
        continue  # 处理完占位符后，跳过后续处理
    """
    
    # 修复点3: 改进公交站点表格处理逻辑，确保表格创建和填充正确
    # 查找以下代码段:
    """
    # 处理公交站点列表占位符
    if '{公交站点列表}' in paragraph.text:
        app.logger.info(f"找到公交站点列表占位符")
        placeholder_found = True
        
        # 创建表格
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        
        # 设置表头
        header_cells = table.rows[0].cells
        header_cells[0].text = "序号"
        header_cells[1].text = "站点名称"
        header_cells[2].text = "类型"
        header_cells[3].text = "距离（米）"
        header_cells[4].text = "详细信息"
        
        # 添加数据行
        for idx, station in enumerate(stations):
            row = table.add_row()
            cells = row.cells
            
            # 记录处理的行数据
            app.logger.info(f"\n处理表格行 {idx+1}:")
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
            os.remove(output_path)  # 删除临时文件
            return jsonify({'success': False, 'message': f'替换段落为表格失败: {str(e)}'}), 500
    """
    
    # 替换为以下改进版本 (主要增强了日志和错误处理):
    """
    # 处理公交站点列表占位符
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
        
        # 添加数据行
        for idx, station in enumerate(stations):
            row = table.add_row()
            cells = row.cells
            
            app.logger.info(f"\n处理表格行 {idx+1}:")
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
        
        continue  # 处理完占位符后，跳过后续处理
    """
    
    # 修复点4: 改进表格单元格中占位符的处理
    # 在现有代码的基础上添加表格单元格占位符处理逻辑
    """
    # 处理表格中的占位符
    app.logger.info("\n开始处理表格中的占位符")
    
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
    """

    # 修复点5: 改进对站点数据的标准化处理
    # 查找以下代码段（在JavaScript中）:
    """
    // 确保所有站点都有详细信息字段
    if (requestData.stations && requestData.stations.length > 0) {
        console.log("处理站点详细信息字段...");
        requestData.stations = requestData.stations.map((station, index) => {
            // 记录原始站点数据
            console.log(`原始站点数据 ${index + 1}:`, JSON.stringify(station));
            
            // 确保所有重要字段都存在
            const normalizedStation = {
                index: station.index || (index + 1),
                name: station.name || '未知站点',
                type: station.type || '公交站',
                distance: station.distance || '0',
                // 优先使用detail字段，如果没有则使用其他可能的字段
                detail: station.detail || 
                       station.address || 
                       station.addressDetail || 
                       station.description || 
                       station.info || 
                       '无详细信息',
                location: station.location || { lng: 0, lat: 0 }
            };
            
            // 记录标准化后的站点数据
            console.log(`标准化后的站点数据 ${index + 1}:`, JSON.stringify(normalizedStation));
            
            return normalizedStation;
        });
    """
    
    # 保留此代码不变，但在后端添加类似的数据规范化处理
    """
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
    stations = standardized_stations
    app.logger.info(f"站点数据已标准化，共 {len(stations)} 个站点")
    """

    return "修复已完成，请按照以上指导修改原始代码"

def get_main_fixes_summary():
    """
    获取主要修复点的总结，方便用户理解需要做的修改
    """
    fixes = [
        "1. 改进特殊占位符处理：确保特殊占位符（如地图截图、结论、公交站点列表）被正确替换",
        "2. 改进结论占位符处理：确保结论文本中的换行格式正确",
        "3. 增强表格创建和填充逻辑：确保公交站点表格被正确创建和填充",
        "4. 添加表格单元格占位符处理：单独处理表格单元格中的占位符",
        "5. 数据标准化：在前端和后端都进行站点数据的标准化，确保字段格式一致"
    ]
    
    return "\n".join(fixes)

if __name__ == "__main__":
    print("公共交通站点分析报告修复补丁")
    print("------------------------")
    print("\n主要修复点：")
    print(get_main_fixes_summary())
    print("\n请将此补丁文件中的代码段应用到原始的 public_transport_analytics.py 文件中")
    print("具体修改方法请参考函数 apply_fix_to_fill_transport_report_template 中的注释") 