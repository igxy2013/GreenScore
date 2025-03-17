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

def create_project_scores_table():
    """创建project_scores表"""
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
        
        # 检查表是否已存在
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'project_scores'")
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            logger.info("project_scores表已存在，跳过创建")
        else:
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
        
        # 检查得分表是否存在
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '得分表'")
        score_table_exists = cursor.fetchone()[0] > 0
        
        if score_table_exists:
            # 从得分表导入数据到project_scores表
            logger.info("从得分表导入数据到project_scores表")
            
            # 检查得分表中是否有数据
            cursor.execute("SELECT COUNT(*) FROM [得分表]")
            score_count = cursor.fetchone()[0]
            logger.info(f"得分表中有 {score_count} 条记录")
            
            if score_count > 0:
                # 查询得分表中的数据
                cursor.execute("""
                    SELECT [项目ID], [评价等级], [专业], [条文号], [分类], [是否达标], [得分], [技术措施]
                    FROM [得分表]
                """)
                scores = cursor.fetchall()
                
                # 导入数据到project_scores表
                imported_count = 0
                for score in scores:
                    project_id, level, specialty, clause_number, category, is_achieved, score_value, technical_measures = score
                    
                    # 检查project_scores表中是否已存在相同记录
                    cursor.execute("""
                        SELECT COUNT(*) FROM project_scores 
                        WHERE project_id = ? AND level = ? AND specialty = ? AND clause_number = ?
                    """, (project_id, level, specialty, clause_number))
                    exists = cursor.fetchone()[0] > 0
                    
                    if not exists:
                        # 插入数据
                        cursor.execute("""
                            INSERT INTO project_scores (project_id, level, specialty, clause_number, category, is_achieved, score, technical_measures)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (project_id, level, specialty, clause_number, category, is_achieved, score_value, technical_measures))
                        imported_count += 1
                
                conn.commit()
                logger.info(f"成功从得分表导入 {imported_count} 条记录到project_scores表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        logger.info("project_scores表创建和数据导入完成")
    
    except Exception as e:
        logger.error(f"创建project_scores表时出错: {str(e)}")
        raise

if __name__ == "__main__":
    create_project_scores_table() 