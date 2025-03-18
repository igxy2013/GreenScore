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
        database = os.getenv('DATABASE')
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        driver = os.getenv('DRIVER', 'ODBC Driver 17 for SQL Server')

        # 检查必要的配置参数
        if not all([server, database, username, password]):
            current_app.logger.error("缺少必要的数据库配置参数")
            raise ValueError("缺少必要的数据库配置参数")

        # 构建连接字符串
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

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
        template_path = os.path.join(current_app.static_folder, 'templates', 'chengdu_template1.docx')
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
                SELECT name, design_unit, construction_unit, total_building_area
                FROM projects 
                WHERE id = ?
            """, [project_id])
            project_rows = cursor.fetchall()

            if not project_rows:
                print(f"未找到项目数据: ID={project_id}")
                return jsonify({"error": "未找到项目数据"}), 404

            print(f"获取到项目数据: {project_rows[0]}")

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
                "项目名称": project_rows[0][0] or '',
                "设计单位": project_rows[0][1] or '',
                "建设单位": project_rows[0][2] or '',
                "建筑面积": str(project_rows[0][3] or '')
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
                    "项目名称": project_rows[0][0] or '',
                    "设计单位": project_rows[0][1] or '',
                    "建设单位": project_rows[0][2] or '',
                    "建筑面积": str(project_rows[0][3] or '')
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
    生成DWG文档的函数
    
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

        # 获取数据库连接
        print("从数据库获取数据...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取项目基本信息
        print(f"获取项目 {project_id} 的基本信息")
        cursor.execute("""
            SELECT name, design_unit, construction_unit, total_building_area, 
                   building_type, location, climate_zone, star_rating_target, standard,
                   total_land_area, green_area, green_ratio, plot_ratio, building_density,
                   building_floors, building_height, above_ground_area, underground_area,
                   architecture_score, structure_score, water_supply_score, 
                   electrical_score, hvac_score, landscape_score,
                   architecture_innovation_score, structure_innovation_score, 
                   hvac_innovation_score, landscape_innovation_score,
                   safety_durability_score, health_comfort_score, 
                   life_convenience_score, resource_saving_score, 
                   environment_livability_score, improvement_innovation_score,
                   total_score, evaluation_result
            FROM projects 
            WHERE id = ?
        """, [project_id])
        project_rows = cursor.fetchall()

        if not project_rows:
            print(f"未找到项目数据: ID={project_id}")
            return jsonify({"error": "未找到项目数据"}), 404

        print(f"获取到项目数据: {project_rows[0]}")
        
        # 获取项目的评价标准和星级目标
        standard = project_rows[0][8] or '成都市标'  # 默认为成都市标
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
                "项目名称": project_rows[0][0] or '',
                "设计单位": project_rows[0][1] or '',
                "建设单位": project_rows[0][2] or '',
                "建筑面积": str(project_rows[0][3] or ''),
                "建筑类型": project_rows[0][4] or '',
                "项目地点": project_rows[0][5] or '',
                "气候区划": project_rows[0][6] or '',
                "星级目标": star_rating_target
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
        
        # 添加项目基本信息
        if data and len(data) > 0:
            project_info = data[0]
            for key, value in project_info.items():
                attributes[key] = str(value)
        
        # 添加项目详细信息（使用中文标签名）
        attributes["项目名称"] = project_rows[0][0] or ''
        attributes["设计单位"] = project_rows[0][1] or ''
        attributes["建设单位"] = project_rows[0][2] or ''
        attributes["总建筑面积"] = str(project_rows[0][3] or '')
        attributes["建筑类型"] = project_rows[0][4] or ''
        attributes["项目地点"] = project_rows[0][5] or ''
        attributes["气候区划"] = project_rows[0][6] or ''
        attributes["星级目标"] = project_rows[0][7] or ''
        attributes["评价标准"] = project_rows[0][8] or ''
        attributes["总用地面积"] = str(project_rows[0][9] or '')
        attributes["绿化面积"] = str(project_rows[0][10] or '')
        attributes["绿地率"] = str(project_rows[0][11] or '')
        attributes["容积率"] = str(project_rows[0][12] or '')
        attributes["建筑密度"] = str(project_rows[0][13] or '')
        attributes["建筑层数"] = str(project_rows[0][14] or '')
        attributes["建筑高度"] = str(project_rows[0][15] or '')
        attributes["地上建筑面积"] = str(project_rows[0][16] or '')
        attributes["地下建筑面积"] = str(project_rows[0][17] or '')
        
        # 添加评分数据（使用中文标签名）
        attributes["建筑总分"] = str(project_rows[0][18] or '0')
        attributes["结构总分"] = str(project_rows[0][19] or '0')
        attributes["给排水总分"] = str(project_rows[0][20] or '0')
        attributes["电气总分"] = str(project_rows[0][21] or '0')
        attributes["暖通总分"] = str(project_rows[0][22] or '0')
        attributes["景观总分"] = str(project_rows[0][23] or '0')
        attributes["建筑创新总分"] = str(project_rows[0][24] or '0')
        attributes["结构创新总分"] = str(project_rows[0][25] or '0')
        attributes["暖通创新总分"] = str(project_rows[0][26] or '0')
        attributes["景观创新总分"] = str(project_rows[0][27] or '0')
        attributes["安全耐久总分"] = str(project_rows[0][28] or '0')
        attributes["健康舒适总分"] = str(project_rows[0][29] or '0')
        attributes["生活便利总分"] = str(project_rows[0][30] or '0')
        attributes["资源节约总分"] = str(project_rows[0][31] or '0')
        attributes["环境宜居总分"] = str(project_rows[0][32] or '0')
        attributes["提高与创新总分"] = str(project_rows[0][33] or '0')
        attributes["项目总分"] = str(project_rows[0][34] or '0')
        attributes["评定结果"] = project_rows[0][35] or ''
        
        # 添加得分数据
        for item in data[1:]:  # 跳过第一项（项目信息）
            条文号 = item.get("条文号", "")
            得分 = item.get("得分", "")
            技术措施 = item.get("技术措施", "")
            
            if 条文号:
                # 添加条文号对应的分值
                attributes[条文号] = str(得分)
                # 添加条文号对应的技术措施
                attributes[f"{条文号}措施"] = 技术措施
        
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
