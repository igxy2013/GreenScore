::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCuDJGm9yGUiLR5afweNLm6GFaEd/OH40+OKo0oYaOUtfYrVybeBMuVe5kKqfJUitg==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSjk=
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
::Zh4grVQjdCuDJGm9yGUiLR5afweNLm6GIacZ7ebI7OWVpwAqZ85ya4rJzLGcbuUL7yU=
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
chcp 65001 > nul

:: 1. 拉取最新代码
git pull
if errorlevel 1 (
echo [错误] Git 拉取失败，请检查网络或仓库权限�?
)

:: 2. 启动WSL中的MySQL
echo 正在启动WSL中的MySQL...
wsl -u root service mysql start --no-pager
if errorlevel 1 (
echo [错误] MySQL 启动失败，请检查是否已安安装MySQL?
wsl -u root service mysql status
pause
exit /b
)

:: 3. 获取当前目录的WSL路径
for /f "delims=" %%A in ('wsl wslpath -a "%cd%"') do set WSL_PATH=%%A

:: 4. 启动Python服务
echo 正在WSL环境中启动服务...
wsl -d Ubuntu -e bash -c "cd '%WSL_PATH%' && source venv/bin/activate && python start.py"
echo 如果服务已成功启动，请访问http://localhost:5050
pause