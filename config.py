import os
import urllib.parse

# 基础配置
SECRET_KEY = 'your-secret-key'  # 请更改为随机的密钥
DEBUG = True

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # 默认数据库连接配置
    server = 'acbim.fun'
    database = '绿色建筑'
    username = 'test'
    password = 'test'
    
    # 对密码进行URL编码
    encoded_password = urllib.parse.quote_plus(password)
    
    # 构建连接字符串
    DATABASE_URL = f'mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 会话配置
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800  # 30分钟

# 上传文件配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 