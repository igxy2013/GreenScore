# GreenScore

## 项目描述

本项目GreenScore似乎是一个用于环境评分或材料管理的Web应用。通过分析项目文件，它可能涉及以下功能：

- 材料分类和聚合 (`classify_and_aggregate_materials.py`)
- 生成公共交通分析报告 (`generate_transport_report.py`)
- 处理自定义占位符 (`process_custom_placeholders.py`)
- 更新DWG属性 (`update_dwg_attribute.py`)
- 数据导出 (`export.py`)
- 用户注册 (`register.py`)
- 项目列表 (`list_projects.py`)
- 数据库初始化 (`init_db.py`, `init_mysql_db.py`)
- Web界面 (`app.py`, `static/`, `templates/`)

## 环境要求

项目可能需要以下环境和依赖：

- Python 3.x
- 数据库 (例如 MySQL，根据 `init_mysql_db.py`)
- Python 包依赖 (详见 `requirements.txt`)
- 可能需要其他系统依赖用于处理DWG文件等。

## 安装步骤

1.  **克隆仓库**：
    ```bash
    git clone <您的仓库地址>
    cd GreenScore
    ```

2.  **创建并激活虚拟环境**：
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    
    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

4.  **设置环境变量**：
    复制 `.env.example` 文件为 `.env` 并根据您的环境配置。
    ```bash
    copy .env.example .env
    # 或 for Linux/macOS
    cp .env.example .env
    ```
    编辑 `.env` 文件，填写数据库连接信息等。

5.  **初始化数据库**：
    根据您使用的数据库，运行相应的初始化脚本。
    ```bash
    python init_db.py
    # 或 python init_mysql_db.py
    ```

## 运行项目

激活虚拟环境后，运行主应用文件：

```bash
python app.py
```

或者，如果您使用 `start.py` 或 `start_win.bat`：

```bash
python start.py
# 或 start_win.bat
```

项目将在本地服务器上运行，通常地址是 `http://127.0.0.1:5000` (如果使用 Flask)。

## 文件结构说明

-   `src/`: 核心源代码
-   `static/`: 静态文件 (CSS, JS, images等)
-   `templates/`: HTML 模板文件
-   `utils/`: 工具函数
-   `test/`: 测试文件
-   `docs/`: 文档 (如果存在)

## 许可证

请在此处说明项目的许可证信息。

## 贡献

欢迎贡献！

## 联系方式

如果您有任何问题或建议，请通过acbim@qq.com联系我。
