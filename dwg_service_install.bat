@echo off
chcp 65001 > nul
echo ===============================================
echo       DWG服务安装程序
echo ===============================================

REM 检查管理员权限
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo 需要管理员权限!
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /B 1
)

echo 正在安装必要组件...

REM 检查Python是否已安装
python --version 2>NUL
if errorlevel 1 (
    echo 未检测到Python，请安装Python 3.7或更高版本
    pause
    exit /B 1
)

REM 检查是否存在编译所需的Visual C++
echo 检查Visual C++构建工具...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0" >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告：未检测到Visual C++构建工具，将跳过需要编译的包
    echo 请先安装Visual C++构建工具：https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo 然后再尝试安装pyodbc等需要编译的包
    set SKIP_COMPILE=1
) else (
    set SKIP_COMPILE=0
)

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
    echo 虚拟环境已创建
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装NSSM（Non-Sucking Service Manager）
if not exist "nssm.exe" (
    echo 正在下载NSSM工具...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.'" -Force
    copy "nssm-2.24\win64\nssm.exe" "nssm.exe"
    rd /s /q "nssm-2.24"
    del "nssm.zip"
)

REM 安装依赖
echo 正在安装Python依赖...
if "%SKIP_COMPILE%"=="1" (
    echo 跳过需要编译的包，安装基本依赖...
    pip install waitress flask
) else (
    pip install -r requirements.txt
)

REM 确保目录存在
if not exist "logs" mkdir logs

REM 创建服务
echo 正在创建Windows服务...
set PYTHON_EXE=%cd%\venv\Scripts\python.exe
set SCRIPT_PATH=%cd%\dwg_service_prod.py

echo 服务配置:
echo Python解释器: %PYTHON_EXE%
echo 脚本路径: %SCRIPT_PATH%
echo 工作目录: %cd%

nssm.exe install DWGService "%PYTHON_EXE%" "%SCRIPT_PATH%"
if %errorlevel% neq 0 (
    echo 服务创建失败！尝试使用绝对路径...
    nssm.exe install DWGService "%PYTHON_EXE%" "%SCRIPT_PATH%"
    if %errorlevel% neq 0 (
        echo 服务创建失败！尝试使用直接安装方式...
        nssm.exe install DWGService "python" "%SCRIPT_PATH%"
    )
)

echo 设置服务参数...
nssm.exe set DWGService DisplayName "DWG服务"
nssm.exe set DWGService Description "AutoCAD DWG文件处理服务"
nssm.exe set DWGService AppDirectory "%cd%"
nssm.exe set DWGService AppStdout "%cd%\logs\service_stdout.log"
nssm.exe set DWGService AppStderr "%cd%\logs\service_stderr.log"
nssm.exe set DWGService Start SERVICE_AUTO_START

echo 服务配置完成！
echo.
echo 服务名称: DWGService
echo 服务描述: AutoCAD DWG文件处理服务
echo 服务路径: %SCRIPT_PATH%
echo.
echo 您可以在Windows服务管理器中管理此服务
echo 或使用以下命令:
echo   启动服务: net start DWGService
echo   停止服务: net stop DWGService
echo   删除服务: nssm.exe remove DWGService
echo.

choice /C YN /M "是否立即启动服务？"
if errorlevel 2 goto END
if errorlevel 1 goto START

:START
echo 正在启动服务...
net start DWGService
if %errorlevel% neq 0 (
    echo 服务启动失败！请检查以上错误信息。
    echo 您可以尝试使用start_dwg_service.bat直接启动服务。
) else (
    echo 服务已启动，可通过 http://localhost:5001/api/health 检查状态
)

:END
REM 取消激活虚拟环境
deactivate
pause 