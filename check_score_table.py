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

def check_score_table():
    """检查得分表的结构"""
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
        
        # 检查得分表是否存在
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '得分表'")
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            logger.error("得分表不存在")
            return
        
        # 查询得分表的列名
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '得分表'")
        columns = [row[0] for row in cursor.fetchall()]
        
        logger.info("得分表的列名:")
        for col in columns:
            logger.info(f"  {col}")
        
        # 查询得分表中的数据
        cursor.execute("SELECT TOP 5 * FROM [得分表]")
        rows = cursor.fetchall()
        
        logger.info("得分表中的前5条记录:")
        for i, row in enumerate(rows):
            logger.info(f"记录 {i+1}:")
            for j, col in enumerate(columns):
                logger.info(f"  {col}: {row[j]}")
        
        # 关闭连接
        cursor.close()
        conn.close()
    
    except Exception as e:
        logger.error(f"检查得分表结构时出错: {str(e)}")
        raise

if __name__ == "__main__":
    check_score_table() 