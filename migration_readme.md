# SQL Server到MySQL迁移指南

## 准备工作

1. 安装所需Python包：
```bash
pip install pymysql pandas sqlalchemy pyodbc
```

2. 确保安装了ODBC驱动程序，用于连接SQL Server。
   - Windows: "ODBC Driver 17 for SQL Server" (注意格式必须正确)
   - Linux: 请参考[Microsoft的文档](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

3. 创建MySQL数据库：
```sql
CREATE DATABASE `绿色建筑` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 迁移步骤

### 1. 配置环境变量（可选）

配置源数据库（SQL Server）：
```bash
# Windows
set SQLSERVER_SERVER=localhost
set SQLSERVER_DATABASE=绿色建筑
set SQLSERVER_USERNAME=test
set SQLSERVER_PASSWORD=123456
set SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server

# Linux/Mac
export SQLSERVER_SERVER=localhost
export SQLSERVER_DATABASE=绿色建筑
export SQLSERVER_USERNAME=test
export SQLSERVER_PASSWORD=123456
export SQLSERVER_DRIVER="ODBC Driver 17 for SQL Server"
```

配置目标数据库（MySQL）：
```bash
# Windows
set MYSQL_HOST=localhost
set MYSQL_PORT=3306
set MYSQL_DATABASE=绿色建筑
set MYSQL_USERNAME=root
set MYSQL_PASSWORD=123456

# Linux/Mac
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=绿色建筑
export MYSQL_USERNAME=root
export MYSQL_PASSWORD=123456
```

### 2. 创建目标数据库表结构

运行初始化脚本创建MySQL数据库表结构：
```bash
python init_mysql_db.py
```

### 3. 执行数据迁移

运行迁移脚本，将数据从SQL Server迁移到MySQL：
```bash
python migrate_to_mysql.py
```

### 注意事项

- 迁移脚本现在使用pyodbc直接连接SQL Server，而不是通过SQLAlchemy
- 这样做可以避免pandas与SQLAlchemy连接对象之间的兼容性问题
- 如果pandas的to_sql方法失败，脚本会自动尝试使用原生SQL语句进行迁移
- 该脚本支持两种方式写入MySQL：
  1. 通过pandas的to_sql方法直接写入（使用分批处理）
  2. 通过生成CREATE TABLE和INSERT语句手动写入
- 如果需要查看系统中安装的ODBC驱动，可以运行以下Python代码：
  ```python
  import pyodbc
  print(pyodbc.drivers())
  ```

### 4. 验证迁移结果

检查迁移日志（migration.log）确认所有表都已成功迁移。

### 5. 配置应用使用MySQL

确保修改了配置文件，使应用连接到MySQL数据库：
- 配置文件已更新，不需要额外修改。

### 6. 启动应用

启动应用，验证是否能正常连接到MySQL数据库：
```bash
python server.py
```

## 故障排除

如果遇到以下问题，请尝试相应的解决方法：

1. **SQL Server连接错误**：
   - 确认SQL Server服务是否运行
   - 检查网络连接和防火墙设置
   - 验证用户名和密码是否正确
   - 确保ODBC驱动名称正确，例如 "ODBC Driver 17 for SQL Server"（不要使用 {SQL Server}）
   - 使用 `pyodbc.drivers()` 命令查看系统中可用的ODBC驱动列表
   - Windows系统上，确保在ODBC驱动字符串中使用三重大括号：`f'DRIVER={{{driver}}};...'`

2. **MySQL连接错误**：
   - 确认MySQL服务是否运行
   - 检查用户权限是否足够
   - 验证数据库名称是否正确
   - 确认字符集设置是否为utf8mb4
   - 如果出现连接超时，检查：
     * MySQL服务器是否允许远程连接
     * 防火墙是否允许3306端口
     * 尝试使用localhost而不是远程地址

3. **连接对象错误**：
   - 如果看到 `'Engine' object has no attribute 'cursor'` 错误，这表明pandas在尝试使用SQLAlchemy引擎作为DBAPI连接
   - 我们现在使用SQLAlchemy连接对象而不是引擎对象来写入数据
   - 如果仍然失败，会自动切换到使用原生SQL语句
   - 每个批次都会单独提交，避免事务太大

4. **数据类型不兼容**：
   - MySQL和SQL Server的数据类型有差异，可能需要手动修改某些表的结构
   - 特别注意：SQL Server的nvarchar对应MySQL的varchar，datetime2对应datetime等
   - 对于不兼容的数据类型，备用方法会尝试自动推断合适的MySQL数据类型

5. **中文字符显示问题**：
   - 确保MySQL数据库、表和字段都使用了utf8mb4字符集
   - 检查连接字符串中的charset参数是否为utf8mb4
   - 对于有中文列名的表，可能需要特殊处理列名

6. **大数据量表的处理**：
   - 现在默认使用分批处理（chunksize=1000）
   - 如果内存仍然不足，可以减小chunksize参数
   - 每个批次都会立即提交，避免事务太大
   - 如果某个表特别大，可以考虑手动分片处理

## 其他说明

- 迁移过程会生成详细的日志（migration.log），用于排查问题
- 迁移脚本默认使用replace模式，会先删除目标表中的数据再插入
- 脚本会跳过没有数据的表
- 迁移大表时可能需要较长时间，请耐心等待
- 如果所有方法都失败，可以考虑使用专业的数据库迁移工具，如MySQL Workbench或其他ETL工具 