@echo off
echo ===============================================
echo       DWG服务 - 生产环境启动脚本
echo ===============================================

REM 确保目录存在
if not exist "logs" mkdir logs

echo 正在启动DWG服务，请稍候...
echo 日志文件保存在 logs\dwg_service.log

REM 启动服务
start "DWG服务" /min python dwg_service_prod.py

echo 服务已在后台启动
echo 可通过 http://localhost:5001/api/health 检查状态
echo.
echo 要停止服务，请关闭对应的命令窗口或任务管理器中的Python进程
echo.

timeout /t 3 >nul

REM 尝试打开健康检查页面
start http://localhost:5001/api/health

pause 