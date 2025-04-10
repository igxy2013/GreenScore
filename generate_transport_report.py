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
            - address: 项目地址
            - stations: 站点列表，每个站点包含 {name, type, distance, detail}
            - map_image: 地图截图的base64编码
            - conclusion: 分析结论，包含 {result6_1_2, result6_2_1, totalScore}
            - project_info: 项目基本信息
    
    返回:
        生成的文档路径
    """
    try:
        print("开始生成公共交通站点分析报告...")
        
        # 获取模板文件路径
        template_path = os.path.join("static", "templates", "公共交通站点分析报告.docx")
        if not os.path.exists(template_path):
            raise Exception(f"模板文件不存在: {template_path}")
        
        # 准备数据
        address = data.get('address', '')
        stations = data.get('stations', [])
        map_image = data.get('map_image', '')
        conclusion = data.get('conclusion', {})
        project_info = data.get('project_info', {})
        
        # 生成站点表格HTML
        stations_table = "<table border='1' style='width:100%; border-collapse: collapse;'>"
        stations_table += "<tr><th>序号</th><th>站点名称</th><th>类型</th><th>距离(m)</th><th>详细信息</th></tr>"
        
        for i, station in enumerate(stations):
            stations_table += f"<tr><td>{i+1}</td><td>{station.get('name', '')}</td><td>{station.get('type', '')}</td><td>{station.get('distance', '')}</td><td>{station.get('detail', '')}</td></tr>"
        
        stations_table += "</table>"
        
        # 准备模板数据
        template_data = [
            # 项目基本信息
            {
                "项目名称": project_info.get('项目名称', ''),
                "项目地点": project_info.get('项目地点', address),
                "项目编号": project_info.get('项目编号', ''),
                "建设单位": project_info.get('建设单位', ''),
                "设计单位": project_info.get('设计单位', ''),
                "总用地面积": project_info.get('总用地面积', ''),
                "总建筑面积": project_info.get('总建筑面积', ''),
                "建筑密度": project_info.get('建筑密度', ''),
                "绿地率": project_info.get('绿地率', ''),
                "容积率": project_info.get('容积率', ''),
                "项目地址": address,
                "设计日期": datetime.now().strftime("%Y年%m月%d日"),
                "地图截图": map_image,  # 这需要在模板处理函数中特殊处理
                "公交站点列表": stations_table,  # 这需要在模板处理函数中特殊处理
                "结论": conclusion.get('result6_1_2', '') + '\n\n' + conclusion.get('result6_2_1', '') + '\n\n总得分：' + str(conclusion.get('totalScore', 0)) + '分'
            }
        ]
        
        # 添加条文得分数据
        template_data.append({
            "条文号": "6.1.2",
            "得分": "符合" if conclusion.get('result6_1_2', '').startswith('符合') else "不符合",
            "技术措施": conclusion.get('result6_1_2', '')
        })
        
        template_data.append({
            "条文号": "6.2.1",
            "得分": str(conclusion.get('totalScore', 0)),
            "技术措施": conclusion.get('result6_2_1', '')
        })
        
        # 使用word_template模块生成报告
        print("调用replace_placeholders生成报告...")
        output_path = replace_placeholders(template_path, template_data)
        
        # 返回生成的文档路径
        return output_path
        
    except Exception as e:
        print(f"生成公共交通站点分析报告失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f"生成公共交通站点分析报告失败: {str(e)}")

if __name__ == "__main__":
    # 测试数据
    test_data = {
        "address": "成都市武侯区天府大道北段1700号",
        "stations": [
            {"name": "天府五街站", "type": "公交站", "distance": "120", "detail": "1路、2路、3路"},
            {"name": "天府三街站", "type": "公交站", "distance": "350", "detail": "4路、5路"},
            {"name": "天府二街站", "type": "地铁站", "distance": "480", "detail": "1号线、7号线"}
        ],
        "map_image": "", # 实际使用时需要提供base64编码的图片
        "conclusion": {
            "result6_1_2": "符合规范6.1.2要求。最近公交站距离为120m，最近地铁站距离为480m。",
            "result6_2_1": "按照规范6.2.1评分，总得分为8分，其中：\n- 最近公交站距离为120m，最近地铁站距离为480m，得4分；\n- 周边800m内有3个公交站（包括天府五街站、天府三街站等），有1个地铁站（包括天府二街站），总计5条线路，得4分。",
            "totalScore": 8
        },
        "project_info": {
            "项目名称": "测试项目",
            "项目地点": "成都市武侯区天府大道北段1700号",
            "项目编号": "TEST-2024-001",
            "建设单位": "测试建设公司",
            "设计单位": "测试设计院",
            "总用地面积": "5000",
            "总建筑面积": "20000",
            "建筑密度": "35",
            "绿地率": "30",
            "容积率": "4.0"
        }
    }
    
    output_path = generate_transport_report(test_data)
    print(f"报告已生成: {output_path}") 