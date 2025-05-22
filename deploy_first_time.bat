@echo off
:: GreenScore项目首次部署脚本

echo 正在检查 Python 环境...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 错误：未找到 Python。请确保已安装 Python 并已添加到系统 PATH。
    echo 脚本将退出。
    goto end
)
echo Python 环境检查通过。

echo 正在检查或创建虚拟环境 (.venv)...
IF NOT EXIST .venv (
    echo 虚拟环境不存在，正在创建...
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo 错误：创建虚拟环境失败。
        echo 脚本将退出。
        goto end
    )
    echo 虚拟环境创建成功。
) ELSE (
    echo 虚拟环境已存在。
)

echo 正在激活虚拟环境并安装依赖...
:: 激活虚拟环境
call .venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    echo 错误：激活虚拟环境失败。
    echo 脚本将退出。
    goto end
)

echo 虚拟环境已激活。

:: 安装依赖
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo 错误：安装依赖失败。请检查 requirements.txt 文件或网络连接。
    echo 脚本将退出。
    goto end
)

echo 依赖安装成功。

echo 项目首次部署基本完成。
echo 您现在可以运行数据库初始化脚本（例如 init_db.py 或 init_mysql_db.py），然后运行 start_win.bat 来启动项目。

:end
echo 脚本执行完毕。
pause 