import os
import urllib.parse

# 基础配置
SECRET_KEY = 'your-secret-key'  # 请更改为随机的密钥
DEBUG = True

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # 默认数据库连接配置
    server = os.environ.get('SQLSERVER_SERVER', 'acbim.fun')
    database = os.environ.get('SQLSERVER_DATABASE', '绿色建筑')
    username = os.environ.get('SQLSERVER_USERNAME', 'test')
    password = os.environ.get('SQLSERVER_PASSWORD', '123456')
    driver = os.environ.get('SQLSERVER_DRIVER', '{SQL Server}')
    
    # 对驱动进行URL编码
    encoded_driver = urllib.parse.quote_plus(driver)
    
    # 构建连接字符串
    DATABASE_URL = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={encoded_driver}'

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 会话配置
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800  # 30分钟

# 上传文件配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB