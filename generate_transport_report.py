from word_template import replace_placeholders
import os
import json
from datetime import datetime
from flask import current_app

def generate_transport_report(data):
    """
    生成公共交通站点分析报告
    
    参数:
        data: 包含以下字段的字典：
            - address: 详细地址
            - stations: 站点列表，每个站点包含 {name, type, distance, detail}
            - map_image: 地图截图的base64编码
            - conclusion: 分析结论，包含 {result6_1_2, result6_2_1, totalScore}
            - project_info: 项目基本信息
    
    返回:
        生成的文档路径
    """
    try:
        print("\n=== 开始生成公共交通站点分析报告 ===")
        
        # 获取模板文件路径
        template_path = os.path.join("static", "templates", "公共交通站点分析报告.docx")
        if not os.path.exists(template_path):
            raise Exception(f"模板文件不存在: {template_path}")
        
        print(f"使用模板: {template_path}")
        
        # 提取数据
        address = data.get('address', '')
        stations = data.get('stations', [])
        map_image = data.get('mapImage', '')
        conclusion = data.get('conclusion', {})
        project_info = data.get('project_info', {})
        project_id = data.get('project_id', '')
        
        print(f"项目ID: {project_id}")
        print(f"地址: {address}")
        print(f"站点数量: {len(stations)}")
        print(f"结论: {conclusion}")
        
        # 输出项目信息
        print("\n项目信息内容:")
        print(json.dumps(project_info, ensure_ascii=False, indent=2))
        
        # 准备数据
        final_data = []
        
        # 创建完整的项目信息字典
        project_data = {}
        
        # 首先添加所有原始项目信息字段
        for key, value in project_info.items():
            project_data[key] = value
        
        # 添加地址相关字段，确保各种格式的占位符都能被替换
        address_fields = ['详细地址', '地址', '项目地址', '公共交通地址', 'address']
        for field in address_fields:
            project_data[field] = address
        
        # 添加结论字段，确保各种格式的占位符都能被替换
        conclusion_text = ""
        if isinstance(conclusion, dict):
            result6_1_2 = conclusion.get('result6_1_2', '')
            result6_2_1 = conclusion.get('result6_2_1', '')
            total_score = conclusion.get('totalScore', 0)
            conclusion_text = f"{result6_1_2}\n\n{result6_2_1}\n\n总得分：{total_score}分"
        elif isinstance(conclusion, str):
            conclusion_text = conclusion
        
        conclusion_fields = ['结论', '交通分析结论', '分析结论', '评价结论']
        for field in conclusion_fields:
            project_data[field] = conclusion_text
        
        # 添加当前日期
        current_date = datetime.now().strftime("%Y年%m月%d日")
        project_data['设计日期'] = current_date
        project_data['日期'] = current_date
        
        # 将项目信息添加到final_data
        final_data.append(project_data)
        
        # 输出最终数据结构（部分）
        print("\n最终处理的数据结构(部分):")
        print(f"详细地址: {project_data.get('详细地址', '未设置')}")
        print(f"项目名称: {project_data.get('projectName', '未设置')}")
        print(f"结论: {project_data.get('结论', '未设置')[:100]}...")
        
        # 调用Word模板处理函数
        output_path = replace_placeholders(template_path, final_data)
        
        print(f"\n报告生成完成: {output_path}")
        
        return output_path
    except Exception as e:
        print(f"生成报告失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f"生成报告失败: {str(e)}")