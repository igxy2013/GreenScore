import os
from dwg_client import dwg_client

# 测试本地连接
local_success, local_result = dwg_client.check_health()
print(f"本地连接 (127.0.0.1) 健康检查结果: {local_success}")
print(f"详细信息: {local_result}")

# 测试IP地址连接
print("\n正在测试IP地址连接...")
# 记住当前的api_url
original_url = dwg_client.api_url
# 更改为使用IP地址
ip_url = "http://192.168.0.80:5001"
dwg_client.api_url = ip_url
print(f"使用IP地址: {ip_url}")

ip_success, ip_result = dwg_client.check_health()
print(f"IP地址连接 (192.168.0.80) 健康检查结果: {ip_success}")
print(f"详细信息: {ip_result}")

# 恢复原始设置
dwg_client.api_url = original_url 