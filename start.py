import os
import platform
import sys

def is_wsl():
    """检查是否在WSL环境中运行"""
    if sys.platform == 'linux':
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                return True
    return False

def start_server():
    """根据运行环境启动合适的服务器"""
    if platform.system() == 'Windows':
        # Windows环境使用waitress
        from waitress import serve
        from app import app
        print("在Windows环境下使用Waitress服务器启动...")
        serve(app, host='0.0.0.0', port=5050)
    else:
        # WSL或其他Linux环境使用gunicorn
        if is_wsl():
            print("在WSL环境下使用Gunicorn服务器启动...")
        else:
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
            'bind': '0.0.0.0:5050',
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