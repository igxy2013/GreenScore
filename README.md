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