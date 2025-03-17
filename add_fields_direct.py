import os
import sys
import logging
import pyodbc
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')

def add_fields_direct():
    """使用pyodbc直接执行SQL语句来添加字段"""
    try:
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
        
        # 查询projects表的列名
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'")
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"现有列: {existing_columns}")
        
        # 添加新的评分字段（使用英文字段名）
        fields = [
            ("architecture_score", "建筑总分"),
            ("structure_score", "结构总分"),
            ("water_supply_score", "给排水总分"),
            ("electrical_score", "电气总分"),
            ("hvac_score", "暖通总分"),
            ("landscape_score", "景观总分"),
            ("architecture_innovation_score", "建筑创新总分"),
            ("structure_innovation_score", "结构创新总分"),
            ("hvac_innovation_score", "暖通创新总分"),
            ("landscape_innovation_score", "景观创新总分"),
            ("safety_durability_score", "安全耐久总分"),
            ("health_comfort_score", "健康舒适总分"),
            ("life_convenience_score", "生活便利总分"),
            ("resource_saving_score", "资源节约总分"),
            ("environment_livability_score", "环境宜居总分"),
            ("improvement_innovation_score", "提高与创新总分"),
            ("total_score", "项目总分")
        ]
        
        for field_name, description in fields:
            try:
                # 检查字段是否已存在
                if field_name.lower() in [col.lower() for col in existing_columns]:
                    logger.info(f"字段 {field_name} 已存在，跳过")
                    continue
                
                # 构建SQL语句
                sql = f"ALTER TABLE projects ADD {field_name} FLOAT"
                logger.info(f"执行SQL: {sql}")
                
                # 执行SQL语句
                cursor.execute(sql)
                conn.commit()
                
                logger.info(f"添加字段 {field_name} ({description}) 成功")
            except Exception as e:
                logger.error(f"添加字段 {field_name} 时出错: {str(e)}")
        
        # 添加评定结果字段
        try:
            # 检查字段是否已存在
            if "evaluation_result" in [col.lower() for col in existing_columns]:
                logger.info("字段 evaluation_result 已存在，跳过")
            else:
                # 构建SQL语句
                sql = "ALTER TABLE projects ADD evaluation_result NVARCHAR(20)"
                logger.info(f"执行SQL: {sql}")
                
                # 执行SQL语句
                cursor.execute(sql)
                conn.commit()
                
                logger.info("添加字段 evaluation_result (评定结果) 成功")
        except Exception as e:
            logger.error(f"添加字段 evaluation_result 时出错: {str(e)}")
        
        # 再次查询列名
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'")
        updated_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"更新后的列: {updated_columns}")
        
        # 检查是否添加成功
        added_fields = set([col.lower() for col in updated_columns]) - set([col.lower() for col in existing_columns])
        logger.info(f"添加的字段: {added_fields}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        logger.info("所有评分字段添加完成")
        
    except Exception as e:
        logger.error(f"添加评分字段时出错: {str(e)}")
        raise

if __name__ == "__main__":
    add_fields_direct() 