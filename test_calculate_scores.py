import requests
import json
import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')

def test_calculate_scores(project_id):
    """测试计算评分API"""
    try:
        # 构建API URL
        api_url = f"http://localhost:5000/api/calculate_scores/{project_id}"
        
        # 发送请求
        logger.info(f"调用计算评分API: {api_url}")
        response = requests.post(api_url)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            logger.info(f"计算评分成功: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查计算结果
            if data.get('success'):
                scores = data.get('scores', {})
                专业分数 = scores.get('专业分数', {})
                章节分数 = scores.get('章节分数', {})
                项目总分 = scores.get('项目总分', 0)
                评定结果 = scores.get('评定结果', '')
                
                logger.info(f"专业分数: {专业分数}")
                logger.info(f"章节分数: {章节分数}")
                logger.info(f"项目总分: {项目总分}")
                logger.info(f"评定结果: {评定结果}")
                
                # 检查数据库中的项目信息
                logger.info("检查数据库中的项目信息...")
                check_project_in_db(project_id)
            else:
                logger.error(f"计算评分失败: {data.get('message', '未知错误')}")
        else:
            logger.error(f"API请求失败: 状态码={response.status_code}, 响应={response.text}")
    
    except Exception as e:
        logger.error(f"测试计算评分API时出错: {str(e)}")
        raise

def check_project_in_db(project_id):
    """检查数据库中的项目信息"""
    try:
        import pyodbc
        
        # 获取数据库连接字符串
        db_uri = os.environ.get('DATABASE_URL')
        if not db_uri:
            # 如果环境变量未设置，使用默认连接字符串
            db_uri = "mssql+pyodbc://test:123456@acbim.fun/绿色建筑?driver=ODBC+Driver+17+for+SQL+Server"
            logger.warning("警告: DATABASE_URL 环境变量未设置，使用默认连接字符串")
        
        # 解析连接字符串
        parts = db_uri.replace('mssql+pyodbc://', '').split('@')
        credentials = parts[0].split(':')
        username = credentials[0]
        password = credentials[1]
        server_db = parts[1].split('?')[0].split('/')
        server = server_db[0]
        database = server_db[1]
        
        # 构建ODBC连接字符串
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        
        # 创建连接
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # 查询项目信息
        cursor.execute("""
            SELECT 
                id, name, standard, 
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
        """, (project_id,))
        
        # 获取结果
        row = cursor.fetchone()
        if row:
            logger.info(f"项目ID: {row[0]}")
            logger.info(f"项目名称: {row[1]}")
            logger.info(f"评价标准: {row[2]}")
            logger.info(f"建筑总分: {row[3]}")
            logger.info(f"结构总分: {row[4]}")
            logger.info(f"给排水总分: {row[5]}")
            logger.info(f"电气总分: {row[6]}")
            logger.info(f"暖通总分: {row[7]}")
            logger.info(f"景观总分: {row[8]}")
            logger.info(f"建筑创新总分: {row[9]}")
            logger.info(f"结构创新总分: {row[10]}")
            logger.info(f"暖通创新总分: {row[11]}")
            logger.info(f"景观创新总分: {row[12]}")
            logger.info(f"安全耐久总分: {row[13]}")
            logger.info(f"健康舒适总分: {row[14]}")
            logger.info(f"生活便利总分: {row[15]}")
            logger.info(f"资源节约总分: {row[16]}")
            logger.info(f"环境宜居总分: {row[17]}")
            logger.info(f"提高与创新总分: {row[18]}")
            logger.info(f"项目总分: {row[19]}")
            logger.info(f"评定结果: {row[20]}")
        else:
            logger.error(f"未找到项目ID为 {project_id} 的记录")
        
        # 确保正确关闭数据库连接
        try:
            cursor.close()
            conn.close()
            logger.info("数据库连接已关闭")
        except Exception as close_error:
            logger.error(f"关闭数据库连接时出错: {str(close_error)}")
            # 不抛出异常，因为主要查询操作已完成
    
    except Exception as e:
        logger.error(f"检查数据库中的项目信息时出错: {str(e)}")
        raise

if __name__ == "__main__":
    # 获取项目ID参数
    if len(sys.argv) > 1:
        project_id = int(sys.argv[1])
    else:
        project_id = 51  # 默认项目ID
    
    # 测试计算评分API
    test_calculate_scores(project_id)