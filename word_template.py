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
        
        # 遍历文档中的所有段落和表格
        # for paragraph in doc.paragraphs:
        #     if not paragraph.text:
        #         continue
                
            # 获取段落中的所有运行对象
            # runs = paragraph.runs
            # if not runs:
            #     continue
                
            # # 合并所有运行的文本
            # text = paragraph.text
            
            # 使用正则表达式查找{x.x.x.x}和项目信息格式的占位符
            # modified = False
            # 处理数字格式的占位符
            # for match in re.finditer(r'\{(\d+(?:\.\d+)*?)\}', text):
            #     article_num = match.group(1)
            #     placeholder = match.group(0)
                
                # 在数据中查找对应的得分
                # for item in data:
                #     if str(item.get('条文号')) == article_num:
                #         replacement = str(item.get('得分', ''))
                #         # 在第一个运行对象中进行替换
                #         if runs:
                #             text = text.replace(placeholder, replacement)
                #             runs[0].text = text
                #             modified = True
                #         break
            
            # 处理项目信息占位符
            # project_fields = ['项目名称', '设计单位', '建设单位', '建筑面积']
            # for field in project_fields:
            #     field_match = re.search(r'\{' + field + r'\}', text)
            #     if field_match:
            #         # 确保data不为空且包含项目信息
            #         field_value = ''
            #         if data and isinstance(data[0], dict):
            #             field_value = str(data[0].get(field, ''))
            #         # 在所有运行对象中查找并替换占位符
            #         for run in runs:
            #             if field_match.group(0) in run.text:
            #                 run.text = run.text.replace(field_match.group(0), field_value)
            #                 modified = True
            #                 break
                        
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
                        project_fields = ['项目名称', '设计单位', '建设单位', '建筑面积']
                        for field in project_fields:
                            field_match = re.search(r'\{' + field + r'\}', text)
                            if field_match:
                                # 确保data不为空且包含项目信息
                                field_value = ''
                                if data and isinstance(data[0], dict):
                                    field_value = str(data[0].get(field, ''))
                                # 在所有运行对象中查找并替换占位符
                                for run in runs:
                                    if field_match.group(0) in run.text:
                                        run.text = run.text.replace(field_match.group(0), field_value)
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
    """
    处理Word模板，填充数据并生成新文档
    
    参数:
    - data: 包含项目信息和评分数据的列表
    
    返回:
    - 生成的文档路径
    """
    try:
        # 使用正确的模板路径
        from flask import current_app
        import os
        
        # 获取模板文件的完整路径
        template_path = os.path.join(current_app.static_folder, 'templates', 'chengdu_template1.docx')
        print(f"使用模板文件: {template_path}")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            raise Exception(f"模板文件不存在: {template_path}")
            
        # 处理模板
        output_path = replace_placeholders(template_path, data)
        if isinstance(output_path, str) and output_path.endswith('.docx'):
            return output_path
        else:
            raise Exception(f'模板处理失败：{output_path}')
    except Exception as e:
        print(f"处理模板失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f'生成Word文档失败：{str(e)}')