import os
import platform
from flask import jsonify, current_app, send_file, request
from dotenv import load_dotenv
from docx import Document
from word_template import process_template, replace_placeholders, replace_placeholders_format
import json
import traceback
from sqlalchemy import text
import pymysql
from models import db
from datetime import datetime

# 加载环境变量
load_dotenv()


# 数据库连接配置
def get_db_connection():
    try:
        # 解析数据库连接字符串
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("数据库连接字符串未配置")
            raise ValueError("数据库连接字符串未配置")

        if IS_WSL:
            # WSL环境下使用MySQL连接
            # 使用正则表达式解析连接字符串
            import re
            pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/([^?]+)'
            match = re.match(pattern, db_url)
            if not match:
                print("数据库连接字符串格式错误")
                raise ValueError("数据库连接字符串格式错误")

            username, password, server, database = match.groups()
            
            try:
                conn = pymysql.connect(
                    host=server,
                    user=username,
                    password=password,
                    database=database,
                    charset='utf8mb4'
                )
                current_app.logger.info("MySQL数据库连接成功")
                return conn
            except Exception as e:
                current_app.logger.error(f"MySQL数据库连接失败: {str(e)}")
                raise
        else:
            # Windows环境下使用SQL Server连接
            # 使用正则表达式解析连接字符串
            import re
            pattern = r'mssql\+pyodbc://([^:]+):([^@]+)@([^/]+)/([^?]+)'
            match = re.match(pattern, db_url)
            if not match:
                print("数据库连接字符串格式错误")
                raise ValueError("数据库连接字符串格式错误")

            username, password, server, database = match.groups()

            # 构建连接字符串，添加超时和TLS配置
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Connection Timeout=30;Encrypt=yes;TrustServerCertificate=yes"
            # 尝试建立连接
            try:
                conn = pyodbc.connect(conn_str)
                current_app.logger.info("SQL Server数据库连接成功")
                return conn
            except Exception as e:
                current_app.logger.error(f"SQL Server数据库连接失败: {str(e)}")
                raise
    except Exception as e:
        current_app.logger.error(f"创建数据库连接时出错: {str(e)}")
        raise

from models import db

def generate_word(request_data):
    """
    生成Word文档的函数
    
    参数:
    - request_data: 包含project_id和standard的字典
    
    返回:
    - tuple: (response, status_code)
    """
    try:
        # 从请求参数中获取项目ID
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "请提供项目ID"}), 400
            
        # 获取评价标准参数，默认为成都市标
        standard = request_data.get('standard', '成都市标')
        print(f"使用评价标准: {standard}")

        # 检查模板文件是否存在
        template_file = 'sichuan_template.docx' if standard == '四川省标' else 'chengdu_template.docx'
        template_path = os.path.join(current_app.static_folder, 'templates', template_file)
        
        if not os.path.exists(template_path):
            print(f"模板文件不存在: {template_path}")
            return jsonify({"error": f"模板文件不存在: {template_file}"}), 404

        # 尝试从缓存获取数据
        cache_file = os.path.join('temp', f'project_{project_id}_{standard}_cache.json')
        data = None
        use_cache = request_data.get('use_cache', True)
        
        if use_cache and os.path.exists(cache_file):
            try:
                print(f"从缓存文件加载数据: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("成功从缓存加载数据")
                
                # 检查缓存数据是否有效
                if not data or len(data) < 1 or not isinstance(data[0], dict) or not data[0].get("项目名称"):
                    print("缓存数据无效，将从数据库重新获取")
                    data = None
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                data = None

        # 如果缓存不存在或无效，从数据库获取数据
        if not data:
            print("从数据库获取数据...")
            
            # 获取项目基本信息
            print(f"获取项目 {project_id} 的基本信息")
            result = db.session.execute(
                text("""
                    SELECT p.id, p.user_id, p.name, p.code, p.construction_unit, p.design_unit, p.location, 
                           p.building_area, p.standard, p.building_type, p.created_at, p.climate_zone, 
                           p.star_rating_target, p.total_land_area, p.total_building_area, p.above_ground_area, 
                           p.underground_area, p.building_height, p.building_floors, p.underground_floor_area, 
                           p.ground_parking_spaces, p.plot_ratio, p.building_base_area, p.building_density, 
                           p.green_area, p.green_ratio, p.residential_units, p.air_conditioning_type,
                           p.average_floors, p.has_garbage_room, p.has_elevator, p.has_underground_garage,
                           p.construction_type, p.has_water_landscape, p.is_fully_decorated, p.public_building_type,
                           p.public_green_space, p.architecture_score, p.structure_score, p.water_supply_score, 
                           p.electrical_score, p.hvac_score, p.landscape_score, p.env_health_energy_score,
                           p.env_health_energy_innovation_score, p.architecture_innovation_score, 
                           p.structure_innovation_score, p.hvac_innovation_score, p.landscape_innovation_score, 
                           p.safety_durability_score, p.health_comfort_score, p.life_convenience_score, 
                           p.resource_saving_score, p.environment_livability_score, p.improvement_innovation_score, 
                           p.total_score, p.evaluation_result
                    FROM projects p
                    WHERE p.id = :project_id
                """),
                {"project_id": project_id}
            )
            project_rows = result.fetchall()

            if not project_rows:
                print(f"未找到项目数据: ID={project_id}")
                return jsonify({"error": "未找到项目数据"}), 404

            print(f"获取到项目数据: {project_rows[0]}")

            # 准备数据
            data = []
            # 添加项目信息作为第一条数据
            data.append({
                "项目ID": str(project_rows[0][0] or ''),
                "用户ID": str(project_rows[0][1] or ''),
                "项目名称": project_rows[0][2] or '',
                "项目编号": project_rows[0][3] or '',
                "建设单位": project_rows[0][4] or '',
                "设计单位": project_rows[0][5] or '',
                "项目地点": project_rows[0][6] or '',
                "建筑面积": str(project_rows[0][7] or '0'),
                "评价标准": project_rows[0][8] or '成都市标',
                "建筑类型": project_rows[0][9] or '',
                "创建时间": project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else '',
                "气候区划": project_rows[0][11] or '',
                "星级目标": project_rows[0][12] or '',
                "总用地面积": str(project_rows[0][13] or '0'),
                "总建筑面积": str(project_rows[0][14] or '0'),
                "地上建筑面积": str(project_rows[0][15] or '0'),
                "地下建筑面积": str(project_rows[0][16] or '0'),
                "建筑高度": str(project_rows[0][17] or '0'),
                "建筑层数": project_rows[0][18] or '',
                "地下一层建筑面积": str(project_rows[0][19] or '0'),
                "地面停车位数量": str(project_rows[0][20] or '0'),
                "容积率": str(project_rows[0][21] or '0'),
                "建筑基底面积": str(project_rows[0][22] or '0'),
                "建筑密度": str(project_rows[0][23] or '0'),
                "绿地面积": str(project_rows[0][24] or '0'),
                "绿地率": str(project_rows[0][25] or '0'),
                "住宅户数": str(project_rows[0][26] or '0'),
                "空调类型": project_rows[0][27] or '',
                "平均层数": project_rows[0][28] or '',
                "有无垃圾用房": project_rows[0][29] or '',
                "有无电梯": project_rows[0][30] or '',
                "有无地下车库": project_rows[0][31] or '',
                "建设情况": project_rows[0][32] or '',
                "有无景观水体": project_rows[0][33] or '',
                "是否全装修": project_rows[0][34] or '',
                "公建类型": project_rows[0][35] or '',
                "绿地向公众开放": project_rows[0][36] or '',
                "建筑总分": str(project_rows[0][37] or '0'),
                "结构总分": str(project_rows[0][38] or '0'),
                "给排水总分": str(project_rows[0][39] or '0'),
                "电气总分": str(project_rows[0][40] or '0'),
                "暖通总分": str(project_rows[0][41] or '0'),
                "景观总分": str(project_rows[0][42] or '0'),
                "环境健康与节能总分": str(project_rows[0][43] or '0'),
                "环境健康与节能创新总分": str(project_rows[0][44] or '0'),
                "建筑创新总分": str(project_rows[0][45] or '0'),
                "结构创新总分": str(project_rows[0][46] or '0'),
                "暖通创新总分": str(project_rows[0][47] or '0'),
                "景观创新总分": str(project_rows[0][48] or '0'),
                "安全耐久总分": str(project_rows[0][49] or '0'),
                "健康舒适总分": str(project_rows[0][50] or '0'),
                "生活便利总分": str(project_rows[0][51] or '0'),
                "资源节约总分": str(project_rows[0][52] or '0'),
                "环境宜居总分": str(project_rows[0][53] or '0'),
                "提高与创新总分": str(project_rows[0][54] or '0'),
                "项目总分": str(project_rows[0][55] or '0'),
                "评定结果": project_rows[0][56] or ''
            })

            # 获取得分数据
            print(f"获取项目 {project_id} 的得分数据")
            result = db.session.execute(
                text("""
                    SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                    FROM 得分表 
                    WHERE 项目ID = :project_id
                    ORDER BY 条文号
                """),
                {"project_id": project_id}
            )
            score_rows = result.fetchall()
            
            print(f"获取到 {len(score_rows)} 条得分数据")

            # 添加得分数据
            for score_row in score_rows:
                data.append({
                    "条文号": score_row[0] or '',
                    "分类": score_row[1] or '',
                    "是否达标": score_row[2] or '',
                    "得分": str(score_row[3] or '0'),
                    "技术措施": score_row[4] or ''
                })

            # 保存数据到缓存
            try:
                os.makedirs('temp', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"数据已保存到缓存: {cache_file}")
            except Exception as e:
                print(f"保存缓存失败: {str(e)}")

        # 使用word_template模块处理文档
        print("开始处理Word模板...")
        print(f"数据内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            # 使用word_template模块处理文档
            output_file = process_template(data)
            
            # 处理国标情况，国标时process_template返回None
            if output_file is None:
                # 对于国标，使用绿色建筑设计自评估报告.docx模板
                standard = data[0].get('评价标准')
                print(f"检测到评价标准为{standard}，使用绿色建筑设计自评估报告模板")
                template_path = os.path.join(current_app.static_folder, 'templates', '绿色建筑设计自评估报告.docx')
                
                # 确保模板文件存在
                if not os.path.exists(template_path):
                    print(f"模板文件不存在: {template_path}")
                    return jsonify({"error": "模板文件不存在"}), 404
                
                try:
                    # 调用word_template模块的replace_placeholders函数处理占位符
                    output_file = replace_placeholders(template_path, data)
                    print(f"占位符替换完成，输出文件: {output_file}")
                except Exception as e:
                    print(f"处理占位符时出错: {str(e)}")
                    print(f"异常详情: {traceback.format_exc()}")
                    return jsonify({"error": f"处理占位符失败: {str(e)}"}), 500
            
            print(f"Word文档生成成功: {output_file}")
            
            # 检查生成的文件是否存在
            if not os.path.exists(output_file):
                print(f"生成的文件不存在: {output_file}")
                return jsonify({"error": "生成的文件不存在"}), 500
                
            # 获取文件名
            download_name = f"{data[0]['项目名称']}_报审表.docx"
            if not download_name:
                download_name = "report.docx"
            
            print(f"准备下载文件: {download_name}")
            return send_file(
                output_file,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        except Exception as e:
            print(f"处理Word模板失败: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            return jsonify({"error": f"处理Word模板失败: {str(e)}"}), 500

    except Exception as e:
        print(f"生成Word文档失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"生成Word文档失败: {str(e)}"}), 500

def save_project_info(project_data):
    """
    保存项目信息到本地缓存和数据库
    
    参数:
    - project_data: 包含项目信息的字典
    
    返回:
    - tuple: (response, status_code)
    """
    try:
        project_id = project_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "请提供项目ID"}), 400

        # 清除旧缓存
        cache_file = os.path.join('temp', f'project_{project_id}_cache.json')
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"已清除旧缓存: {cache_file}")
            except Exception as e:
                print(f"清除旧缓存失败: {str(e)}")

        # 更新项目信息
        result = db.session.execute(
            text("""
                UPDATE projects 
                SET name = :project_name, 
                    design_unit = :design_unit,
                    construction_unit = :construction_unit,
                    total_building_area = :total_building_area,
                    building_type = :building_type,
                    location = :location,
                    climate_zone = :climate_zone,
                    star_rating_target = :star_rating_target
                WHERE id = :project_id
            """),
            {
                "project_name": project_data.get('project_name', ''),
                "design_unit": project_data.get('design_unit', ''),
                "construction_unit": project_data.get('construction_unit', ''),
                "total_building_area": project_data.get('total_building_area', ''),
                "building_type": project_data.get('building_type', ''),
                "location": project_data.get('location', ''),
                "climate_zone": project_data.get('climate_zone', ''),
                "star_rating_target": project_data.get('star_rating_target', ''),
                "project_id": project_id
            }
        )
        
        db.session.commit()
        print("项目信息已保存到数据库")
        
        # 创建新的缓存
        try:
            # 获取最新的项目信息
            result = db.session.execute(
                text("""
                    SELECT name, design_unit, construction_unit, total_building_area
                    FROM projects 
                    WHERE id = :project_id
                """),
                {"project_id": project_id}
            )
            project_rows = result.fetchall()
            
            if project_rows:
                # 获取得分数据
                result = db.session.execute(
                    text("""
                        SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                        FROM 得分表 
                        WHERE 项目ID = :project_id
                        ORDER BY 条文号
                    """),
                    {"project_id": project_id}
                )
                score_rows = result.fetchall()
                
                # 准备数据
                data = []
                # 添加项目信息作为第一条数据
                data.append({
                    "项目ID": str(project_rows[0][0] or ''),
                    "用户ID": str(project_rows[0][1] or ''),
                    "项目名称": project_rows[0][2] or '',
                    "项目编号": project_rows[0][3] or '',
                    "建设单位": project_rows[0][4] or '',
                    "设计单位": project_rows[0][5] or '',
                    "项目地点": project_rows[0][6] or '',
                    "建筑面积": str(project_rows[0][7] or '0'),
                    "评价标准": project_rows[0][8] or '成都市标',
                    "建筑类型": project_rows[0][9] or '',
                    "创建时间": project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else '',
                    "气候区划": project_rows[0][11] or '',
                    "星级目标": project_rows[0][12] or '',
                    "总用地面积": str(project_rows[0][13] or '0'),
                    "总建筑面积": str(project_rows[0][14] or '0'),
                    "地上建筑面积": str(project_rows[0][15] or '0'),
                    "地下建筑面积": str(project_rows[0][16] or '0'),
                    "建筑高度": str(project_rows[0][17] or '0'),
                    "建筑层数": project_rows[0][18] or '',
                    "地下一层建筑面积": str(project_rows[0][19] or '0'),
                    "地面停车位数量": str(project_rows[0][20] or '0'),
                    "容积率": str(project_rows[0][21] or '0'),
                    "建筑基底面积": str(project_rows[0][22] or '0'),
                    "建筑密度": str(project_rows[0][23] or '0'),
                    "绿地面积": str(project_rows[0][24] or '0'),
                    "绿地率": str(project_rows[0][25] or '0'),
                    "住宅户数": str(project_rows[0][26] or '0'),
                    "空调类型": project_rows[0][27] or '',
                    "平均层数": project_rows[0][28] or '',
                    "有无垃圾用房": project_rows[0][29] or '',
                    "有无电梯": project_rows[0][30] or '',
                    "有无地下车库": project_rows[0][31] or '',
                    "建设情况": project_rows[0][32] or '',
                    "有无景观水体": project_rows[0][33] or '',
                    "是否全装修": project_rows[0][34] or '',
                    "公建类型": project_rows[0][35] or '',
                    "绿地向公众开放": project_rows[0][36] or '',
                    "建筑总分": str(project_rows[0][37] or '0'),
                    "结构总分": str(project_rows[0][38] or '0'),
                    "给排水总分": str(project_rows[0][39] or '0'),
                    "电气总分": str(project_rows[0][40] or '0'),
                    "暖通总分": str(project_rows[0][41] or '0'),
                    "景观总分": str(project_rows[0][42] or '0'),
                    "环境健康与节能总分": str(project_rows[0][43] or '0'),
                    "环境健康与节能创新总分": str(project_rows[0][44] or '0'),
                    "建筑创新总分": str(project_rows[0][45] or '0'),
                    "结构创新总分": str(project_rows[0][46] or '0'),
                    "暖通创新总分": str(project_rows[0][47] or '0'),
                    "景观创新总分": str(project_rows[0][48] or '0'),
                    "安全耐久总分": str(project_rows[0][49] or '0'),
                    "健康舒适总分": str(project_rows[0][50] or '0'),
                    "生活便利总分": str(project_rows[0][51] or '0'),
                    "资源节约总分": str(project_rows[0][52] or '0'),
                    "环境宜居总分": str(project_rows[0][53] or '0'),
                    "提高与创新总分": str(project_rows[0][54] or '0'),
                    "项目总分": str(project_rows[0][55] or '0'),
                    "评定结果": project_rows[0][56] or ''
                })
                
                # 添加得分数据
                for score_row in score_rows:
                    data.append({
                        "条文号": score_row[0] or '',
                        "分类": score_row[1] or '',
                        "是否达标": score_row[2] or '',
                        "得分": str(score_row[3] or '0'),
                        "技术措施": score_row[4] or ''
                    })
                
                # 保存到缓存
                os.makedirs('temp', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"最新项目信息已保存到缓存: {cache_file}")
            else:
                print("未找到项目数据，无法创建缓存")
        except Exception as e:
            print(f"创建新缓存失败: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
        
        return jsonify({"message": "项目信息保存成功"}), 200

    except Exception as e:
        print(f"保存项目信息失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"保存项目信息失败: {str(e)}"}), 500

def generate_self_assessment_report(request_data):
    """
    生成绿色建筑设计自评估报告的函数
    
    参数:
    - request_data: 包含project_id的字典
    
    返回:
    - tuple: (response, status_code)
    """
    try:
        # 从请求参数中获取项目ID
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "请提供项目ID"}), 400
            
        # 检查模板文件是否存在
        template_file = '绿色建筑设计自评估报告.docx'
        template_path = os.path.join(current_app.static_folder, 'templates', template_file)
        
        if not os.path.exists(template_path):
            print(f"模板文件不存在: {template_path}")
            return jsonify({"error": f"模板文件不存在: {template_file}"}), 404

        # 尝试从缓存获取数据
        cache_file = os.path.join('temp', f'project_{project_id}_cache.json')
        data = None
        use_cache = request_data.get('use_cache', True)
        
        if use_cache and os.path.exists(cache_file):
            try:
                print(f"从缓存文件加载数据: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("成功从缓存加载数据")
                
                # 检查缓存数据是否有效
                if not data or len(data) < 1 or not isinstance(data[0], dict) or not data[0].get("项目名称"):
                    print("缓存数据无效，将从数据库重新获取")
                    data = None
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                data = None

        # 如果缓存不存在或无效，从数据库获取数据
        if not data:
            print("从数据库获取数据...")
            
            # 获取项目基本信息
            print(f"获取项目 {project_id} 的基本信息")
            result = db.session.execute(
                text("""
                    SELECT p.id, p.user_id, p.name, p.code, p.construction_unit, p.design_unit, p.location, 
                           p.building_area, p.standard, p.building_type, p.created_at, p.climate_zone, 
                           p.star_rating_target, p.total_land_area, p.total_building_area, p.above_ground_area, 
                           p.underground_area, p.building_height, p.building_floors, p.underground_floor_area, 
                           p.ground_parking_spaces, p.plot_ratio, p.building_base_area, p.building_density, 
                           p.green_area, p.green_ratio, p.residential_units, p.air_conditioning_type,
                           p.average_floors, p.has_garbage_room, p.has_elevator, p.has_underground_garage,
                           p.construction_type, p.has_water_landscape, p.is_fully_decorated, p.public_building_type,
                           p.public_green_space, p.architecture_score, p.structure_score, p.water_supply_score, 
                           p.electrical_score, p.hvac_score, p.landscape_score, p.env_health_energy_score,
                           p.env_health_energy_innovation_score, p.architecture_innovation_score, 
                           p.structure_innovation_score, p.hvac_innovation_score, p.landscape_innovation_score, 
                           p.safety_durability_score, p.health_comfort_score, p.life_convenience_score, 
                           p.resource_saving_score, p.environment_livability_score, p.improvement_innovation_score, 
                           p.total_score, p.evaluation_result
                    FROM projects p
                    WHERE p.id = :project_id
                """),
                {"project_id": project_id}
            )
            project_rows = result.fetchall()

            if not project_rows:
                print(f"未找到项目数据: ID={project_id}")
                return jsonify({"error": "未找到项目数据"}), 404

            print(f"获取到项目数据: {project_rows[0]}")

            # 准备数据
            data = []
            # 添加项目信息作为第一条数据
            data.append({
                "项目ID": str(project_rows[0][0] or ''),
                "用户ID": str(project_rows[0][1] or ''),
                "项目名称": project_rows[0][2] or '',
                "项目编号": project_rows[0][3] or '',
                "建设单位": project_rows[0][4] or '',
                "设计单位": project_rows[0][5] or '',
                "项目地点": project_rows[0][6] or '',
                "建筑面积": str(project_rows[0][7] or '0'),
                "评价标准": project_rows[0][8] or '成都市标',
                "建筑类型": project_rows[0][9] or '',
                "创建时间": project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else '',
                "气候区划": project_rows[0][11] or '',
                "星级目标": project_rows[0][12] or '',
                "总用地面积": str(project_rows[0][13] or '0'),
                "总建筑面积": str(project_rows[0][14] or '0'),
                "地上建筑面积": str(project_rows[0][15] or '0'),
                "地下建筑面积": str(project_rows[0][16] or '0'),
                "建筑高度": str(project_rows[0][17] or '0'),
                "建筑层数": project_rows[0][18] or '',
                "地下一层建筑面积": str(project_rows[0][19] or '0'),
                "地面停车位数量": str(project_rows[0][20] or '0'),
                "容积率": str(project_rows[0][21] or '0'),
                "建筑基底面积": str(project_rows[0][22] or '0'),
                "建筑密度": str(project_rows[0][23] or '0'),
                "绿地面积": str(project_rows[0][24] or '0'),
                "绿地率": str(project_rows[0][25] or '0'),
                "住宅户数": str(project_rows[0][26] or '0'),
                "空调类型": project_rows[0][27] or '',
                "平均层数": project_rows[0][28] or '',
                "有无垃圾用房": project_rows[0][29] or '',
                "有无电梯": project_rows[0][30] or '',
                "有无地下车库": project_rows[0][31] or '',
                "建设情况": project_rows[0][32] or '',
                "有无景观水体": project_rows[0][33] or '',
                "是否全装修": project_rows[0][34] or '',
                "公建类型": project_rows[0][35] or '',
                "绿地向公众开放": project_rows[0][36] or '',
                "建筑总分": str(project_rows[0][37] or '0'),
                "结构总分": str(project_rows[0][38] or '0'),
                "给排水总分": str(project_rows[0][39] or '0'),
                "电气总分": str(project_rows[0][40] or '0'),
                "暖通总分": str(project_rows[0][41] or '0'),
                "景观总分": str(project_rows[0][42] or '0'),
                "环境健康与节能总分": str(project_rows[0][43] or '0'),
                "环境健康与节能创新总分": str(project_rows[0][44] or '0'),
                "建筑创新总分": str(project_rows[0][45] or '0'),
                "结构创新总分": str(project_rows[0][46] or '0'),
                "暖通创新总分": str(project_rows[0][47] or '0'),
                "景观创新总分": str(project_rows[0][48] or '0'),
                "安全耐久总分": str(project_rows[0][49] or '0'),
                "健康舒适总分": str(project_rows[0][50] or '0'),
                "生活便利总分": str(project_rows[0][51] or '0'),
                "资源节约总分": str(project_rows[0][52] or '0'),
                "环境宜居总分": str(project_rows[0][53] or '0'),
                "提高与创新总分": str(project_rows[0][54] or '0'),
                "项目总分": str(project_rows[0][55] or '0'),
                "评定结果": project_rows[0][56] or ''
            })

            # 获取得分数据
            print(f"获取项目 {project_id} 的得分数据")
            result = db.session.execute(
                text("""
                    SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                    FROM 得分表 
                    WHERE 项目ID = :project_id
                    ORDER BY 条文号
                """),
                {"project_id": project_id}
            )
            score_rows = result.fetchall()
            
            print(f"获取到 {len(score_rows)} 条得分数据")

            # 添加得分数据
            for score_row in score_rows:
                data.append({
                    "条文号": score_row[0] or '',
                    "分类": score_row[1] or '',
                    "是否达标": score_row[2] or '',
                    "得分": str(score_row[3] or '0'),
                    "技术措施": score_row[4] or ''
                })

            # 保存数据到缓存
            try:
                os.makedirs('temp', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"数据已保存到缓存: {cache_file}")
            except Exception as e:
                print(f"保存缓存失败: {str(e)}")

        # 使用word_template模块处理文档
        print("开始处理Word模板...")
        
        try:
            # 使用word_template模块处理文档
            output_file = process_template(data)
            
            # 处理国标情况，国标时process_template返回None
            if output_file is None:
                # 对于国标，使用绿色建筑设计自评估报告.docx模板
                standard = data[0].get('评价标准')
                print(f"检测到评价标准为{standard}，使用绿色建筑设计自评估报告模板")
                template_path = os.path.join(current_app.static_folder, 'templates', '绿色建筑设计自评估报告.docx')
                
                # 确保模板文件存在
                if not os.path.exists(template_path):
                    print(f"模板文件不存在: {template_path}")
                    return jsonify({"error": "模板文件不存在"}), 404
                
                try:
                    # 调用word_template模块的replace_placeholders函数处理占位符
                    output_file = replace_placeholders(template_path, data)
                    print(f"占位符替换完成，输出文件: {output_file}")
                except Exception as e:
                    print(f"处理占位符时出错: {str(e)}")
                    print(f"异常详情: {traceback.format_exc()}")
                    return jsonify({"error": f"处理占位符失败: {str(e)}"}), 500
            
            print(f"Word文档生成成功: {output_file}")
            
            # 检查生成的文件是否存在
            if not os.path.exists(output_file):
                print(f"生成的文件不存在: {output_file}")
                return jsonify({"error": "生成的文件不存在"}), 500
                
            # 获取文件名
            download_name = f"{data[0]['项目名称']}_绿色建筑设计自评估报告.docx"
            if not download_name:
                download_name = "self_assessment_report.docx"
            
            print(f"准备下载文件: {download_name}")
            return send_file(
                output_file,
                as_attachment=True,
                download_name=download_name,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        except Exception as e:
            print(f"处理Word模板失败: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            return jsonify({"error": f"处理Word模板失败: {str(e)}"}), 500

    except Exception as e:
        print(f"生成绿色建筑设计自评估报告失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"生成绿色建筑设计自评估报告失败: {str(e)}"}), 500
def generate_generateljzpwb(request_data):
    """
    生成绿建专篇文本的函数
    
    参数:
    - request_data: 包含project_id的字典
    
    返回:
    - tuple: (response, status_code)
    """
    try:
        # 从请求参数中获取项目ID
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "请提供项目ID"}), 400
            
        # 检查模板文件是否存在
        template_file = '绿建专篇文本.docx'
        template_path = os.path.join(current_app.static_folder, 'templates', template_file)
        
        if not os.path.exists(template_path):
            print(f"模板文件不存在: {template_path}")
            return jsonify({"error": f"模板文件不存在: {template_file}"}), 404

        # 尝试从缓存获取数据
        cache_file = os.path.join('temp', f'project_{project_id}_cache.json')
        data = None
        use_cache = request_data.get('use_cache', True)
        
        if use_cache and os.path.exists(cache_file):
            try:
                print(f"从缓存文件加载数据: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("成功从缓存加载数据")
                
                # 检查缓存数据是否有效
                if not data or len(data) < 1 or not isinstance(data[0], dict) or not data[0].get("项目名称"):
                    print("缓存数据无效，将从数据库重新获取")
                    data = None
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                data = None

        # 如果缓存不存在或无效，从数据库获取数据
        if not data:
            print("从数据库获取数据...")
            
            # 获取项目基本信息
            print(f"获取项目 {project_id} 的基本信息")
            result = db.session.execute(
                text("""
                    SELECT p.id, p.user_id, p.name, p.code, p.construction_unit, p.design_unit, p.location, 
                           p.building_area, p.standard, p.building_type, p.created_at, p.climate_zone, 
                           p.star_rating_target, p.total_land_area, p.total_building_area, p.above_ground_area, 
                           p.underground_area, p.building_height, p.building_floors, p.underground_floor_area, 
                           p.ground_parking_spaces, p.plot_ratio, p.building_base_area, p.building_density, 
                           p.green_area, p.green_ratio, p.residential_units, p.air_conditioning_type,
                           p.average_floors, p.has_garbage_room, p.has_elevator, p.has_underground_garage,
                           p.construction_type, p.has_water_landscape, p.is_fully_decorated, p.public_building_type,
                           p.public_green_space, p.architecture_score, p.structure_score, p.water_supply_score, 
                           p.electrical_score, p.hvac_score, p.landscape_score, p.env_health_energy_score,
                           p.env_health_energy_innovation_score, p.architecture_innovation_score, 
                           p.structure_innovation_score, p.hvac_innovation_score, p.landscape_innovation_score, 
                           p.safety_durability_score, p.health_comfort_score, p.life_convenience_score, 
                           p.resource_saving_score, p.environment_livability_score, p.improvement_innovation_score, 
                           p.total_score, p.evaluation_result
                    FROM projects p
                    WHERE p.id = :project_id
                """),
                {"project_id": project_id}
            )
            project_rows = result.fetchall()

            if not project_rows:
                print(f"未找到项目数据: ID={project_id}")
                return jsonify({"error": "未找到项目数据"}), 404

            print(f"获取到项目数据: {project_rows[0]}")

            # 准备数据
            data = []
            # 添加项目信息作为第一条数据
            data.append({
                "项目ID": str(project_rows[0][0] or ''),
                "用户ID": str(project_rows[0][1] or ''),
                "项目名称": project_rows[0][2] or '',
                "项目编号": project_rows[0][3] or '',
                "建设单位": project_rows[0][4] or '',
                "设计单位": project_rows[0][5] or '',
                "项目地点": project_rows[0][6] or '',
                "建筑面积": str(project_rows[0][7] or '0'),
                "评价标准": project_rows[0][8] or '成都市标',
                "建筑类型": project_rows[0][9] or '',
                "创建时间": project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else '',
                "气候区划": project_rows[0][11] or '',
                "星级目标": project_rows[0][12] or '',
                "总用地面积": str(project_rows[0][13] or '0'),
                "总建筑面积": str(project_rows[0][14] or '0'),
                "地上建筑面积": str(project_rows[0][15] or '0'),
                "地下建筑面积": str(project_rows[0][16] or '0'),
                "建筑高度": str(project_rows[0][17] or '0'),
                "建筑层数": project_rows[0][18] or '',
                "地下一层建筑面积": str(project_rows[0][19] or '0'),
                "地面停车位数量": str(project_rows[0][20] or '0'),
                "容积率": str(project_rows[0][21] or '0'),
                "建筑基底面积": str(project_rows[0][22] or '0'),
                "建筑密度": str(project_rows[0][23] or '0'),
                "绿地面积": str(project_rows[0][24] or '0'),
                "绿地率": str(project_rows[0][25] or '0'),
                "住宅户数": str(project_rows[0][26] or '0'),
                "空调类型": project_rows[0][27] or '',
                "平均层数": project_rows[0][28] or '',
                "有无垃圾用房": project_rows[0][29] or '',
                "有无电梯": project_rows[0][30] or '',
                "有无地下车库": project_rows[0][31] or '',
                "建设情况": project_rows[0][32] or '',
                "有无景观水体": project_rows[0][33] or '',
                "是否全装修": project_rows[0][34] or '',
                "公建类型": project_rows[0][35] or '',
                "绿地向公众开放": project_rows[0][36] or '',
                "建筑总分": str(project_rows[0][37] or '0'),
                "结构总分": str(project_rows[0][38] or '0'),
                "给排水总分": str(project_rows[0][39] or '0'),
                "电气总分": str(project_rows[0][40] or '0'),
                "暖通总分": str(project_rows[0][41] or '0'),
                "景观总分": str(project_rows[0][42] or '0'),
                "环境健康与节能总分": str(project_rows[0][43] or '0'),
                "环境健康与节能创新总分": str(project_rows[0][44] or '0'),
                "建筑创新总分": str(project_rows[0][45] or '0'),
                "结构创新总分": str(project_rows[0][46] or '0'),
                "暖通创新总分": str(project_rows[0][47] or '0'),
                "景观创新总分": str(project_rows[0][48] or '0'),
                "安全耐久总分": str(project_rows[0][49] or '0'),
                "健康舒适总分": str(project_rows[0][50] or '0'),
                "生活便利总分": str(project_rows[0][51] or '0'),
                "资源节约总分": str(project_rows[0][52] or '0'),
                "环境宜居总分": str(project_rows[0][53] or '0'),
                "提高与创新总分": str(project_rows[0][54] or '0'),
                "项目总分": str(project_rows[0][55] or '0'),
                "评定结果": project_rows[0][56] or ''
            })

            # 获取得分数据
            print(f"获取项目 {project_id} 的得分数据")
            result = db.session.execute(
                text("""
                    SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                    FROM 得分表 
                    WHERE 项目ID = :project_id
                    ORDER BY 条文号
                """),
                {"project_id": project_id}
            )
            score_rows = result.fetchall()
            
            print(f"获取到 {len(score_rows)} 条得分数据")

            # 添加得分数据
            for score_row in score_rows:
                data.append({
                    "条文号": score_row[0] or '',
                    "分类": score_row[1] or '',
                    "是否达标": score_row[2] or '',
                    "得分": str(score_row[3] or '0'),
                    "技术措施": score_row[4] or ''
                })

            # 保存数据到缓存
            try:
                os.makedirs('temp', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"数据已保存到缓存: {cache_file}")
            except Exception as e:
                print(f"保存缓存失败: {str(e)}")
        # 使用word_template模块处理文档
        print("开始处理Word模板...")

        try:
            template_path = os.path.join(current_app.static_folder, 'templates', '绿建专篇文本.docx')
            # 调用word_template模块的replace_placeholders_format函数处理占位符
            output_file = replace_placeholders(template_path, data)
            print(f"占位符替换完成，输出文件: {output_file}")
        except Exception as e:
            print(f"处理占位符时出错: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            return jsonify({"error": f"处理占位符失败: {str(e)}"}), 500
            
        print(f"Word文档生成成功: {output_file}")
        
        # 检查生成的文件是否存在
        if not os.path.exists(output_file):
            print(f"生成的文件不存在: {output_file}")
            return jsonify({"error": "生成的文件不存在"}), 500
            
        # 获取文件名
        download_name = f"{data[0]['项目名称']}_绿建专篇文本.docx"
        if not download_name:
            download_name = "generateljzpwb.docx"
        
        print(f"准备下载文件: {download_name}")
        return send_file(
            output_file,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        print(f"生成绿建专篇文本失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"生成绿建专篇文本失败: {str(e)}"}), 500

def generate_dwg(request_data):
    """
    生成绿色建筑设计专篇DWG文件
    """
    try:
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "未提供项目ID"}), 400

        # 获取项目信息和评分数据
        result = db.session.execute(
            text("""
                SELECT 
                    p.id,
                    p.user_id,
                    p.name,
                    p.code,
                    p.construction_unit,
                    p.design_unit,
                    p.location,
                    p.building_area,
                    p.standard,
                    p.building_type,
                    p.created_at,
                    p.climate_zone,
                    p.star_rating_target,
                    p.total_land_area,
                    p.total_building_area,
                    p.above_ground_area,
                    p.underground_area,
                    p.building_height,
                    p.building_floors,
                    p.underground_floor_area,
                    p.ground_parking_spaces,
                    p.plot_ratio,
                    p.building_base_area,
                    p.building_density,
                    p.green_area,
                    p.green_ratio,
                    p.residential_units,
                    p.air_conditioning_type,
                    p.average_floors,
                    p.has_garbage_room,
                    p.has_elevator,
                    p.has_underground_garage,
                    p.construction_type,
                    p.has_water_landscape,
                    p.is_fully_decorated,
                    p.public_building_type,
                    p.public_green_space,
                    p.architecture_score,
                    p.structure_score,
                    p.water_supply_score,
                    p.electrical_score,
                    p.hvac_score,
                    p.landscape_score,
                    p.env_health_energy_score,
                    p.env_health_energy_innovation_score,
                    p.architecture_innovation_score,
                    p.structure_innovation_score,
                    p.hvac_innovation_score,
                    p.landscape_innovation_score,
                    p.safety_durability_score,
                    p.health_comfort_score,
                    p.life_convenience_score,
                    p.resource_saving_score,
                    p.environment_livability_score,
                    p.improvement_innovation_score,
                    p.total_score,
                    p.evaluation_result
                FROM projects p
                WHERE p.id = :project_id
            """),
            {"project_id": project_id}
        )
        project_rows = result.fetchall()

        if not project_rows:
            print(f"未找到项目数据: ID={project_id}")
            return jsonify({"error": "未找到项目数据"}), 404

        print(f"获取到项目数据: {project_rows[0]}")
        
        standard = project_rows[0][8]  # 使用数据库中的评价标准
        star_rating_target = project_rows[0][12] or ''  # 星级目标
        
        print(f"项目评价标准: {standard}, 星级目标: {star_rating_target}")
        
        # 根据评价标准和星级目标选择模板文件
        template_filename = ""
        if standard == '成都市标':
            template_filename = '绿色建筑设计专篇(市标2024).dwg'
        elif standard == '四川省标':
            if star_rating_target == '基本级':
                template_filename = '绿色建筑设计专篇(省标基本级2024).dwg'
            else:
                template_filename = '绿色建筑设计专篇(省标2024).dwg'
        elif standard == '国标':
            # 检查是否为内蒙古地区且非基本级
            location = project_rows[0][6] or ''  # 获取项目地点
            if '内蒙古' in location and star_rating_target != '基本级':
                template_filename = '绿色建筑设计专篇-内蒙古.dwg'
            elif star_rating_target == '基本级':
                template_filename = '绿色建筑设计专篇(国标基本级2024).dwg'
            else:
                template_filename = '绿色建筑设计专篇(国标2024).dwg'
        else:
            # 默认使用成都市标模板
            template_filename = '绿色建筑设计专篇(市标2024).dwg'
        
        # 检查模板文件是否存在
        template_path = os.path.join(current_app.static_folder, 'templates', template_filename)
        print(f"CAD模板文件路径: {template_path}")
        if not os.path.exists(template_path):
            print(f"CAD模板文件不存在: {template_path}")
            return jsonify({"error": f"CAD模板文件不存在，请确保templates目录下有{template_filename}文件"}), 404

        # 同步得分表和project_scores表的数据
        print(f"同步项目 {project_id} 的得分表和project_scores表数据")
        try:
            # 检查得分表中是否有该项目的数据
            result = db.session.execute(
                text("SELECT COUNT(*) FROM 得分表 WHERE 项目ID = :project_id"),
                {"project_id": project_id}
            )
            score_count = result.scalar()
            print(f"得分表中项目ID={project_id}的记录有 {score_count} 条")
            
            # 清空project_scores表中该项目的数据
            result = db.session.execute(
                text("DELETE FROM project_scores WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            deleted_count = result.rowcount
            print(f"从project_scores表中删除项目ID={project_id}的 {deleted_count} 条记录")
            
            # 从得分表导入数据到project_scores表
            result = db.session.execute(
                text("""
                    SELECT 项目ID, 评价等级, 专业, 条文号, 分类, 是否达标, 得分, 技术措施
                    FROM 得分表
                    WHERE 项目ID = :project_id
                """),
                {"project_id": project_id}
            )
            scores = result.fetchall()
            
            # 导入数据到project_scores表
            imported_count = 0
            for score in scores:
                project_id, level, specialty, clause_number, category, is_achieved, score_value, technical_measures = score
                
                # 尝试将得分转换为浮点数
                try:
                    if score_value and score_value.strip():
                        score_float = float(score_value)
                    else:
                        score_float = 0
                except (ValueError, TypeError):
                    score_float = 0
                
                # 插入数据
                db.session.execute(
                    text("""
                        INSERT INTO project_scores (project_id, level, specialty, clause_number, category, is_achieved, score, technical_measures)
                        VALUES (:project_id, :level, :specialty, :clause_number, :category, :is_achieved, :score_float, :technical_measures)
                    """),
                    {
                        "project_id": project_id,
                        "level": level,
                        "specialty": specialty,
                        "clause_number": clause_number,
                        "category": category,
                        "is_achieved": is_achieved,
                        "score_float": score_float,
                        "technical_measures": technical_measures
                    }
                )
                imported_count += 1
            
            # 提交事务
            db.session.commit()
            print(f"成功从得分表导入 {imported_count} 条记录到project_scores表")
        except Exception as e:
            print(f"同步得分表和project_scores表数据时出错: {str(e)}")
            print(traceback.format_exc())
            # 继续执行，不影响后续操作

        # 尝试从缓存获取数据
        cache_file = os.path.join('temp', f'project_{project_id}_cache.json')
        data = None
        use_cache = request_data.get('use_cache', False)  # 默认不使用缓存
        
        if use_cache and os.path.exists(cache_file):
            try:
                print(f"从缓存文件加载数据: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("成功从缓存加载数据")
                
                # 检查缓存数据是否有效
                if not data or len(data) < 1 or not isinstance(data[0], dict) or not data[0].get("项目名称"):
                    print("缓存数据无效，将从数据库重新获取")
                    data = None
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                data = None

        # 如果缓存不存在或无效，从数据库获取数据
        if not data:
            # 获取得分数据
            print(f"获取项目 {project_id} 的得分数据")
            result = db.session.execute(
                text("""
                    SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                    FROM 得分表 
                    WHERE 项目ID = :project_id
                    ORDER BY 条文号
                """),
                {"project_id": project_id}
            )
            score_rows = result.fetchall()
            
            print(f"获取到 {len(score_rows)} 条得分数据")

            # 准备数据
            data = []
            # 添加项目信息作为第一条数据
            data.append({
                "项目ID": str(project_rows[0][0] or ''),
                "用户ID": str(project_rows[0][1] or ''),
                "项目名称": project_rows[0][2] or '',
                "项目编号": project_rows[0][3] or '',
                "建设单位": project_rows[0][4] or '',
                "设计单位": project_rows[0][5] or '',
                "项目地点": project_rows[0][6] or '',
                "建筑面积": str(project_rows[0][7] or '0'),
                "评价标准": project_rows[0][8] or '成都市标',
                "建筑类型": project_rows[0][9] or '',
                "创建时间": project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else '',
                "气候区划": project_rows[0][11] or '',
                "星级目标": project_rows[0][12] or '',
                "总用地面积": str(project_rows[0][13] or '0'),
                "总建筑面积": str(project_rows[0][14] or '0'),
                "地上建筑面积": str(project_rows[0][15] or '0'),
                "地下建筑面积": str(project_rows[0][16] or '0'),
                "建筑高度": str(project_rows[0][17] or '0'),
                "建筑层数": project_rows[0][18] or '',
                "地下一层建筑面积": str(project_rows[0][19] or '0'),
                "地面停车位数量": str(project_rows[0][20] or '0'),
                "容积率": str(project_rows[0][21] or '0'),
                "建筑基底面积": str(project_rows[0][22] or '0'),
                "建筑密度": str(project_rows[0][23] or '0'),
                "绿地面积": str(project_rows[0][24] or '0'),
                "绿地率": str(project_rows[0][25] or '0'),
                "住宅户数": str(project_rows[0][26] or '0'),
                "空调类型": project_rows[0][27] or '',
                "平均层数": project_rows[0][28] or '',
                "有无垃圾用房": project_rows[0][29] or '',
                "有无电梯": project_rows[0][30] or '',
                "有无地下车库": project_rows[0][31] or '',
                "建设情况": project_rows[0][32] or '',
                "有无景观水体": project_rows[0][33] or '',
                "是否全装修": project_rows[0][34] or '',
                "公建类型": project_rows[0][35] or '',
                "绿地向公众开放": project_rows[0][36] or '',
                "建筑总分": str(project_rows[0][37] or '0'),
                "结构总分": str(project_rows[0][38] or '0'),
                "给排水总分": str(project_rows[0][39] or '0'),
                "电气总分": str(project_rows[0][40] or '0'),
                "暖通总分": str(project_rows[0][41] or '0'),
                "景观总分": str(project_rows[0][42] or '0'),
                "环境健康与节能总分": str(project_rows[0][43] or '0'),
                "环境健康与节能创新总分": str(project_rows[0][44] or '0'),
                "建筑创新总分": str(project_rows[0][45] or '0'),
                "结构创新总分": str(project_rows[0][46] or '0'),
                "暖通创新总分": str(project_rows[0][47] or '0'),
                "景观创新总分": str(project_rows[0][48] or '0'),
                "安全耐久总分": str(project_rows[0][49] or '0'),
                "健康舒适总分": str(project_rows[0][50] or '0'),
                "生活便利总分": str(project_rows[0][51] or '0'),
                "资源节约总分": str(project_rows[0][52] or '0'),
                "环境宜居总分": str(project_rows[0][53] or '0'),
                "提高与创新总分": str(project_rows[0][54] or '0'),
                "项目总分": str(project_rows[0][55] or '0'),
                "评定结果": project_rows[0][56] or ''
            })

            # 添加得分数据
            for score_row in score_rows:
                data.append({
                    "条文号": score_row[0] or '',
                    "分类": score_row[1] or '',
                    "是否达标": score_row[2] or '',
                    "得分": str(score_row[3] or '0'),
                    "技术措施": score_row[4] or ''
                })

            # 保存数据到缓存
            try:
                os.makedirs('temp', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"数据已保存到缓存: {cache_file}")
            except Exception as e:
                print(f"保存缓存失败: {str(e)}")

        # 准备属性块数据
        attributes = {}
        
        # 添加项目所有信息
        attributes["项目ID"] = str(project_rows[0][0] or '')
        attributes["用户ID"] = str(project_rows[0][1] or '')
        attributes["项目名称"] = project_rows[0][2] or ''
        attributes["项目编号"] = project_rows[0][3] or ''
        attributes["建设单位"] = project_rows[0][4] or ''
        attributes["设计单位"] = project_rows[0][5] or ''
        attributes["项目地点"] = project_rows[0][6] or ''
        attributes["建筑面积"] = str(project_rows[0][7] or '0')
        attributes["评价标准"] = project_rows[0][8] or '成都市标'
        attributes["建筑类型"] = project_rows[0][9] or ''
        attributes["创建时间"] = project_rows[0][10].strftime('%Y-%m-%d %H:%M:%S') if project_rows[0][10] else ''
        attributes["气候区划"] = project_rows[0][11] or ''
        attributes["星级目标"] = project_rows[0][12] or ''
        attributes["总用地面积"] = str(project_rows[0][13] or '0')
        attributes["总建筑面积"] = str(project_rows[0][14] or '0')
        attributes["地上建筑面积"] = str(project_rows[0][15] or '0')
        attributes["地下建筑面积"] = str(project_rows[0][16] or '0')
        attributes["建筑高度"] = str(project_rows[0][17] or '0')
        attributes["建筑层数"] = project_rows[0][18] or ''
        attributes["地下一层建筑面积"] = str(project_rows[0][19] or '0')
        attributes["地面停车位数量"] = str(project_rows[0][20] or '0')
        attributes["容积率"] = str(project_rows[0][21] or '0')
        attributes["建筑基底面积"] = str(project_rows[0][22] or '0')
        attributes["建筑密度"] = str(project_rows[0][23] or '0')
        attributes["绿地面积"] = str(project_rows[0][24] or '0')
        attributes["绿地率"] = str(project_rows[0][25] or '0')
        attributes["住宅户数"] = str(project_rows[0][26] or '0')
        attributes["空调类型"] = project_rows[0][27] or ''
        attributes["平均层数"] = project_rows[0][28] or ''
        attributes["有无垃圾用房"] = project_rows[0][29] or ''
        attributes["有无电梯"] = project_rows[0][30] or ''
        attributes["有无地下车库"] = project_rows[0][31] or ''
        attributes["建设情况"] = project_rows[0][32] or ''
        attributes["有无景观水体"] = project_rows[0][33] or ''
        attributes["是否全装修"] = project_rows[0][34] or ''
        attributes["公建类型"] = project_rows[0][35] or ''
        attributes["绿地向公众开放"] = project_rows[0][36] or ''
        attributes["设计日期"] = datetime.now().strftime('%Y年%m月%d日')
        # 添加评分数据

        attributes["建筑总分"] = str(project_rows[0][37] or '0')
        attributes["结构总分"] = str(project_rows[0][38] or '0')
        attributes["给排水总分"] = str(project_rows[0][39] or '0')
        attributes["电气总分"] = str(project_rows[0][40] or '0')
        attributes["暖通总分"] = str(project_rows[0][41] or '0')
        attributes["景观总分"] = str(project_rows[0][42] or '0')
        attributes["环境健康与节能总分"] = str(project_rows[0][43] or '0')
        attributes["环境健康与节能创新总分"] = str(project_rows[0][44] or '0')
        attributes["建筑创新总分"] = str(project_rows[0][45] or '0')
        attributes["结构创新总分"] = str(project_rows[0][46] or '0')
        attributes["暖通创新总分"] = str(project_rows[0][47] or '0')
        attributes["景观创新总分"] = str(project_rows[0][48] or '0')
        attributes["安全耐久总分"] = str(project_rows[0][49] or '0')
        attributes["健康舒适总分"] = str(project_rows[0][50] or '0')
        attributes["生活便利总分"] = str(project_rows[0][51] or '0')
        attributes["资源节约总分"] = str(project_rows[0][52] or '0')
        attributes["环境宜居总分"] = str(project_rows[0][53] or '0')
        attributes["提高与创新总分"] = str(project_rows[0][54] or '0')
        attributes["项目总分"] = str(project_rows[0][55] or '0')
        attributes["评定结果"] = project_rows[0][56] or ''
        
        # 添加得分数据
        for item in data[1:]:  # 跳过第一项（项目信息）
            条文号 = item.get("条文号", "")
            得分 = item.get("得分", "")
            技术措施 = item.get("技术措施", "")
            是否达标 = item.get("是否达标", "")
            分类 = item.get("分类", "")
            
            if 条文号:
                # 添加条文号对应的所有信息
                attributes[条文号] = str(得分)
                attributes[f"{条文号}措施"] = 技术措施 if 技术措施 is not None else ""
                attributes[f"{条文号}达标"] = 是否达标 if 是否达标 is not None else ""
                attributes[f"{条文号}分类"] = 分类 if 分类 is not None else ""
                
        # 确保所有可能的条文号措施字段都存在，即使没有数据
        # 通过查找所有键中包含"措施"的，如果没有找到对应的条文号，则创建一个为空的
        all_keys = list(attributes.keys())
        for key in all_keys:
            if "措施" in key:
                clause_num = key.replace("措施", "")
                # 确保条文号存在
                if clause_num not in attributes:
                    attributes[clause_num] = ""
                # 确保其他相关字段也存在
                if f"{clause_num}达标" not in attributes:
                    attributes[f"{clause_num}达标"] = ""
                if f"{clause_num}分类" not in attributes:
                    attributes[f"{clause_num}分类"] = ""
        
        # 生成输出文件路径

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = current_app.config.get('EXPORT_FOLDER', 'static/exports')
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取文件名
        standard_short = {
            '成都市标': '市标',
            '四川省标': '省标',
            '国标': '国标'
        }.get(standard, '市标')
        
        project_name = data[0]['项目名称'] if data and len(data) > 0 and '项目名称' in data[0] else 'unknown'
        download_name = f"{project_name}_绿色建筑设计专篇.dwg"
        if not download_name:
            download_name = "green_building.dwg"
        
        # 临时文件路径
        temp_dir = 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, f"绿建设计专篇_{project_name}_{timestamp}.dwg")
        
        # 根据环境选择处理方式
        if IS_WINDOWS and update_attribute_text:
            print("使用Windows本地AutoCAD处理DWG文件")
            try:
                print(f"使用本地函数更新CAD文件，使用模板: {template_path}...")
                print(f"更新的属性数量: {len(attributes)}")
                
                # 调用update_attribute_text函数
                update_attribute_text(template_path, output_path, attributes)
                
                # 检查文件是否存在
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"文件已成功生成: {output_path}, 大小: {file_size} 字节")
                    
                    print(f"准备下载CAD文件: {download_name}")
                    try:
                        # 直接发送文件给用户下载
                        return send_file(
                            output_path,
                            as_attachment=True,
                            download_name=download_name,
                            mimetype='application/acad'
                        )
                    except Exception as send_error:
                        print(f"直接发送文件失败: {str(send_error)}")
                        print(traceback.format_exc())
                        
                        # 发送失败时回退到旧方式 - 通过保存到static/exports目录
                        target_path = os.path.join(output_dir, f"绿建设计专篇_{project_name}_{timestamp}.dwg")
                        import shutil
                        shutil.copy2(output_path, target_path)
                        
                        # 构建文件URL
                        file_url = f'/static/exports/绿建设计专篇_{project_name}_{timestamp}.dwg'
                        
                        print(f"使用备用方式发送文件，URL: {file_url}")
                        
                        # 返回文件URL以兼容旧的前端逻辑
                        return jsonify({
                            'success': True,
                            'file_url': file_url,
                            'message': '绿色建筑设计专篇生成成功(使用URL方式)'
                        })
                else:
                    print(f"文件生成失败: {output_path}")
                    return jsonify({"error": "文件生成失败"}), 500
            except Exception as e:
                print(f"本地处理DWG文件失败: {str(e)}")
                print(traceback.format_exc())
                return jsonify({"error": f"生成失败: {str(e)}"}), 500
        elif IS_WSL and dwg_client:
            print("使用WSL环境下的DWG远程服务处理DWG文件")
            # 将字典转换为列表格式，以适应DWG服务的API
            attribute_list = []
            for key, value in attributes.items():
                attribute_list.append({
                    'field': key,
                    'value': value
                })
            
            # 调用DWG服务客户端
            print(f"开始更新CAD文件，使用模板: {template_filename}...")
            print(f"更新的属性数量: {len(attributes)}")
            success, result = dwg_client.update_dwg_attributes(template_path, attribute_list)
            
            if success:
                try:
                    # 检查result中是否包含file_data
                    if 'file_data' not in result:
                        print(f"DWG服务返回的结果中缺少file_data字段: {result}")
                        return jsonify({"error": "DWG服务未返回文件数据"}), 500
                    
                    # 检查file_data是否为空
                    file_data = result['file_data']
                    if not file_data or len(file_data) == 0:
                        print("DWG服务返回的文件数据为空")
                        return jsonify({"error": "DWG服务返回的文件数据为空"}), 500
                    
                    print(f"收到DWG服务返回的文件数据，大小: {len(file_data)} 字节")
                    
                    try:
                        # 保存到临时文件
                        with open(output_path, 'wb') as f:
                            f.write(file_data)
                        
                        file_size = os.path.getsize(output_path)
                        print(f"文件已成功保存到: {output_path}, 大小: {file_size} 字节")
                        
                        print(f"准备下载CAD文件: {download_name}")
                        try:
                            # 直接发送文件给用户下载
                            return send_file(
                                output_path,
                                as_attachment=True,
                                download_name=download_name,
                                mimetype='application/acad'
                            )
                        except Exception as send_error:
                            print(f"直接发送文件失败: {str(send_error)}")
                            print(traceback.format_exc())
                            
                            # 发送失败时回退到旧方式 - 通过保存到static/exports目录
                            target_path = os.path.join(output_dir, f"绿建设计专篇_{project_name}_{timestamp}.dwg")
                            import shutil
                            shutil.copy2(output_path, target_path)
                            
                            # 构建文件URL
                            file_url = f'/static/exports/绿建设计专篇_{project_name}_{timestamp}.dwg'
                            
                            print(f"使用备用方式发送文件，URL: {file_url}")
                            
                            # 返回文件URL以兼容旧的前端逻辑
                            return jsonify({
                                'success': True,
                                'file_url': file_url,
                                'message': '绿色建筑设计专篇生成成功(使用URL方式)'
                            })
                    except Exception as file_write_error:
                        print(f"写入文件时出错: {str(file_write_error)}")
                        print(traceback.format_exc())
                        return jsonify({"error": f"写入文件时出错: {str(file_write_error)}"}), 500
                except Exception as e:
                    print(f"处理DWG服务返回数据时出错: {str(e)}")
                    print(traceback.format_exc())
                    return jsonify({"error": f"处理DWG服务返回数据时出错: {str(e)}"}), 500
            else:
                error_message = result.get('message', '未知错误')
                print(f"DWG服务返回错误: {error_message}")
                return jsonify({"error": f"生成失败: {error_message}"}), 500
        else:
            # 环境不支持处理DWG
            return jsonify({
                "error": "当前环境不支持DWG处理。Windows需要安装pywin32，WSL需要配置dwg_client。"
            }), 500

    except Exception as e:
        print(f"生成CAD文件失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"生成失败: {str(e)}"}), 500
