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

def create_tables():
    """创建数据库表"""
    try:
        # 从环境变量获取数据库配置
        server = os.environ.get('SQLSERVER_SERVER', 'acbim.fun')
        database = os.environ.get('SQLSERVER_DATABASE', '绿色建筑')
        username = os.environ.get('SQLSERVER_USERNAME', 'test')
        password = os.environ.get('SQLSERVER_PASSWORD', '123456')
        driver = os.environ.get('SQLSERVER_DRIVER', '{SQL Server}')

        # 构建数据库连接字符串
        db_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={urllib.parse.quote_plus(driver)}"
        logger.info("数据库配置已加载")
        
        # 安全地获取数据库URL并打印
        masked_url = db_uri.replace(':' + db_uri.split(':')[2].split('@')[0] + '@', ':***@')
        logger.info(f"使用SQL Server数据库: {masked_url}")
        
        # 创建数据库引擎
        engine = create_engine(db_uri)
        
        # 创建连接
        with engine.connect() as conn:
            # 创建项目表
            conn.execute(text('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'projects')
            BEGIN
                CREATE TABLE projects (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(255) NOT NULL,
                    location NVARCHAR(255),
                    climate_zone NVARCHAR(50),
                    building_type NVARCHAR(50),
                    public_building_type NVARCHAR(50),
                    construction_type NVARCHAR(50),
                    total_land_area FLOAT,
                    above_ground_area FLOAT,
                    underground_area FLOAT,
                    first_floor_underground_area FLOAT,
                    plot_ratio FLOAT,
                    green_ratio FLOAT,
                    green_area FLOAT,
                    residential_units INT,
                    average_floors FLOAT,
                    star_rating_target NVARCHAR(50),
                    public_green_space FLOAT,
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE()
                )
            END
            '''))
            
            print("项目表创建成功")
            
            # 检查并添加public_green_space列
            try:
                conn.execute(text('''
                IF NOT EXISTS (
                    SELECT * FROM sys.columns 
                    WHERE name = 'public_green_space' AND object_id = OBJECT_ID('projects')
                )
                BEGIN
                    ALTER TABLE projects ADD public_green_space FLOAT
                END
                '''))
                print("检查或添加public_green_space列成功")
            except Exception as e:
                print(f"检查或添加列时出错: {str(e)}")
            
            # 创建得分表
            conn.execute(text('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '得分表')
            BEGIN
                CREATE TABLE [得分表] (
                    [ID] INT IDENTITY(1,1) PRIMARY KEY,
                    [项目ID] INT NOT NULL,
                    [项目名称] NVARCHAR(100),
                    [专业] NVARCHAR(50),
                    [评价等级] NVARCHAR(20),
                    [条文号] NVARCHAR(50),
                    [分类] NVARCHAR(50),
                    [是否达标] NVARCHAR(10),
                    [得分] NVARCHAR(10),
                    [技术措施] NVARCHAR(MAX),
                    [评价标准] NVARCHAR(50),
                    [创建时间] DATETIME DEFAULT GETDATE(),
                    [更新时间] DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_得分表_Projects FOREIGN KEY ([项目ID]) 
                        REFERENCES projects (id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            END
            '''))
            
            print("得分表创建成功")
            
            # 创建星级案例表
            conn.execute(text('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '星级案例表')
            BEGIN
                CREATE TABLE 星级案例表 (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    项目ID INT,
                    星级目标 NVARCHAR(20),
                    条文号 NVARCHAR(20),
                    分类 NVARCHAR(20),
                    是否达标 NVARCHAR(10),
                    得分 NVARCHAR(10),
                    技术措施 NVARCHAR(MAX),
                    专业 NVARCHAR(20),
                    评价等级 NVARCHAR(20),
                    评价标准 NVARCHAR(50),
                    创建时间 DATETIME DEFAULT GETDATE(),
                    更新时间 DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_星级案例表_Projects FOREIGN KEY (项目ID) 
                        REFERENCES projects (id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            END
            '''))
            
            print("星级案例表创建成功")
            
    except Exception as e:
        logger.error(f"创建表时出错: {str(e)}")
        raise

if __name__ == "__main__":
    create_tables()