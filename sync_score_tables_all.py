import os
import sys
import logging
import traceback
from dotenv import load_dotenv
import pyodbc

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('greenscore')

def get_db_connection():
    """获取数据库连接"""
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
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

def sync_score_tables_all():
    """同步所有项目的得分表和project_scores表的数据"""
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查project_scores表是否存在
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'project_scores'")
        if cursor.fetchone()[0] == 0:
            logger.info("project_scores表不存在，创建表")
            # 创建project_scores表
            cursor.execute("""
                CREATE TABLE project_scores (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    project_id INT NOT NULL,
                    level NVARCHAR(10) NOT NULL,
                    specialty NVARCHAR(20) NOT NULL,
                    clause_number NVARCHAR(20) NOT NULL,
                    category NVARCHAR(20) NULL,
                    is_achieved NVARCHAR(10) NOT NULL,
                    score FLOAT NULL,
                    technical_measures NVARCHAR(MAX) NULL,
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE()
                )
            """)
            conn.commit()
            logger.info("成功创建project_scores表")
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX idx_project_scores_project_id ON project_scores (project_id)
            """)
            conn.commit()
            logger.info("成功创建project_scores表索引")
        
        # 获取所有项目ID
        cursor.execute("SELECT DISTINCT [项目ID] FROM [得分表] WHERE [项目ID] IS NOT NULL")
        project_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"找到 {len(project_ids)} 个项目需要同步")
        
        # 清空project_scores表
        cursor.execute("DELETE FROM project_scores")
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"清空project_scores表，删除了 {deleted_count} 条记录")
        
        # 为每个项目同步数据
        total_imported = 0
        for project_id in project_ids:
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
            logger.info(f"项目 {project_id} 同步完成，导入了 {imported_count} 条记录")
            total_imported += imported_count
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        logger.info(f"所有项目同步完成，共导入 {total_imported} 条记录")
        return True
    except Exception as e:
        logger.error(f"同步所有项目数据时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("开始同步所有项目的得分表和project_scores表数据")
    result = sync_score_tables_all()
    if result:
        logger.info("同步成功")
    else:
        logger.error("同步失败") 