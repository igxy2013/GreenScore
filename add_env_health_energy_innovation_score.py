import os
from sqlalchemy import create_engine, text
import logging
import traceback
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')
handler = RotatingFileHandler('logs/add_fields.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def add_env_health_energy_innovation_score():
    """向projects表添加环境健康与节能创新总分字段"""
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
            # 检查projects表是否存在
            result = conn.execute(text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'projects'"))
            table_exists = result.scalar() > 0
            
            if not table_exists:
                logger.error("projects表不存在！")
                return
            
            logger.info("projects表存在，开始添加字段")
            
            # 检查现有列
            result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
            existing_columns = [row[0] for row in result]
            logger.info(f"现有列: {existing_columns}")
            
            field_name = "env_health_energy_innovation_score"
            description = "环境健康与节能创新总分"
            
            try:
                # 检查字段是否已存在
                if field_name in existing_columns:
                    logger.info(f"字段 {field_name} 已存在，跳过")
                else:
                    # 构建SQL语句
                    sql = f"""
                    IF NOT EXISTS (
                        SELECT * FROM sys.columns 
                        WHERE name = '{field_name}' AND object_id = OBJECT_ID('projects')
                    )
                    BEGIN
                        ALTER TABLE projects ADD {field_name} FLOAT
                    END
                    """
                    logger.info(f"执行SQL: {sql}")
                    
                    # 执行SQL语句
                    conn.execute(text(sql))
                    conn.commit()  # 确保提交事务
                    
                    logger.info(f"添加字段 {field_name} ({description}) 成功")
            except Exception as e:
                logger.error(f"添加字段 {field_name} 时出错: {str(e)}")
                logger.error(traceback.format_exc())
            
            # 再次检查列
            result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
            updated_columns = [row[0] for row in result]
            logger.info(f"更新后的列: {updated_columns}")
            
            logger.info("环境健康与节能创新总分字段添加完成")
            
    except Exception as e:
        logger.error(f"添加字段时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    add_env_health_energy_innovation_score()