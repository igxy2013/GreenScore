import os
import sys
import logging
import traceback
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')

def add_score_fields():
    """向projects表添加新的评分字段"""
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
            
            # 添加新的评分字段（使用英文字段名）
            fields = [
                ("architecture_score", "建筑总分"),
                ("structure_score", "结构总分"),
                ("water_supply_score", "给排水总分"),
                ("electrical_score", "电气总分"),
                ("hvac_score", "暖通总分"),
                ("landscape_score", "景观总分"),
                ("env_health_energy_score", "环境健康与节能总分"),
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
            
            # 检查现有列
            result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
            existing_columns = [row[0] for row in result]
            logger.info(f"现有列: {existing_columns}")
            
            for field_name, description in fields:
                try:
                    # 检查字段是否已存在
                    if field_name in existing_columns:
                        logger.info(f"字段 {field_name} 已存在，跳过")
                        continue
                    
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
            
            # 添加评定结果字段
            try:
                # 检查字段是否已存在
                if "evaluation_result" in existing_columns:
                    logger.info("字段 evaluation_result 已存在，跳过")
                else:
                    # 构建SQL语句
                    sql = """
                    IF NOT EXISTS (
                        SELECT * FROM sys.columns 
                        WHERE name = 'evaluation_result' AND object_id = OBJECT_ID('projects')
                    )
                    BEGIN
                        ALTER TABLE projects ADD evaluation_result NVARCHAR(20)
                    END
                    """
                    logger.info(f"执行SQL: {sql}")
                    
                    # 执行SQL语句
                    conn.execute(text(sql))
                    conn.commit()  # 确保提交事务
                    
                    logger.info("添加字段 evaluation_result (评定结果) 成功")
            except Exception as e:
                logger.error(f"添加字段 evaluation_result 时出错: {str(e)}")
                logger.error(traceback.format_exc())
            
            # 再次检查列
            result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
            updated_columns = [row[0] for row in result]
            logger.info(f"更新后的列: {updated_columns}")
            
            # 检查是否添加成功
            added_fields = set(updated_columns) - set(existing_columns)
            logger.info(f"添加的字段: {added_fields}")
            
            logger.info("所有评分字段添加完成")
            
    except Exception as e:
        logger.error(f"添加评分字段时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    add_score_fields()