import os
import sys
import platform

# 打开日志文件
log_file = open('environment_test.log', 'w')

def log(message):
    """同时输出到控制台和日志文件"""
    print(message)
    log_file.write(message + '\n')
    log_file.flush()

# 检查是否在WSL环境中
def is_wsl():
    """检查当前是否在WSL环境中运行"""
    is_wsl_env = 'WSL' in platform.uname().release or \
         (os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower())
    return is_wsl_env

# 检查是否在Windows环境中
def is_windows():
    """检查当前是否在Windows环境中运行"""
    return platform.system() == 'Windows'

# 主测试函数
def test_environment():
    """测试当前环境和DWG处理模块"""
    log("=" * 50)
    log(" 环境和DWG处理模块测试")
    log("=" * 50)
    
    # 检查操作系统
    log(f"操作系统: {platform.system()}")
    log(f"平台: {platform.platform()}")
    log(f"Python版本: {platform.python_version()}")
    
    # 检查WSL环境
    wsl = is_wsl()
    log(f"是否在WSL环境中: {wsl}")
    
    # 检查Windows环境
    windows = is_windows()
    log(f"是否在Windows环境中: {windows}")
    
    # 检查DWG处理模块
    log("\n正在检查DWG处理模块...")
    
    if windows:
        log("Windows环境，检查本地AutoCAD处理模块...")
        try:
            from update_dwg_attribute import update_attribute_text
            log("✓ 已加载Windows本地AutoCAD处理模块")
            
            # 检查是否可以访问AutoCAD COM对象
            try:
                import win32com.client
                log("尝试连接AutoCAD...")
                acad = win32com.client.Dispatch("AutoCAD.Application")
                log("✓ 已成功连接到AutoCAD")
                acad = None
            except Exception as e:
                log(f"✗ 无法连接到AutoCAD: {str(e)}")
        except ImportError:
            log("✗ 未安装Windows本地AutoCAD处理模块")
            log("  请确保已安装pywin32模块")
    
    if wsl:
        log("\nWSL环境，检查DWG客户端模块...")
        try:
            from dwg_client import dwg_client, IS_WSL
            log(f"✓ 已加载DWG客户端模块，WSL环境检测结果: {IS_WSL}")
            
            # 检查DWG服务连接
            log("检查DWG服务连接...")
            health_ok, result = dwg_client.check_health()
            if health_ok:
                log(f"✓ DWG服务连接正常: {result}")
            else:
                log(f"✗ DWG服务连接失败: {result}")
                
            # 获取DWG服务URL
            log(f"当前DWG服务URL: {dwg_client.api_url}")
            
            # 检查环境变量
            host_ip = os.environ.get('DWG_HOST_IP')
            log(f"DWG_HOST_IP环境变量: {host_ip or '未设置'}")
        except ImportError:
            log("✗ 未安装DWG客户端模块")
    
    log("\n总结:")
    if windows and not wsl:
        log("当前是纯Windows环境，应使用本地AutoCAD处理DWG文件")
    elif wsl and not windows:
        log("当前是纯WSL环境，应使用DWG客户端连接Windows主机处理DWG文件")
    elif wsl and windows:
        log("当前环境同时具有WSL和Windows特性，应优先使用本地AutoCAD处理")
    else:
        log("当前环境既不是Windows也不是WSL，不支持DWG处理")

if __name__ == "__main__":
    try:
        test_environment()
    finally:
        log("\n测试完成！")
        log(f"详细日志已保存到 {os.path.abspath('environment_test.log')}")
        log_file.close() 