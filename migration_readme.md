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