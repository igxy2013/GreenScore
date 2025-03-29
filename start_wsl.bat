@echo off
chcp 65001 
echo 正在WSL环境中启动服务...
wsl bash -c "cd '$(wslpath -a .)' && source venv/bin/activate && python start.py"
echo 如果服务已成功启动，请访问 http://localhost:5050
pause