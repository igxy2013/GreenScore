# GreenScore 绿色建筑评分系统

## 在WSL环境下运行

本项目可以在WSL环境中运行，同时支持Windows环境中的DWG文件生成功能。

### 配置步骤

1. **WSL环境配置**：
   - 确保WSL中已安装Python和必要的依赖：
     ```bash
     sudo apt update
     sudo apt install python3 python3-pip python3-venv
     ```
   - 安装MySQL：
     ```bash
     sudo apt install mysql-server
     sudo service mysql start
     sudo mysql_secure_installation
     ```

2. **数据库配置**：
   - 创建数据库：
     ```bash
     sudo mysql
     CREATE DATABASE 绿色建筑 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     CREATE USER 'greenscore'@'localhost' IDENTIFIED BY 'your_password';
     GRANT ALL PRIVILEGES ON 绿色建筑.* TO 'greenscore'@'localhost';
     FLUSH PRIVILEGES;
     EXIT;
     ```
   - 配置环境变量：
     ```bash
     # 编辑.env文件
     DATABASE_URL=mysql+pymysql://greenscore:your_password@localhost/绿色建筑
     ```

3. **初始化数据库**：
   ```bash
   python init_db.py
   ```

4. **Windows端DWG服务配置**：
   - 在Windows系统上安装Python和AutoCAD
   - 安装必要的Python包：
     ```powershell
     pip install flask flask-cors comtypes requests
     ```
   - 将`dwg_service.py`复制到Windows系统中
   - 启动DWG服务：
     ```powershell
     python dwg_service.py
     ```
   - DWG服务将在端口5001上运行

5. **启动应用**：
   ```bash
   python start.py
   ```

### 跨环境通信

WSL应用能够自动连接到Windows主机上运行的DWG服务：

1. 应用启动时会自动检测是否在WSL环境中运行
2. 在WSL中，会自动尝试连接到Windows主机IP上的DWG服务
3. Windows主机IP会自动从以下来源获取：
   - `/etc/resolv.conf`中的DNS服务器地址
   - `host.docker.internal`域名
   - 默认网关地址

这种配置允许您在WSL中运行主应用程序，同时利用Windows上的AutoCAD功能生成DWG文件。

### 故障排除

1. **无法连接到DWG服务**：
   - 确保Windows防火墙允许端口5001的通信
   - 验证Windows主机IP是否正确
   - 检查DWG服务是否正在运行

2. **数据库连接问题**：
   - 确保MySQL服务已启动：`sudo service mysql status`
   - 检查数据库用户名和密码是否正确
   - 验证数据库名称是否正确

3. **手动设置Windows主机IP**：
   如果自动检测失败，可以在`.env`文件中手动设置：
   ```
   DWG_SERVICE_URL=http://your.windows.ip:5001
   ```

# 得分更新工具

这是一个用于更新"得分表"中数据的工具，可以根据条文号和分值直接修改数据库中的记录。

## 功能特点

- 直接更新数据库中的得分数据
- 支持检查现有得分记录
- 支持列出项目的所有得分记录
- 提供简单易用的Web界面
- 提供JavaScript API，方便在其他页面中调用

## 文件结构

- `update_score_api.py` - Python后端API，提供数据库操作功能
- `static/js/score_api.js` - JavaScript前端API，提供调用后端API的函数
- `templates/score_updater.html` - 示例Web界面

## 安装和使用

### 1. 安装依赖

```bash
pip install flask pyodbc
```

### 2. 启动API服务

```bash
python update_score_api.py
```

服务将在 http://localhost:5001 上运行。

### 3. 访问Web界面

在浏览器中访问 http://localhost:5001/templates/score_updater.html

### 4. 在其他页面中使用

在HTML页面中引入JavaScript API：

```html
<script src="/static/js/score_api.js"></script>
```

然后可以使用以下函数：

```javascript
// 更新得分
updateScore('3.1.2.14', 12, 1);  // 条文号, 得分, 项目ID

// 检查得分
checkScore('3.1.2.14', 1);  // 条文号, 项目ID

// 列出得分
listScores(1, 10);  // 项目ID, 限制数量
```

## API接口说明

### 1. 更新得分

- 接口：`/direct_update_score`
- 方法：POST
- 参数：
  ```json
  {
    "project_id": 1,                 // 项目ID
    "clause_number": "3.1.2.14",     // 条文号
    "score": 12,                     // 得分值
    "standard": "成都市标",           // 评价标准
    "specialty": "建筑专业",          // 专业，可选
    "level": "提高级",               // 评价等级，可选
    "category": "资源节约",           // 分类，可选
    "is_achieved": "true"            // 是否达标，可选
  }
  ```
- 响应：
  ```json
  {
    "success": true,
    "message": "更新成功",
    "data": {
      "project_id": 1,
      "clause_number": "3.1.2.14",
      "score": 12,
      "standard": "成都市标"
    }
  }
  ```

### 2. 检查得分

- 接口：`/check_score`
- 方法：GET
- 参数：`?project_id=1&clause_number=3.1.2.14&standard=成都市标`
- 响应：
  ```json
  {
    "success": true,
    "data": {
      "project_id": 1,
      "clause_number": "3.1.2.14",
      "score": 12,
      "standard": "成都市标",
      "specialty": "建筑专业",
      "level": "提高级",
      "category": "资源节约",
      "is_achieved": "true",
      "technical_measures": ""
    }
  }
  ```

### 3. 列出得分

- 接口：`/list_scores`
- 方法：GET
- 参数：`?project_id=1&standard=成都市标&limit=10`
- 响应：
  ```json
  {
    "success": true,
    "data": [
      {
        "project_id": 1,
        "clause_number": "3.1.2.14",
        "score": 12,
        "standard": "成都市标",
        "specialty": "建筑专业",
        "level": "提高级",
        "category": "资源节约",
        "is_achieved": "true",
        "technical_measures": ""
      },
      // ...更多记录
    ]
  }
  ```

## 注意事项

1. 确保数据库连接字符串正确配置
2. 确保数据库中存在"得分表"表
3. 确保数据库用户有足够的权限进行读写操作
4. 如果遇到中文字符问题，请确保数据库和应用程序使用相同的字符编码 