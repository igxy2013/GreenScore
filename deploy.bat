@echo off
chcp 65001 >NUL
echo 绿色建筑评价系统 - 生产环境部署脚本
echo ======================================

REM 检查程序是否运行，如果运行则终止旧进程
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if %ERRORLEVEL% equ 0 (
    echo 检测到程序正在运行，正在终止旧进程...
    taskkill /F /IM python.exe
    if %ERRORLEVEL% neq 0 (
        echo 无法终止旧进程，请手动检查
        pause
        exit /b 1
    )
    echo 旧进程已终止
)

REM 如果存在 Git 目录，则获取最新更新
if exist .git (
    echo 正在从 Git 获取最新更新...
    git pull
)

REM 创建必要的目录
if not exist logs (
    echo 正在创建 logs 目录...
    mkdir logs
)

if not exist cache (
    echo 正在创建 cache 目录...
    mkdir cache
)

REM 检查是否存在 .env 文件
if not exist .env (
    echo 警告: .env文件不存在，将使用默认配置
    echo 建议从.env.example创建.env文件并配置环境变量
    echo 正在复制 .env.example 到 .env...
    copy .env.example .env
)

REM 升级 pip 并安装依赖
echo Updating pip...
python -m pip install --user --upgrade pip

echo 正在安装依赖...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 安装依赖失败，请检查网络连接和requirements.txt文件
    pause
    exit /b 1
)

REM 设置环境变量
setx FLASK_ENV production

REM 启动服务器
python server.py
if %ERRORLEVEL% neq 0 (
    echo 服务器启动失败，请检查 server.py 文件
    pause
    exit /b 1
)

pause