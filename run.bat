@echo off
chcp 65001 >NUL
echo 绿色建筑评价系统 - 启动脚本
echo ======================================

REM 设置错误级别检查
setlocal EnableDelayedExpansion
set "ERROR_LEVEL=0"

REM 检查Python是否安装
echo [信息] 检查Python环境...
python --version >logs\python_version.log 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到Python环境，请确保已安装Python并添加到系统环境变量中
    echo 详细信息请查看 logs\python_version.log
    set "ERROR_LEVEL=1"
    pause
    exit /b !ERROR_LEVEL!
)
echo [成功] Python环境检查通过

REM 创建日志目录
echo [信息] 检查日志目录...
if not exist logs (
    echo [信息] 创建日志目录...
    mkdir logs
    if !ERRORLEVEL! neq 0 (
        echo [错误] 创建日志目录失败
        set "ERROR_LEVEL=1"
        pause
        exit /b !ERROR_LEVEL!
    )
)
echo [成功] 日志目录检查/创建完成

REM 检查是否在WSL环境中
echo [信息] 检查运行环境...
wsl.exe echo > NUL 2>&1
if %ERRORLEVEL% equ 0 (
    echo [信息] 检测到WSL环境，使用WSL模式启动...
    
    REM 在WSL中执行Python命令
    echo [信息] 在WSL环境中执行命令...
    wsl.exe bash -c "cd $(wslpath '%~dp0') && \
        if [ ! -d 'venv' ]; then \
            echo '[信息] 创建Python虚拟环境...' && \
            python3 -m venv venv; \
            if [ $? -ne 0 ]; then \
                echo '[错误] 创建虚拟环境失败'; \
                exit 1; \
            fi; \
        fi && \
        source venv/bin/activate && \
        echo '[信息] 安装依赖...' && \
        pip install -r requirements.txt > logs/pip_install.log 2>&1 && \
        echo '[成功] 依赖安装完成' && \
        echo '[信息] 启动应用...' && \
        python start.py 2>&1 | tee logs/app.log"
    if !ERRORLEVEL! neq 0 (
        echo [错误] 应用启动失败，请查看logs目录下的日志文件
        type logs\app.log
        set "ERROR_LEVEL=1"
        pause
        exit /b !ERROR_LEVEL!
    )
    echo [成功] 应用在WSL环境中启动成功
) else (
    echo [信息] 检测到Windows环境，使用Windows模式启动...
    
    REM 检查虚拟环境是否存在，不存在则创建
    if not exist venv (
        echo [信息] 创建Python虚拟环境...
        python -m venv venv
        if !ERRORLEVEL! neq 0 (
            echo [错误] 创建虚拟环境失败
            set "ERROR_LEVEL=1"
            pause
            exit /b !ERROR_LEVEL!
        )
        echo [成功] 虚拟环境创建完成
    ) else (
        echo [信息] 虚拟环境已存在
    )
    
    REM 激活虚拟环境
    echo [信息] 激活虚拟环境...
    call venv\Scripts\activate.bat
    if !ERRORLEVEL! neq 0 (
        echo [错误] 激活虚拟环境失败
        set "ERROR_LEVEL=1"
        pause
        exit /b !ERROR_LEVEL!
    )
    echo [成功] 虚拟环境激活完成
    
    REM 安装依赖
    echo [信息] 检查并安装依赖...
    echo [信息] 开始安装依赖...
    pip install -r requirements.txt > logs\pip_install.log 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [错误] 安装依赖失败
        echo 详细信息请查看 logs\pip_install.log
        type logs\pip_install.log
        set "ERROR_LEVEL=1"
        pause
        exit /b !ERROR_LEVEL!
    )
    echo [成功] 依赖安装完成
    
    REM 启动应用
    echo [信息] 启动应用...
    echo [信息] 正在启动应用...
    python start.py > logs\app.log 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [错误] 应用启动失败
        echo 详细信息请查看 logs\app.log
        type logs\app.log
        set "ERROR_LEVEL=1"
        pause
        exit /b !ERROR_LEVEL!
    )
    echo [成功] 应用启动成功
)

pause