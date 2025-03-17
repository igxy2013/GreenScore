from docx import Document
import json
from flask import jsonify
import re
import os
from flask import current_app

def replace_placeholders(template_path, data):
    try:
        # 加载Word模板
        doc = Document(template_path)
        
        # 遍历表格中的单元格
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if not paragraph.text:
                            continue
                            
                        # 获取段落中的所有运行对象
                        runs = paragraph.runs
                        if not runs:
                            continue
                            
                        # 合并所有运行的文本
                        text = paragraph.text
                        
                        # 使用正则表达式查找{x.x.x.x}和{项目名称}格式的占位符
                        modified = False
                        # 处理数字格式的占位符
                        for match in re.finditer(r'\{(\d+(?:\.\d+)*?)\}', text):
                            article_num = match.group(1)
                            placeholder = match.group(0)
                            
                            # 在数据中查找对应的得分
                            for item in data:
                                if str(item.get('条文号')) == article_num:
                                    replacement = str(item.get('得分', ''))
                                    # 在第一个运行对象中进行替换
                                    if runs:
                                        text = text.replace(placeholder, replacement)
                                        runs[0].text = text
                                        modified = True
                                    break
                        
                        # 处理项目信息占位符
                        project_fields = ['项目名称', '设计单位', '建设单位', '总建筑面积', '星级目标','建筑类型','建筑总分','结构总分','给排水总分','电气总分','暖通总分','景观总分'
                        ,'建筑创新总分','结构创新总分','给排水创新总分','电气创新总分','暖通创新总分','景观创新总分','项目总分','创新总分']
                        
                        # 添加占位符映射关系
                        placeholder_mapping = {
                            '建创总分': '建筑创新总分',
                            '结创总分': '结构创新总分',
                            '暖创总分': '暖通创新总分',
                            '电创总分': '电气创新总分',
                            '景创总分': '景观创新总分',
                            '创新总分': '提高与创新总分'
                        }
                        # 处理设计日期占位符
                        date_match = re.search(r'\{设计日期\}', text)
                        if date_match:
                            from datetime import datetime
                            current_date = datetime.now().strftime("%Y年%m月%d日")
                            # 在所有运行对象中查找并替换占位符
                            for run in runs:
                                if date_match.group(0) in run.text:
                                    run.text = run.text.replace(date_match.group(0), current_date)
                                    modified = True
                                    break
                        # 处理标准字段
                        for field in project_fields:
                            field_match = re.search(r'\{' + field + r'\}', text)
                            if field_match:
                                # 添加调试信息
                                print(f"找到字段: {field}")
                                # 确保data不为空且包含项目信息
                                field_value = ''
                                if data and isinstance(data[0], dict):
                                    field_value = str(data[0].get(field, ''))
                                    print(f"字段 {field} 的值: {field_value}")
                                # 在所有运行对象中查找并替换占位符
                                for run in runs:
                                    if field_match.group(0) in run.text:
                                        run.text = run.text.replace(field_match.group(0), field_value)
                                        modified = True
                                        print(f"替换完成: {field} -> {field_value}")
                                        break
                        
                        # 处理映射的简写占位符
                        for short_name, full_name in placeholder_mapping.items():
                            short_match = re.search(r'\{' + short_name + r'\}', text)
                            if short_match:
                                field_value = ''
                                if data and isinstance(data[0], dict):
                                    field_value = str(data[0].get(full_name, ''))
                                # 在所有运行对象中查找并替换占位符
                                for run in runs:
                                    if short_match.group(0) in run.text:
                                        run.text = run.text.replace(short_match.group(0), field_value)
                                        modified = True
                                        break
                       
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
        
        # 使用单个模板文件
        template_file = 'chengdu_template1.docx'
        
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