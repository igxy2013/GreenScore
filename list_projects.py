import os
import pyodbc
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    try:
        # 解析数据库连接字符串
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("数据库连接字符串未配置")
            raise ValueError("数据库连接字符串未配置")

        # 使用正则表达式解析连接字符串
        import re
        pattern = r'mssql\+pyodbc://([^:]+):([^@]+)@([^/]+)/([^?]+)'
        match = re.match(pattern, db_url)
        if not match:
            print("数据库连接字符串格式错误")
            raise ValueError("数据库连接字符串格式错误")

        username, password, server, database = match.groups()
        
        # 构建pyodbc连接字符串
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        # 尝试建立连接
        try:
            conn = pyodbc.connect(conn_str)
            print("数据库连接成功")
            return conn
        except pyodbc.Error as e:
            print(f"数据库连接失败: {str(e)}")
            raise
    except Exception as e:
        print(f"创建数据库连接时出错: {str(e)}")
        raise

def list_projects():
    """列出项目"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取项目列表
        cursor.execute("SELECT TOP 10 id, name, standard, star_rating_target FROM projects ORDER BY id DESC")
        rows = cursor.fetchall()
        
        print("\n项目列表:")
        print("=" * 60)
        print(f"{'ID':<5} | {'名称':<30} | {'评价标准':<10} | {'星级目标':<10}")
        print("-" * 60)
        
        for row in rows:
            project_id = row[0]
            name = row[1] or '未命名项目'
            standard = row[2] or '未设置'
            star_rating_target = row[3] or '未设置'
            print(f"{project_id:<5} | {name[:30]:<30} | {standard:<10} | {star_rating_target:<10}")
        
        print("=" * 60)
        print("提示: 使用 'python test_dwg_export.py <项目ID>' 测试DWG导出功能")
        
    except Exception as e:
        print(f"获取项目列表失败: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    list_projects() 