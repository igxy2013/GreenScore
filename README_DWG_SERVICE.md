# DWG文件处理服务（简化版）

这是一个用于处理AutoCAD DWG文件的简化版服务系统，主要用于更新DWG文件中的文本属性。

## 系统组件

该系统包括以下几个关键组件：

1. **dwg_service_simplified.py** - 服务端主程序，提供HTTP API接口
2. **dwg_client_simplified.py** - 客户端，用于与服务端通信
3. **dwg_service_optimized_simplified.py** - 优化版服务，提供缓存和批处理功能

## 功能特点

- 通过HTTP API更新DWG文件中的文本属性
- 支持WSL与Windows混合环境
- 自动检测和适配环境（WSL/Windows）
- 提供缓存机制，提高重复处理性能
- 支持批量处理多个DWG文件
- 提供健康检查API
- 错误处理和重试机制

## 系统架构

系统采用客户端-服务器架构：

- 服务端运行在Windows环境中，通过COM调用AutoCAD处理DWG文件
- 客户端可以运行在WSL环境中，通过HTTP API与服务端通信
- 优化服务作为中间层，提供缓存和批处理功能

```
[WSL环境]                      [Windows环境]
客户端应用 --> dwg_client --> 网络 --> dwg_service --> AutoCAD COM
               ^
               |
      dwg_service_optimized
```

## 安装与配置

### 前提条件

- Windows操作系统
- 已安装AutoCAD软件
- Python 3.6+
- 所需Python库：flask, waitress, pywin32, requests

### 环境变量配置

可以通过环境变量定制系统行为：

- `DWG_HOST_IP` - WSL环境中访问Windows主机的IP地址
- `DWG_SERVICE_URL` - 完整的服务URL（如不设置则使用自动检测）
- `DWG_SERVICE_KEY` - API密钥
- `DWG_REQUEST_TIMEOUT` - 请求超时时间（秒）
- `DWG_MAX_RETRIES` - 最大重试次数
- `DWG_MAX_WORKERS` - 并行处理的最大工作线程数
- `DWG_BATCH_SIZE` - 批处理的任务大小
- `DWG_USE_CACHE` - 是否使用缓存（true/false）

## 使用方法

### 启动服务端

在Windows环境中运行：

```
python dwg_service_simplified.py
```

服务将在端口5001上启动。

### 使用客户端

```python
from dwg_client_simplified import dwg_client

# 检查服务健康状态
success, result = dwg_client.check_health()
print(f"健康状态: {success}, 结果: {result}")

# 更新DWG文件属性
template_file = "path/to/template.dwg"
attribute_data = [
    {"field": "项目名称", "value": "绿色建筑示例项目"},
    {"field": "日期", "value": "2023-01-01"}
]

success, result = dwg_client.update_dwg_attributes(template_file, attribute_data)
if success:
    # 处理成功的结果
    file_data = result["file_data"]
    filename = result["filename"]
    # 保存文件或进一步处理
else:
    # 处理错误
    error_message = result["message"]
    print(f"更新失败: {error_message}")
```

### 使用优化服务

```python
from dwg_service_optimized_simplified import optimized_dwg_service

# 单个文件处理
success, result = optimized_dwg_service.update_attributes(
    'template.dwg',
    [{"field": "项目名称", "value": "绿色建筑示例项目"}]
)

# 批量处理
tasks = [
    ('template1.dwg', [{"field": "项目名称", "value": "项目1"}]),
    ('template2.dwg', [{"field": "项目名称", "value": "项目2"}]),
    ('template3.dwg', [{"field": "项目名称", "value": "项目3"}])
]
results = optimized_dwg_service.batch_update(tasks)

# 清空缓存
optimized_dwg_service.clear_cache()
```

## API接口说明

### 健康检查

- **URL**: `/api/health`
- **方法**: GET
- **返回**: 服务状态信息

### 更新DWG文件属性

- **URL**: `/api/dwg/update`
- **方法**: POST
- **请求头**: 
  - `X-API-KEY`: API密钥
- **请求体**:
  - `file`: DWG文件（multipart/form-data）
  - `data`: 属性数据JSON字符串
- **返回**: 
  - 成功: `{"success": true, "message": "更新成功", "filename": "output_xxx.dwg", "file_data": "base64编码的文件数据"}`
  - 失败: `{"success": false, "message": "错误信息"}`

## 注意事项

1. 服务端需运行在Windows环境，且已安装AutoCAD
2. 在WSL环境中使用时，需要正确设置Windows主机IP
3. 确保服务端有足够的权限运行AutoCAD
4. 处理大型DWG文件可能需要较长时间
5. 服务使用单线程模式避免COM冲突 