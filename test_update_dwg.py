import os
import sys
from dwg_client import dwg_client
import logging

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG)

# 查找一个可用的DWG文件
def find_dwg_file():
    """在项目中寻找第一个可用的DWG文件"""
    templates_dir = os.path.join('static', 'templates')
    if os.path.exists(templates_dir):
        for file in os.listdir(templates_dir):
            if file.lower().endswith('.dwg'):
                return os.path.join(templates_dir, file)
    
    # 如果没有找到，返回None
    return None

# 主测试函数
def test_update_dwg():
    # 修改服务器地址为本地地址
    print("将服务器地址修改为本地127.0.0.1...")
    original_url = dwg_client.api_url
    dwg_client.api_url = "http://127.0.0.1:5001"
    print(f"修改后的DWG服务URL: {dwg_client.api_url}")
    
    # 首先测试服务健康状态
    print("正在检查DWG服务健康状态...")
    health_ok, health_result = dwg_client.check_health()
    if not health_ok:
        print(f"DWG服务健康检查失败: {health_result.get('message', '未知错误')}")
        return
    
    print(f"DWG服务健康检查通过: {health_result}")
    
    # 查找测试文件
    dwg_file = find_dwg_file()
    if not dwg_file:
        print("未找到可用的DWG测试文件，请确保static/templates目录中有.dwg文件")
        return
    
    print(f"使用测试文件: {dwg_file}")
    
    # 准备简单的测试数据
    test_data = [
        {"field": "项目名称", "value": "测试项目"},
        {"field": "项目编号", "value": "TEST-001"}
    ]
    
    # 调用更新方法
    print(f"正在调用update_dwg_attributes方法...")
    success, result = dwg_client.update_dwg_attributes(dwg_file, test_data)
    
    # 检查结果
    if success:
        print("测试成功!")
        print(f"结果信息: {result.get('message', '')}")
        print(f"文件名: {result.get('filename', '')}")
        print(f"获取到的文件数据大小: {len(result.get('file_data', '')) if 'file_data' in result else '无数据'}")
    else:
        print(f"测试失败: {result.get('message', '未知错误')}")
    
    # 恢复原始URL
    dwg_client.api_url = original_url

if __name__ == "__main__":
    test_update_dwg() 