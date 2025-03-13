import os
from waitress import serve
from app import app
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('waitress')

if __name__ == '__main__':
    # 设置为生产环境
    os.environ['FLASK_ENV'] = 'production'
    
    # 获取端口，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 输出启动信息
    logger.info(f"启动生产服务器 - 端口: {port}")
    
    # 使用Waitress服务器
    serve(app, host='0.0.0.0', port=port, threads=4) 