from docx import Document
import json
from flask import jsonify
import re
import os
from flask import current_app
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsmap

def replace_placeholders(template_path, data):
    try:
        # 加载Word模板
        doc = Document(template_path)
        
        # 处理项目信息
        project_fields = ['项目名称', '设计单位', '建设单位', '总建筑面积', '星级目标', '建筑类型', '建筑总分', '结构总分', '给排水总分', '电气总分', '暖通总分', '景观总分', 
        '建筑创新总分', '结构创新总分', '给排水创新总分', '电气创新总分', '暖通创新总分', '景观创新总分', '项目总分', '创新总分', '项目地点', '建筑高度', '建筑层数',
        '安全耐久总分','生活便利总分','健康舒适总分','资源节约总分','环境宜居总分','提高与创新总分','设计日期','环境健康与节能总分','环境健康与节能创新总分',
        ]
        
        # 添加占位符映射关系
        placeholder_mapping = {
            '建创总分': '建筑创新总分',
            '结创总分': '结构创新总分',
            '暖创总分': '暖通创新总分',
            '电创总分': '电气创新总分',
            '水创总分': '给排水创新总分',
            '景创总分': '景观创新总分',
            '创新总分': '提高与创新总分',
            '节能总分': '环境健康与节能总分',
            '节创总分': '环境健康与节能创新总分'
        }
        
        # 获取文档中的所有书签
        bookmarks_dict = {}
        for bookmark_start in doc.element.xpath('//w:bookmarkStart'):
            bookmark_name = bookmark_start.get(qn('w:name'))
            if not bookmark_name:
                continue
            
            # 获取书签的内容范围
            bookmark_id = bookmark_start.get(qn('w:id'))
            bookmark_end = doc.element.xpath(f'//w:bookmarkEnd[@w:id="{bookmark_id}"]')[0]
            
            # 创建一个范围对象来表示书签的内容
            bookmark_range = bookmark_start.getnext()
            while bookmark_range is not None and bookmark_range is not bookmark_end:
                if bookmark_range.tag.endswith('}r') or bookmark_range.tag.endswith('}p'):
                    break
                bookmark_range = bookmark_range.getnext()
            
            if bookmark_range is not None:
                bookmarks_dict[bookmark_name] = bookmark_range
                print(f"找到书签: {bookmark_name}")
            else:
                print(f"跳过无效书签: {bookmark_name}")
        
        # 处理数字格式的书签（条文号对应的得分）
        for bookmark_name, bookmark_range in bookmarks_dict.items():
            if re.match(r'\d+(?:\.\d+)*?', bookmark_name) or bookmark_name.startswith('f'):
                # 在数据中查找对应的得分
                for item in data:
                    # 将条文号转换为新的书签格式（去掉点号并添加f前缀）
                    bookmark_format = 'f' + str(item.get('条文号')).replace('.', '')
                    # 同时检查原始条文号格式和带f前缀的格式
                    if bookmark_format == bookmark_name or str(item.get('条文号')) == bookmark_name:
                        try:
                            # 创建新的文本运行
                            new_text = str(item.get('得分', ''))
                            new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{new_text}</w:t></w:r>')
                            
                            # 替换书签内容
                            if bookmark_range is not None:
                                parent = bookmark_range.getparent()
                                if parent is not None:
                                    parent.replace(bookmark_range, new_run)
                                    print(f"替换书签 {bookmark_name} 的值为: {new_text}")
                        except Exception as e:
                            print(f"替换书签 {bookmark_name} 时出错: {str(e)}")
                        break
        
        # 处理设计日期书签（包括带数字后缀的）
        from datetime import datetime
        current_date = datetime.now().strftime("%Y年%m月%d日")
        # 使用正则表达式匹配设计日期及其带数字后缀的变体
        date_pattern = re.compile(r'^设计日期[0-9]*$')
        for bookmark_name in list(bookmarks_dict.keys()):
            if date_pattern.match(bookmark_name):
                # 创建新的文本运行
                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{current_date}</w:t></w:r>')
                
                # 替换书签内容
                bookmark_range = bookmarks_dict[bookmark_name]
                if bookmark_range is not None:
                    parent = bookmark_range.getparent()
                    if parent is not None:
                        parent.replace(bookmark_range, new_run)
                        print(f"处理设计日期书签: {bookmark_name} -> {current_date}")

        
        # 处理标准字段书签（包括带数字后缀的书签）
        for field in project_fields:
            # 特殊处理星级目标字段
            field_pattern = re.compile(r'^星级目标[0-9]*$')
            if field_pattern.match(field):
                field_value = ''
                if data and isinstance(data[0], dict):
                    target = data[0].get('星级目标', '')
                    field_value = f'基本级{"■" if target == "基本级" else "□"}一星级{"■" if target == "一星级" else "□"}二星级{"■" if target == "二星级" else "□"}三星级{"■" if target == "三星级" else "□"}'
                    print(f"处理书签: {field} -> {field_value}")
                # 创建新的文本运行
                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                
                # 替换书签内容
                bookmark_range = bookmarks_dict[field]
                if bookmark_range is not None:
                    parent = bookmark_range.getparent()
                    if parent is not None:
                        parent.replace(bookmark_range, new_run)
                # 处理所有带数字后缀的相同字段
                for bookmark_name in list(bookmarks_dict.keys()):
                    if field_pattern.match(bookmark_name):
                        bookmark_range = bookmarks_dict[bookmark_name]
                        if bookmark_range is not None:
                            parent = bookmark_range.getparent()
                            if parent is not None:
                                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                                parent.replace(bookmark_range, new_run)
                                print(f"处理带数字后缀的书签: {bookmark_name} -> {field_value}")
                continue
            
            # 特殊处理绿色星级字段
            field_pattern = re.compile(r'^绿色星级[0-9]*$')
            if field_pattern.match(field) or field == '绿色星级':
                field_value = ''
                if data and isinstance(data[0], dict):
                    target = data[0].get('星级目标', '')
                    if target == '基本级':
                        field_value = '基本级'
                    elif target == '一星级':
                        field_value = '一星级'
                    elif target == '二星级':
                        field_value = '二星级'
                    elif target == '三星级':
                        field_value = '三星级'
                    else:
                        field_value = target
                    print(f"处理书签: {field} -> {field_value}")
                # 创建新的文本运行
                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                
                # 替换书签内容
                bookmark_range = bookmarks_dict[field]
                if bookmark_range is not None:
                    parent = bookmark_range.getparent()
                    if parent is not None:
                        parent.replace(bookmark_range, new_run)
                # 处理所有带数字后缀的相同字段
                for bookmark_name in list(bookmarks_dict.keys()):
                    if field_pattern.match(bookmark_name) or bookmark_name == '绿色星级':
                        bookmark_range = bookmarks_dict[bookmark_name]
                        if bookmark_range is not None:
                            parent = bookmark_range.getparent()
                            if parent is not None:
                                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                                parent.replace(bookmark_range, new_run)
                                print(f"处理带数字后缀的书签: {bookmark_name} -> {field_value}")
                continue
            
            # 特殊处理建筑类型字段
            field_pattern = re.compile(r'^建筑类型[0-9]*$')
            if field_pattern.match(field):
                field_value = ''
                if data and isinstance(data[0], dict):
                    building_type = data[0].get('建筑类型', '')
                    field_value = f'居住建筑{"■" if building_type == "居住建筑" else "□"} 公共建筑{"■" if building_type == "公共建筑" else "□"} 居住+公建{"■" if building_type == "居住+公建" else "□"}'
                    print(f"处理书签: {field} -> {field_value}")
                # 创建新的文本运行
                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                
                # 替换书签内容
                bookmark_range = bookmarks_dict[field]
                if bookmark_range is not None:
                    parent = bookmark_range.getparent()
                    if parent is not None:
                        parent.replace(bookmark_range, new_run)
                # 处理所有带数字后缀的相同字段
                for bookmark_name in list(bookmarks_dict.keys()):
                    if field_pattern.match(bookmark_name):
                        bookmark_range = bookmarks_dict[bookmark_name]
                        if bookmark_range is not None:
                            parent = bookmark_range.getparent()
                            if parent is not None:
                                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                                parent.replace(bookmark_range, new_run)
                                print(f"处理带数字后缀的书签: {bookmark_name} -> {field_value}")
                continue
            # 使用正则表达式匹配字段名及其带数字后缀的变体
            field_pattern = re.compile(f"{field}[0-9]*$")
            for bookmark_name in list(bookmarks_dict.keys()):
                if field_pattern.match(bookmark_name):
                    field_value = ''
                    if data and isinstance(data[0], dict):
                        field_value = str(data[0].get(field, ''))
                        print(f"处理书签: {bookmark_name} -> {field_value}")
                    # 创建新的文本运行
                    new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                    
                    # 替换书签内容
                    bookmark_range = bookmarks_dict[bookmark_name]
                    if bookmark_range is not None:
                        parent = bookmark_range.getparent()
                        if parent is not None:
                            parent.replace(bookmark_range, new_run)
        
        # 处理绿色星级书签
        field_pattern = re.compile(r'^绿色星级[0-9]*$')
        for bookmark_name in list(bookmarks_dict.keys()):
            if field_pattern.match(bookmark_name):
                field_value = ''
                if data and isinstance(data[0], dict):
                    target = data[0].get('星级目标', '')
                    if target == '基本级':
                        field_value = '基本级'
                    elif target == '一星级':
                        field_value = '一星级'
                    elif target == '二星级':
                        field_value = '二星级'
                    elif target == '三星级':
                        field_value = '三星级'
                    else:
                        field_value = target
                    print(f"处理书签: {bookmark_name} -> {field_value}")
                # 创建新的文本运行
                new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                
                # 替换书签内容
                bookmark_range = bookmarks_dict[bookmark_name]
                if bookmark_range is not None:
                    parent = bookmark_range.getparent()
                    if parent is not None:
                        parent.replace(bookmark_range, new_run)
        
        # 处理成都项目总分书签
        if '成都项目总分' in bookmarks_dict:
            field_value = ''
            if data and isinstance(data[0], dict):
                project_score = float(data[0].get('项目总分', '0'))
                field_value = format((project_score + 400) / 10, '.1f')
            # 创建新的文本运行
            new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
            
            # 替换书签内容
            bookmark_range = bookmarks_dict['成都项目总分']
            if bookmark_range is not None:
                parent = bookmark_range.getparent()
                if parent is not None:
                    parent.replace(bookmark_range, new_run)
        
        # 处理映射的简写书签（包括带数字后缀的）
        for short_name, full_name in placeholder_mapping.items():
            # 使用正则表达式匹配简写字段名及其带数字后缀的变体
            short_name_pattern = re.compile(f"{short_name}[0-9]*$")
            for bookmark_name in list(bookmarks_dict.keys()):
                if short_name_pattern.match(bookmark_name):
                    field_value = ''
                    if data and isinstance(data[0], dict):
                        field_value = str(data[0].get(full_name, ''))
                        print(f"处理简写书签: {bookmark_name} -> {field_value}")
                    # 创建新的文本运行
                    new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{field_value}</w:t></w:r>')
                    
                    # 替换书签内容
                    bookmark_range = bookmarks_dict[bookmark_name]
                    if bookmark_range is not None:
                        parent = bookmark_range.getparent()
                        if parent is not None:
                            parent.replace(bookmark_range, new_run)
                            print(f"替换简写书签: {bookmark_name} -> {field_value}")
        
        # 处理表格中的■字符，将其字体改为宋体
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            if '■' in run.text:
                                run.font.name = '宋体'
                                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                       
        # 确保temp目录存在
        os.makedirs('temp', exist_ok=True)
        
        # 生成带时间戳的输出文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join('temp', f'report_{timestamp}.docx')
        
        # 保存修改后的文档
        doc.save(output_path)
        print(f"文档已保存到: {output_path}")
        
        # 检查文件是否成功创建
        if not os.path.exists(output_path):
            raise Exception(f"文件保存失败: {output_path}")
            
        return output_path
    except Exception as e:
        return f'处理文档时出错：{str(e)}'

def process_template(data):
    try:
        from flask import current_app
        import os
        
        # 根据评价标准选择模板文件
        standard = data[0].get('standard', '成都市标')  # 默认使用成都市标
        
        if standard == '国标':
            return None  # 国标不进行任何操作
        
        # 根据评价标准选择模板文件
        template_file = 'sichuan_template.docx' if standard == '四川省标' else 'chengdu_template.docx'
        
        # 获取模板文件的完整路径
        template_path = os.path.join(current_app.static_folder, 'templates', template_file)
        print(f"处理模板文件: {template_path}")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            raise Exception(f"模板文件不存在: {template_path}")
                
        # 处理模板
        output_path = replace_placeholders(template_path, data)
        if not isinstance(output_path, str) or not output_path.endswith('.docx'):
            raise Exception(f"模板处理失败：{output_path}")
        
        # 返回生成的文档路径
        return output_path
        
    except Exception as e:
        print(f"处理模板失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f'生成Word文档失败：{str(e)}')