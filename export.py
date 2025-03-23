import os
import pyodbc
from flask import jsonify, current_app, send_file, request
from dotenv import load_dotenv
from docx import Document
from word_template import process_template
import json
import traceback
from update_dwg_attribute import update_attribute_text
# 加载环境变量
load_dotenv()


# 数据库连接配置
def get_db_connection():
    try:
        # 获取数据库配置参数
        server = os.getenv('SQLSERVER_SERVER')
        database = os.getenv('SQLSERVER_DATABASE')
        username = os.getenv('SQLSERVER_USERNAME')
        password = os.getenv('SQLSERVER_PASSWORD')
        driver = os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')

        # 检查必要的配置参数
        if not all([server, database, username, password]):
            current_app.logger.error("缺少必要的数据库配置参数")
            raise ValueError("缺少必要的数据库配置参数")

        # 构建连接字符串
        conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

        # 尝试建立连接
        try:
            conn = pyodbc.connect(conn_str)
            current_app.logger.info("数据库连接成功")
            return conn
        except pyodbc.Error as e:
            current_app.logger.error(f"数据库连接失败: {str(e)}")
            raise
    except Exception as e:
        current_app.logger.error(f"创建数据库连接时出错: {str(e)}")
        raise

def generate_word(request_data):
    """
    生成Word文档的函数
    
    参数:
    - request_data: 包含project_id的字典
    
    返回:
    - tuple: (response, status_code)
    """
    cursor = None
    conn = None
    try:
        # 从请求参数中获取项目ID
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "请提供项目ID"}), 400

        # 检查模板文件是否存在
        template_path = os.path.join(current_app.static_folder, 'templates', 'chengdu_template.docx')
        if not os.path.exists(template_path):
            print(f"模板文件不存在: {template_path}")
            return jsonify({"error": "模板文件不存在"}), 404

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
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 获取项目基本信息
            print(f"获取项目 {project_id} 的基本信息")
            cursor.execute("""
                SELECT p.name, p.design_unit, p.construction_unit, p.total_building_area,
                       p.building_type, p.location, p.climate_zone, p.star_rating_target,
                       p.architecture_score, p.structure_score, p.water_supply_score, 
                       p.electrical_score, p.hvac_score, p.landscape_score,
                       p.architecture_innovation_score, p.structure_innovation_score, 
                       p.hvac_innovation_score, p.landscape_innovation_score,
                       p.improvement_innovation_score, p.total_score,
                       p.safety_durability_score, p.health_comfort_score,
                       p.life_convenience_score, p.resource_saving_score,
                       p.environment_livability_score, p.total_land_area, p.standard,
                       p.building_height, p.building_floors, p.env_health_energy_score,
                       p.env_health_energy_innovation_score, p.evaluation_result
                FROM projects p
                WHERE p.id = ?
            """, [project_id])
            project_rows = cursor.fetchall()

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
            
            # 打印数据对象，用于调试
            print("数据对象内容:")
            print("数据对象中的所有字段名:")
            for key in data[0].keys():
                print(f"  {key}")
            print("数据对象中的所有字段值:")
            for key, value in data[0].items():
                print(f"  {key}: {value}")
            print("数据对象中的总建筑面积字段值:", data[0].get("总建筑面积", "未找到"))
            print("数据对象中的建筑面积字段值:", data[0].get("建筑面积", "未找到"))

            # 获取得分数据
            print(f"获取项目 {project_id} 的得分数据")
            cursor.execute("""
                SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                FROM 得分表 
                WHERE 项目ID = ?
                ORDER BY 条文号
            """, [project_id])
            score_rows = cursor.fetchall()
            
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
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("数据库连接已关闭")

def save_project_info(project_data):
    """
    保存项目信息到本地缓存和数据库
    
    参数:
    - project_data: 包含项目信息的字典
    
    返回:
    - tuple: (response, status_code)
    """
    cursor = None
    conn = None
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

        # 保存到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新项目信息
        cursor.execute("""
            UPDATE projects 
            SET name = ?, 
                design_unit = ?,
                construction_unit = ?,
                total_building_area = ?,
                building_type = ?,
                location = ?,
                climate_zone = ?,
                star_rating_target = ?
            WHERE id = ?
        """, [
            project_data.get('project_name', ''),
            project_data.get('design_unit', ''),
            project_data.get('construction_unit', ''),
            project_data.get('total_building_area', ''),
            project_data.get('building_type', ''),
            project_data.get('location', ''),
            project_data.get('climate_zone', ''),
            project_data.get('star_rating_target', ''),
            project_id
        ])
        
        conn.commit()
        print("项目信息已保存到数据库")
        
        # 创建新的缓存
        try:
            # 获取最新的项目信息
            cursor.execute("""
                SELECT name, design_unit, construction_unit, total_building_area
                FROM projects 
                WHERE id = ?
            """, [project_id])
            project_rows = cursor.fetchall()
            
            if project_rows:
                # 获取得分数据
                cursor.execute("""
                    SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                    FROM 得分表 
                    WHERE 项目ID = ?
                    ORDER BY 条文号
                """, [project_id])
                score_rows = cursor.fetchall()
                
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
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("数据库连接已关闭")

def generate_dwg(request_data):
    """
    生成绿色建筑设计专篇DWG文件
    """
    cursor = None
    conn = None
    try:
        project_id = request_data.get('project_id')
        if not project_id:
            print("未提供项目ID")
            return jsonify({"error": "未提供项目ID"}), 400

        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取项目信息和评分数据
        query = """
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
            WHERE p.id = ?
        """
        
        cursor.execute(query, (project_id,))
        project_rows = cursor.fetchall()

        if not project_rows:
            print(f"未找到项目数据: ID={project_id}")
            return jsonify({"error": "未找到项目数据"}), 404

        print(f"获取到项目数据: {project_rows[0]}")
        
        standard = project_rows[0][8]  # 使用数据库中的评价标准
        star_rating_target = project_rows[0][7] or ''  # 星级目标
        
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
            if star_rating_target == '基本级':
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
            cursor.execute("SELECT COUNT(*) FROM [得分表] WHERE [项目ID] = ?", (project_id,))
            score_count = cursor.fetchone()[0]
            print(f"得分表中项目ID={project_id}的记录有 {score_count} 条")
            
            # 清空project_scores表中该项目的数据
            cursor.execute("DELETE FROM project_scores WHERE project_id = ?", (project_id,))
            deleted_count = cursor.rowcount
            print(f"从project_scores表中删除项目ID={project_id}的 {deleted_count} 条记录")
            
            # 从得分表导入数据到project_scores表
            cursor.execute("""
                SELECT [项目ID], [评价等级], [专业], [条文号], [分类], [是否达标], [得分], [技术措施]
                FROM [得分表]
                WHERE [项目ID] = ?
            """, (project_id,))
            scores = cursor.fetchall()
            
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
                cursor.execute("""
                    INSERT INTO project_scores (project_id, level, specialty, clause_number, category, is_achieved, score, technical_measures)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (project_id, level, specialty, clause_number, category, is_achieved, score_float, technical_measures))
                imported_count += 1
            
            # 提交事务
            conn.commit()
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
            cursor.execute("""
                SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
                FROM 得分表 
                WHERE 项目ID = ?
                ORDER BY 条文号
            """, [project_id])
            score_rows = cursor.fetchall()
            
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
                attributes[f"{条文号}措施"] = 技术措施
                attributes[f"{条文号}达标"] = 是否达标
                attributes[f"{条文号}分类"] = 分类
        
        # 生成输出文件路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join('temp', f'green_building_{timestamp}.dwg')
        
        # 调用update_attribute_text更新DWG文件
        print(f"开始更新CAD文件，使用模板: {template_filename}...")
        print(f"更新的属性数量: {len(attributes)}")
        update_attribute_text(template_path, output_path, attributes)
        
        # 检查生成的文件是否存在
        if not os.path.exists(output_path):
            print(f"生成的CAD文件不存在: {output_path}")
            return jsonify({"error": "生成的CAD文件不存在"}), 500
            
        # 获取文件名
        standard_short = {
            '成都市标': '市标',
            '四川省标': '省标',
            '国标': '国标'
        }.get(standard, '市标')
        
        download_name = f"{data[0]['项目名称']}_{standard_short}_{star_rating_target}_绿色建筑设计专篇.dwg"
        if not download_name:
            download_name = "green_building.dwg"
        
        print(f"准备下载CAD文件: {download_name}")
        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/acad'
        )
    except Exception as e:
        print(f"生成CAD文件失败: {str(e)}")
        print(f"异常详情: {traceback.format_exc()}")
        return jsonify({"error": f"生成CAD文件失败: {str(e)}"}), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("数据库连接已关闭")
