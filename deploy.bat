@echo off
chcp 65001
echo 绿色建筑评价系统 - 生产环境部署脚本
echo ======================================

REM 创建必要的目录
if not exist logs mkdir logs
if not exist cache mkdir cache

REM 检查是否存在.env文件
if not exist .env (
    echo 警告: .env文件不存在，将使用默认配置
    echo 建议从.env.example创建.env文件并配置环境变量
    copy .env.example .env
)

REM 安装依赖
echo 正在安装依赖...
pip install --user -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 安装依赖失败，请检查网络连接和requirements.txt文件
    pause
    exit /b 1
)

REM 设置环境变量
set FLASK_ENV=production

REM 启动服务器
echo 正在启动生产服务器...
python server.py

pause 