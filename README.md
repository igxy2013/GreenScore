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