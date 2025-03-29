import os
import urllib.parse

# 基础配置
SECRET_KEY = '5c72fbbfc4e446aa7bc28c81348b35a6c264b83b47768a9dec768d7a26b2ea85'  # 请更改为随机的密钥
DEBUG = True

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # MySQL数据库连接配置
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_database = os.environ.get('MYSQL_DATABASE', '绿色建筑')
    mysql_username = os.environ.get('MYSQL_USERNAME', 'mysql')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '12345678')
    
    # 构建MySQL连接字符串
    # 对中文数据库名进行URL编码
    encoded_database = urllib.parse.quote(mysql_database)
    DATABASE_URL = f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/{encoded_database}'

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 数据库连接池配置
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,           # 连接池大小
    'max_overflow': 5,         # 超过池大小的最大连接数
    'pool_timeout': 30,        # 连接超时(秒)
    'pool_recycle': 1800       # 连接回收时间(秒)
}

# 会话配置
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800  # 30分钟

# 上传文件配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件限制为16MB