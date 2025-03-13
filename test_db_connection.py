import os
import pyodbc
import urllib.parse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_connection():
    try:
        # 直接使用连接字符串
        server = "acbim.fun"
        database = "绿色建筑"  # 使用"绿色建筑"作为数据库名
        username = "test"
        password = "123456"
        
        print(f"服务器: {server}")
        print(f"数据库: {database}")
        print(f"用户名: {username}")
        
        # 构建连接字符串
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        print(f"连接字符串: {conn_str}")
        
        # 尝试连接
        conn = pyodbc.connect(conn_str)
        print("数据库连接成功!")
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM 成都市标")
        row = cursor.fetchone()
        if row:
            print(f"查询成功，第一行数据: {row}")
        else:
            print("查询成功，但没有数据")
        
        # 关闭连接
        conn.close()
        return True
    except Exception as e:
        print(f"连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 