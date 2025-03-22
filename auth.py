import bcrypt
from sqlalchemy import create_engine, text
import os
import urllib.parse
from loguru import logger

def get_db_connection():
    """获取数据库连接"""
    server = os.environ.get('SQLSERVER_SERVER', 'acbim.fun')
    database = os.environ.get('SQLSERVER_DATABASE', '绿色建筑')
    username = os.environ.get('SQLSERVER_USERNAME', 'test')
    password = os.environ.get('SQLSERVER_PASSWORD', '123456')
    driver = os.environ.get('SQLSERVER_DRIVER', '{SQL Server}')
    
    db_uri = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={urllib.parse.quote_plus(driver)}"
    return create_engine(db_uri)

def hash_password(password):
    """对密码进行加密"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def authenticate_user(username, password):
    """验证用户身份"""
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            # 查询用户
            result = conn.execute(
                text("SELECT id, username, password FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            
            if result and verify_password(password, result.password.encode('utf-8')):
                return {'id': result.id, 'username': result.username}
            return None
    except Exception as e:
        logger.error(f"用户认证失败: {str(e)}")
        return None

def update_last_login(user_id):
    """更新用户最后登录时间"""
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET last_login = GETDATE() WHERE id = :user_id"),
                {"user_id": user_id}
            )
    except Exception as e:
        logger.error(f"更新最后登录时间失败: {str(e)}")