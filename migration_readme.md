# MySQL数据库配置指南

1. 创建MySQL数据库：
```sql
CREATE DATABASE `绿色建筑` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 配置MySQL数据库环境变量：
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

# SQL Server到MySQL数据迁移

本脚本用于将SQL Server数据库中的数据迁移到MySQL数据库。

## 环境要求

- Python 3.8+
- 依赖项：pandas, pyodbc, pymysql
- SQL Server ODBC驱动程序
- MySQL数据库

## 配置说明

迁移前需要正确配置环境变量或.env文件，指定源数据库和目标数据库的连接信息：

### SQL Server配置（源数据库）
```
SQLSERVER_SERVER=aibim.xyz
SQLSERVER_DATABASE=绿色建筑
SQLSERVER_USERNAME=test
SQLSERVER_PASSWORD=123456
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
```

### MySQL配置（目标数据库）
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=绿色建筑
MYSQL_USERNAME=mysql
MYSQL_PASSWORD=12345678
```

## 使用方法

1. 安装依赖项：
```bash
pip install pandas pyodbc pymysql
```

2. 配置环境变量或.env文件

3. 运行迁移脚本：
```bash
python migrate_to_mysql.py
```

## 执行结果

迁移过程将在控制台和migration.log文件中记录。成功完成后，会显示迁移的表数量和记录数量。

## 问题排查

- 如果遇到ODBC驱动程序问题，请确保已安装正确版本的SQL Server ODBC驱动
- 如果遇到字符集问题，请检查MySQL数据库的字符集设置，建议使用utf8mb4

## 注意事项

- 迁移脚本会先删除目标数据库中已存在的同名表，请确保备份重要数据
- 迁移过程中表结构可能会被简化，仅保留基本数据类型
- 部分复杂的索引、约束和存储过程需要手动迁移