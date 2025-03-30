from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 用户角色：admin或user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)  # 最后在线时间
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
        
    def is_online(self):
        """检查用户是否在线（15分钟内有活动）"""
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < 900  # 15分钟 = 900秒

class InvitationCode(db.Model):
    __tablename__ = 'invitation_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    usage_count = db.Column(db.Integer, default=0)
    max_usage = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class LogRecord(db.Model):
    """系统日志记录模型"""
    __tablename__ = 'log_records'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR, etc.
    message = db.Column(db.Text, nullable=False)  # 日志消息
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 日志时间
    source = db.Column(db.String(100))  # 日志来源（模块、函数等）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 相关用户ID
    ip_address = db.Column(db.String(50))  # 操作者IP
    path = db.Column(db.String(255))  # 请求路径
    method = db.Column(db.String(10))  # 请求方法（GET, POST等）
    user_agent = db.Column(db.String(255))  # 用户代理
    
    @classmethod
    def add_log(cls, level, message, source=None, user_id=None, ip_address=None, path=None, method=None, user_agent=None):
        """添加一条日志记录"""
        log = cls(
            level=level,
            message=message,
            source=source,
            user_id=user_id,
            ip_address=ip_address,
            path=path,
            method=method,
            user_agent=user_agent
        )
        db.session.add(log)
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False