@echo off
chcp 65001
echo 绿色建筑评价系统 - Windows服务安装脚本
echo =========================================

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 请以管理员身份运行此脚本
    pause
    exit /b 1
)

REM 获取当前目录的绝对路径
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM 创建NSSM服务配置
echo 正在安装Windows服务...

REM 检查NSSM是否已安装
where nssm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo NSSM未安装，请先安装NSSM工具
    echo 下载地址: https://nssm.cc/download
    pause
    exit /b 1
)

REM 创建服务
nssm install GreenScoreService "%SCRIPT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%\server.py"
nssm set GreenScoreService DisplayName "绿色建筑评价系统"
nssm set GreenScoreService Description "绿色建筑评价系统服务"
nssm set GreenScoreService AppDirectory "%SCRIPT_DIR%"
nssm set GreenScoreService AppEnvironmentExtra "FLASK_ENV=production"
nssm set GreenScoreService Start SERVICE_AUTO_START
nssm set GreenScoreService ObjectName LocalSystem
nssm set GreenScoreService AppStdout "%SCRIPT_DIR%\logs\service_stdout.log"
nssm set GreenScoreService AppStderr "%SCRIPT_DIR%\logs\service_stderr.log"

echo 服务安装完成，正在启动服务...
net start GreenScoreService

if %ERRORLEVEL% neq 0 (
    echo 服务启动失败，请检查日志文件
) else (
    echo 服务已成功启动
    echo 服务名称: GreenScoreService
    echo 可以通过服务管理器管理此服务
)

pause 