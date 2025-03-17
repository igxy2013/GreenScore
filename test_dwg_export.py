import os
import sys
import json
import logging
from dotenv import load_dotenv
import pyodbc
from update_dwg_attribute import update_attribute_text

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dwg_export_test')

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    try:
        # 解析数据库连接字符串
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("数据库连接字符串未配置")
            raise ValueError("数据库连接字符串未配置")

        # 使用正则表达式解析连接字符串
        import re
        pattern = r'mssql\+pyodbc://([^:]+):([^@]+)@([^/]+)/([^?]+)'
        match = re.match(pattern, db_url)
        if not match:
            logger.error("数据库连接字符串格式错误")
            raise ValueError("数据库连接字符串格式错误")

        username, password, server, database = match.groups()
        
        # 构建pyodbc连接字符串
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        # 尝试建立连接
        try:
            conn = pyodbc.connect(conn_str)
            logger.info("数据库连接成功")
            return conn
        except pyodbc.Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"创建数据库连接时出错: {str(e)}")
        raise

def test_dwg_export(project_id):
    """测试DWG导出功能"""
    cursor = None
    conn = None
    try:
        # 获取数据库连接
        logger.info("从数据库获取数据...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取项目基本信息
        logger.info(f"获取项目 {project_id} 的基本信息")
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
            logger.error(f"未找到项目数据: ID={project_id}")
            return False

        logger.info(f"获取到项目数据: {project_rows[0]}")
        
        # 获取项目的评价标准和星级目标
        standard = project_rows[0][8] or '成都市标'  # 默认为成都市标
        star_rating_target = project_rows[0][7] or ''  # 星级目标
        
        logger.info(f"项目评价标准: {standard}, 星级目标: {star_rating_target}")
        
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
        template_path = os.path.join('static', 'templates', template_filename)
        logger.info(f"CAD模板文件路径: {template_path}")
        if not os.path.exists(template_path):
            logger.error(f"CAD模板文件不存在: {template_path}")
            return False

        # 获取得分数据
        logger.info(f"获取项目 {project_id} 的得分数据")
        cursor.execute("""
            SELECT 条文号, 分类, 是否达标, 得分, 技术措施 
            FROM 得分表 
            WHERE 项目ID = ?
            ORDER BY 条文号
        """, [project_id])
        score_rows = cursor.fetchall()
        
        logger.info(f"获取到 {len(score_rows)} 条得分数据")

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
        for row in score_rows:
            data.append({
                "条文号": row[0],
                "分类": row[1],
                "是否达标": row[2],
                "得分": row[3],
                "技术措施": row[4]
            })

        # 准备属性数据
        attributes = {}
        
        # 添加项目信息
        attributes["项目名称"] = data[0]["项目名称"]
        attributes["设计单位"] = data[0]["设计单位"]
        attributes["建设单位"] = data[0]["建设单位"]
        attributes["建筑面积"] = data[0]["建筑面积"]
        attributes["建筑类型"] = data[0]["建筑类型"]
        attributes["项目地点"] = data[0]["项目地点"]
        attributes["气候区划"] = data[0]["气候区划"]
        attributes["星级目标"] = data[0]["星级目标"]
        
        # 添加更多项目详细信息
        attributes["总用地面积"] = str(project_rows[0][9] or '')
        attributes["绿地面积"] = str(project_rows[0][10] or '')
        attributes["绿地率"] = str(project_rows[0][11] or '')
        attributes["容积率"] = str(project_rows[0][12] or '')
        attributes["建筑密度"] = str(project_rows[0][13] or '')
        attributes["建筑层数"] = str(project_rows[0][14] or '')
        attributes["建筑高度"] = str(project_rows[0][15] or '')
        attributes["地上建筑面积"] = str(project_rows[0][16] or '')
        attributes["地下建筑面积"] = str(project_rows[0][17] or '')
        
        # 添加评分数据
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
                # 添加条文号对应的技术措施（只有在技术措施不为空时才添加）
                if 技术措施 and 技术措施.strip():
                    attributes[f"{条文号}措施"] = 技术措施
        
        # 生成输出文件路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join('temp', f'test_green_building_{timestamp}.dwg')
        
        # 调用update_attribute_text更新DWG文件
        logger.info(f"开始更新CAD文件，使用模板: {template_filename}...")
        logger.info(f"更新的属性数量: {len(attributes)}")
        
        # 将属性数据保存到文件，以便检查
        with open(os.path.join('temp', f'attributes_{timestamp}.json'), 'w', encoding='utf-8') as f:
            json.dump(attributes, f, ensure_ascii=False, indent=4)
        
        update_attribute_text(template_path, output_path, attributes)
        
        # 检查生成的文件是否存在
        if not os.path.exists(output_path):
            logger.error(f"生成的CAD文件不存在: {output_path}")
            return False
            
        logger.info(f"CAD文件生成成功: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"生成CAD文件失败: {str(e)}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_dwg_export.py <项目ID>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    success = test_dwg_export(project_id)
    
    if success:
        print("DWG导出测试成功")
        sys.exit(0)
    else:
        print("DWG导出测试失败")
        sys.exit(1) 