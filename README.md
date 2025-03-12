# 绿建标准数据库-成都市标 网页展示系统

这是一个用于展示绿建标准数据库中成都市标准的Web应用程序。

## 功能特点

- 从SQL Server数据库读取绿建标准数据
- 以表格形式展示标准数据
- 响应式设计，适应不同屏幕尺寸

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 安装SQL Server ODBC驱动程序：
   - 对于Windows：从Microsoft官网下载并安装"ODBC Driver for SQL Server"
   - 对于Linux：按照Microsoft文档安装相应的驱动程序

3. 配置数据库连接：
   - 编辑`.env`文件，设置正确的SQL Server连接信息：
   ```
   DATABASE_URL=mssql+pyodbc://用户名:密码@服务器名/绿建标准?driver=ODBC+Driver+17+for+SQL+Server
   ```
   - 将`用户名`、`密码`和`服务器名`替换为您的SQL Server凭据

4. 确保SQL Server数据库中存在名为"绿建标准"的数据库，并包含"成都市标"表，表结构应包含以下中文字段：
   - 序号 (主键)
   - 条文号
   - 分类
   - 专业
   - 条文内容
   - 分值
   - 审查材料

## 运行应用

```bash
python app.py
```

应用将在本地启动，访问 http://localhost:5000 查看数据表格。

## 技术栈

- 后端：Flask, SQLAlchemy
- 数据库：SQL Server
- 前端：HTML, CSS 