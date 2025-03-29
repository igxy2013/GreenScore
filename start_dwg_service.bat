::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFDpQQQ2MNXiuFLQI5/rH3+OEtlgPUfEDS5rV6LGeL/IHpEznevY=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCuDJGm9yGUiLR5afweNLm6GAqIb1/v+/fyOoUhTUfo6GA==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
chcp 65001 > nul
echo ===============================================
echo       DWG服务 - 生产环境启动脚本
echo ===============================================

REM 确保目录存在
if not exist "logs" mkdir logs

echo 正在启动DWG服务，请稍�?..
echo 日志文件保存�?logs\dwg_service.log

REM 启动服务
start "DWG服务" /min python dwg_service_prod.py

echo 服务已在后台启动
echo 可通过 http://localhost:5001/api/health 检查状�?
echo.
echo 要停止服务，请关闭对应的命令窗口或任务管理器中的Python进程
echo.

timeout /t 3 >nul

REM 尝试打开健康检查页�?
start http://localhost:5001/api/health

pause 