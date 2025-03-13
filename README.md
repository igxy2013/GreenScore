# 绿色建筑评价系统

## 项目概述
绿色建筑评价系统是一个基于Flask的Web应用，用于评估建筑项目的绿色建材应用比例和绿色建筑评分。系统支持多种评价标准，包括成都市标、四川省标和通用国标。

## 功能特点

### 项目管理
- 创建新项目并选择评价标准（成都市标、四川省标、通用国标）
- 查看和管理现有项目
- 每个项目可以独立设置项目信息和评价标准

### 绿色建材计算
- 计算绿色建材应用比例
- 支持多种建材类别的评估
- 自动计算得分和达标率

### 评分汇总
- 汇总各项评分结果
- 生成评分报告
- 导出计算书

## 技术栈
- 后端：Flask, SQLAlchemy
- 前端：HTML, CSS (Tailwind CSS), JavaScript
- 数据库：SQL Server

## 安装与运行

### 环境要求
- Python 3.8+
- SQL Server 数据库
- ODBC Driver 17 for SQL Server

### 安装步骤
1. 克隆仓库
```
git clone <repository-url>
cd <repository-directory>
```

2. 创建并激活虚拟环境
```
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 安装依赖
```
pip install -r requirements.txt
```

4. 配置数据库连接
创建 `.env` 文件并设置数据库连接字符串：
```
DATABASE_URL=mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
```

5. 创建数据库表
```
python create_tables.py
```

6. 运行应用
```
flask run
```

7. 访问应用
在浏览器中访问 `http://localhost:5000`

## 生产环境部署

### Windows服务器部署

#### 方法一：一键部署（临时运行）

1. 双击运行 `deploy.bat` 脚本
2. 脚本会自动安装依赖并启动应用
3. 应用将在命令行窗口中运行，关闭窗口即停止应用

#### 方法二：作为Windows服务运行（推荐）

1. 下载并安装 [NSSM](https://nssm.cc/download)
2. 以管理员身份运行 `install_service.bat` 脚本
3. 脚本会自动创建并启动Windows服务
4. 服务将在后台运行，即使用户注销也不会停止
5. 可以通过Windows服务管理器管理服务

### 环境配置

1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env` 文件，设置数据库连接和其他配置
3. 主要配置项：
   - `DATABASE_URL`: 数据库连接字符串
   - `FLASK_ENV`: 设置为 `production`
   - `PORT`: 应用端口，默认5000

### 访问应用

部署完成后，可以通过以下地址访问应用：
- 本地访问：http://localhost:5000
- 局域网访问：http://服务器IP:5000

### 故障排除

如果应用无法启动或运行异常，请检查以下日志文件：
- `logs/app.log`: 应用日志
- `logs/server.log`: 服务器日志
- `logs/service_stdout.log`: 服务标准输出（仅服务模式）
- `logs/service_stderr.log`: 服务错误输出（仅服务模式）

## 使用指南

### 创建新项目
1. 访问项目管理页面
2. 填写项目信息（名称、编号、建设单位等）
3. 选择评价标准（成都市标、四川省标、通用国标）
4. 点击"创建项目"按钮

### 绿色建材计算
1. 进入项目详情页面
2. 选择"绿色建材"选项卡
3. 填写各类建材的应用比例
4. 点击"立即计算"按钮查看结果

### 导出计算书
1. 完成绿色建材计算后
2. 点击"导出计算书"按钮
3. 保存生成的Word文档 