import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')

def check_db_structure():
    """查询数据库中projects表的结构"""
    try:
        # 获取数据库连接字符串
        db_uri = os.environ.get('DATABASE_URL')
        if not db_uri:
            # 如果环境变量未设置，使用默认连接字符串
            db_uri = "mssql+pyodbc://test:123456@acbim.fun/绿色建筑?driver=ODBC+Driver+17+for+SQL+Server"
            logger.warning("警告: DATABASE_URL 环境变量未设置，使用默认连接字符串")
        
        # 安全地获取数据库URL并打印
        masked_url = db_uri.replace(':' + db_uri.split(':')[2].split('@')[0] + '@', ':***@')
        logger.info(f"使用SQL Server数据库: {masked_url}")
        
        # 创建数据库引擎
        engine = create_engine(db_uri)
        
        # 创建连接
        with engine.connect() as conn:
            # 查询projects表的列名
            result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
            columns = [row[0] for row in result]
            
            print("projects表的列名:")
            for col in columns:
                print(col)
        
    except Exception as e:
        logger.error(f"查询数据库结构时出错: {str(e)}")
        raise

if __name__ == "__main__":
    check_db_structure() 