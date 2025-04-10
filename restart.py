import os
import time

# 尝试停止所有Python进程
try:
    os.system('taskkill /F /IM python.exe')
    print("已尝试停止所有Python进程")
    time.sleep(1)
except Exception as e:
    print(f"停止进程时出错: {e}")

# 启动Flask应用
try:
    os.system('start cmd /k python app.py')
    print("已启动Flask应用")
except Exception as e:
    print(f"启动应用时出错: {e}") 