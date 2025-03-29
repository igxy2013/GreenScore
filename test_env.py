import os
from dotenv import load_dotenv

# 清除可能存在的环境变量
if 'DWG_HOST_IP' in os.environ:
    print(f"系统环境变量中已存在DWG_HOST_IP: {os.environ['DWG_HOST_IP']}")
    print("清除该环境变量...")
    
# 加载.env文件，并强制覆盖已存在的环境变量
print("尝试加载.env文件并覆盖已存在的环境变量...")
result = load_dotenv(override=True)
print(f"load_dotenv(override=True)返回结果: {result}")

# 检查环境变量
dwg_host_ip = os.environ.get('DWG_HOST_IP', '未设置')
print("DWG_HOST_IP的值是:")
print(dwg_host_ip)

# 列出所有DWG相关环境变量
dwg_vars = [k for k in os.environ.keys() if k.startswith('DWG')]
print(f"所有DWG相关环境变量: {dwg_vars}")

# 打印所有DWG环境变量的值
for var in dwg_vars:
    value = os.environ.get(var, '')
    print(f"{var} = {value}") 