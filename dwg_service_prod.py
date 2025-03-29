from flask import Flask, request, jsonify
import win32com.client
import pythoncom
import os
import traceback
import json
import uuid
import base64
import logging
import time
import hashlib
from logging.handlers import RotatingFileHandler
from functools import lru_cache
from waitress import serve

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dwg_service')
handler = RotatingFileHandler('dwg_service.log', maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
CACHE_FOLDER = 'dwg_cache'
SECRET_KEY = '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85'  # 用于API认证
MAX_CACHE_SIZE = 50  # 最大缓存条目数
PORT = 5001  # 服务端口

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# 从dwg_service.py导入所有现有功能
from dwg_service import DwgFileCache, update_dwg_attribute, restart_autocad, api_update_dwg, health_check

# 添加健康检查接口
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'dwg-service',
        'version': '1.0-production'
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print(" DWG服务 - 生产环境版本")
    print("=" * 50)
    
    # 初始化COM环境
    try:
        pythoncom.CoInitialize()
        logger.info("COM环境初始化成功")
    except Exception as e:
        logger.error(f"COM环境初始化失败: {str(e)}")
    
    try:
        # 设置适当的权限
        import win32api
        import win32con
        import win32security
        
        # 提升进程权限
        logger.info("尝试提升进程权限")
        handle = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY)
        win32security.AdjustTokenPrivileges(
            handle, 0, [(win32security.LookupPrivilegeValue(None, "SeDebugPrivilege"), win32con.SE_PRIVILEGE_ENABLED)]
        )
        logger.info("进程权限已提升")
    except Exception as e:
        logger.warning(f"提升进程权限失败: {str(e)}")
    
    # 尝试预启动AutoCAD以避免第一次请求超时
    try:
        logger.info("尝试预启动AutoCAD")
        acad = win32com.client.Dispatch("AutoCAD.Application")
        logger.info("AutoCAD已预启动")
        
        # 释放引用但不关闭AutoCAD
        acad = None
        import gc
        gc.collect()
        logger.info("AutoCAD引用已释放")
    except Exception as e:
        logger.warning(f"预启动AutoCAD失败: {str(e)}")
        # 尝试重启AutoCAD
        restart_autocad()
    
    # 使用waitress提供生产级别服务
    print(f"服务已启动，在 http://0.0.0.0:{PORT} 监听")
    print("按 Ctrl+C 停止服务")
    serve(app, host='0.0.0.0', port=PORT, threads=1)  # 使用单线程模式避免COM冲突 