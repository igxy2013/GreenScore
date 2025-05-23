import os
import platform
import sys
import logging
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 配置日志
# 确保logs文件夹存在
if not os.path.exists('logs'):
    os.makedirs('logs')
    logger.info("Created logs directory")

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库并创建管理员用户（如果不存在）"""
    from app import app
    from models import db, User
    
    try:
        with app.app_context():
            # 初始化数据库
            db.create_all()
            logger.info("数据库表已创建")
            
            # 检查是否需要创建管理员用户
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = User()
                admin.username = 'admin'
                admin.email = 'admin@example.com'
                admin.set_password('admin123')
                admin.role = 'admin'
                db.session.add(admin)
                db.session.commit()
                logger.info("已创建默认管理员用户")
    except Exception as e:
        logger.error(f"初始化数据库时出错: {str(e)}")
        raise

def start_server():
    """根据运行环境启动合适的服务器"""
    # 先初始化数据库
    init_database()
    
    # 从环境变量获取端口号，默认为 5050
    port = int(os.getenv('SERVER_PORT', '5050'))
    logger.info(f"服务器将在端口 {port} 上启动...")
    print(f"服务器将在端口 {port} 上启动...")

    if platform.system() == 'Windows':
        # Windows环境使用waitress
        from waitress import serve
        from app import app
        logger.info("在Windows环境下使用Waitress服务器启动...")
        print("在Windows环境下使用Waitress服务器启动...")
        # 增加线程数和其他配置参数，优化Waitress性能
        serve(
            app, 
            host='0.0.0.0', 
            port=port,              # 使用从环境变量获取的端口
            threads=32,               # 增加线程数量，处理更多并发请求
            connection_limit=1000,    # 增加连接限制
            channel_timeout=300,      # 设置通道超时时间
            cleanup_interval=30,      # 设置清理间隔
            max_request_header_size=16384,  # 增加请求头大小限制
            max_request_body_size=1073741824,  # 增加请求体大小限制(1GB)
            clear_untrusted_proxy_headers=True,  # 清除不信任的代理头
            url_scheme='http'         # 设置URL方案
        )
    else:
        # Linux环境使用gunicorn
        logger.info("在Linux环境下使用Gunicorn服务器启动...")
        print("在Linux环境下使用Gunicorn服务器启动...")
        
        # 确保logs目录存在
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 使用gunicorn启动
        import gunicorn.app.base
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                         if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        from app import app
        
        options = {
            'bind': f'0.0.0.0:{port}', # 使用从环境变量获取的端口
            'workers': 3,
            'worker_class': 'sync',
            'threads': 4,
            'timeout': 300,
            'accesslog': 'logs/gunicorn_access.log',
            'errorlog': 'logs/gunicorn_error.log',
            'loglevel': 'info'
        }
        
        StandaloneApplication(app, options).run()

if __name__ == '__main__':
    start_server()