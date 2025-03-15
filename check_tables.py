import pyodbc

# 连接数据库
conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=acbim.fun;DATABASE=绿色建筑;UID=test;PWD=123456'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# 查询所有表
print("数据库中的表:")
cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

# 关闭连接
cursor.close()
conn.close() 