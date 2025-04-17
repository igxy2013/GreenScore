from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # 添加用户ID字段
    name = db.Column(db.String(100), nullable=False)  # 项目名称
    code = db.Column(db.String(50))  # 项目编号
    construction_unit = db.Column(db.String(100))  # 建设单位
    design_unit = db.Column(db.String(100))  # 设计单位
    location = db.Column(db.String(200))  # 项目地点
    building_area = db.Column(db.Float)  # 建筑面积
    standard = db.Column(db.String(20))  # 评价标准
    building_type = db.Column(db.String(50))  # 建筑类型
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # 新增字段
    climate_zone = db.Column(db.String(10))  # 建筑气候区划
    star_rating_target = db.Column(db.String(10))  # 星级目标
    total_land_area = db.Column(db.Float)  # 总用地面积
    total_building_area = db.Column(db.Float)  # 总建筑面积
    above_ground_area = db.Column(db.Float)  # 地上建筑面积
    underground_area = db.Column(db.Float)  # 地下建筑面积
    building_height = db.Column(db.Float)  # 建筑高度
    building_floors = db.Column(db.String(20))  # 建筑层数（地上/地下）
    underground_floor_area = db.Column(db.Float)  # 地下一层建筑面积
    ground_parking_spaces = db.Column(db.Integer)  # 地面停车位数量
    plot_ratio = db.Column(db.Float)  # 容积率
    building_base_area = db.Column(db.Float)  # 建筑基底面积
    building_density = db.Column(db.Float)  # 建筑密度
    green_area = db.Column(db.Float)  # 绿地面积
    green_ratio = db.Column(db.Float)  # 绿地率
    residential_units = db.Column(db.Integer)  # 住宅户数
    air_conditioning_type = db.Column(db.String(50))  # 空调形式
    average_floors = db.Column(db.String(50))  # 住宅平均层数
    has_garbage_room = db.Column(db.String(10))  # 有无垃圾用房
    has_elevator = db.Column(db.String(10))  # 有无电梯或扶梯
    has_underground_garage = db.Column(db.String(10))  # 有无地下车库
    construction_type = db.Column(db.String(50))  # 项目建设情况
    has_water_landscape = db.Column(db.String(10))  # 有无景观水体
    is_fully_decorated = db.Column(db.String(10))  # 是否为全装修项目
    public_building_type = db.Column(db.String(50))  # 公建类型
    public_green_space = db.Column(db.String(10))  # 绿地向公众开放
    status = db.Column(db.String(20), default='规划中')  # 项目状态：规划中、进行中、已完成、已暂停等
    
    # 新增评分字段（使用英文字段名）
    architecture_score = db.Column(db.Float)  # 建筑总分
    structure_score = db.Column(db.Float)  # 结构总分
    water_supply_score = db.Column(db.Float)  # 给排水总分
    electrical_score = db.Column(db.Float)  # 电气总分
    hvac_score = db.Column(db.Float)  # 暖通总分
    landscape_score = db.Column(db.Float)  # 景观总分
    env_health_energy_score = db.Column(db.Float)  # 环境健康与节能总分
    env_health_energy_innovation_score = db.Column(db.Float)  # 环境健康与节能创新总分
    architecture_innovation_score = db.Column(db.Float)  # 建筑创新总分
    structure_innovation_score = db.Column(db.Float)  # 结构创新总分
    hvac_innovation_score = db.Column(db.Float)  # 暖通创新总分
    landscape_innovation_score = db.Column(db.Float)  # 景观创新总分
    safety_durability_score = db.Column(db.Float)  # 安全耐久总分
    health_comfort_score = db.Column(db.Float)  # 健康舒适总分
    life_convenience_score = db.Column(db.Float)  # 生活便利总分
    resource_saving_score = db.Column(db.Float)  # 资源节约总分
    environment_livability_score = db.Column(db.Float)  # 环境宜居总分
    improvement_innovation_score = db.Column(db.Float)  # 提高与创新总分
    total_score = db.Column(db.Float)  # 项目总分
    evaluation_result = db.Column(db.String(20))  # 评定结果

    def to_dict(self):
        # 辅助函数：格式化浮点数，保留2位小数
        def format_float(value):
            if value is not None:
                return round(value, 2)
            return None
            
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'construction_unit': self.construction_unit,
            'design_unit': self.design_unit,
            'location': self.location,
            'building_area': format_float(self.building_area),
            'standard': self.standard,
            'building_type': self.building_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'status': self.status,
            # 新增字段
            'climate_zone': self.climate_zone,
            'star_rating_target': self.star_rating_target,
            'total_land_area': format_float(self.total_land_area),
            'total_building_area': format_float(self.total_building_area),
            'above_ground_area': format_float(self.above_ground_area),
            'underground_area': format_float(self.underground_area),
            'underground_floor_area': format_float(self.underground_floor_area),
            'ground_parking_spaces': self.ground_parking_spaces,
            'plot_ratio': format_float(self.plot_ratio),
            'building_base_area': format_float(self.building_base_area),
            'building_density': format_float(self.building_density),
            'green_area': format_float(self.green_area),
            'green_ratio': format_float(self.green_ratio),
            'residential_units': self.residential_units,
            'building_floors': self.building_floors,
            'building_height': format_float(self.building_height),
            'air_conditioning_type': self.air_conditioning_type,
            'average_floors': self.average_floors,
            'has_garbage_room': self.has_garbage_room,
            'has_elevator': self.has_elevator,
            'has_underground_garage': self.has_underground_garage,
            'construction_type': self.construction_type,
            'has_water_landscape': self.has_water_landscape,
            'is_fully_decorated': self.is_fully_decorated,
            'public_building_type': self.public_building_type,
            'public_green_space': self.public_green_space,
            # 新增评分字段（使用中文键名以保持前端兼容性）
            '建筑总分': format_float(self.architecture_score),
            '结构总分': format_float(self.structure_score),
            '给排水总分': format_float(self.water_supply_score),
            '电气总分': format_float(self.electrical_score),
            '暖通总分': format_float(self.hvac_score),
            '景观总分': format_float(self.landscape_score),
            '环境健康与节能总分': format_float(self.env_health_energy_score),
            '环境健康与节能创新总分': format_float(self.env_health_energy_innovation_score),
            '建筑创新总分': format_float(self.architecture_innovation_score),
            '结构创新总分': format_float(self.structure_innovation_score),
            '暖通创新总分': format_float(self.hvac_innovation_score),
            '景观创新总分': format_float(self.landscape_innovation_score),
            '安全耐久总分': format_float(self.safety_durability_score),
            '健康舒适总分': format_float(self.health_comfort_score),
            '生活便利总分': format_float(self.life_convenience_score),
            '资源节约总分': format_float(self.resource_saving_score),
            '环境宜居总分': format_float(self.environment_livability_score),
            '提高与创新总分': format_float(self.improvement_innovation_score),
            '项目总分': format_float(self.total_score),
            '评定结果': self.evaluation_result,
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 用户角色：admin或user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)  # 最后在线时间
    
    # 添加个人信息字段
    nickname = db.Column(db.String(50))  # 用户昵称
    gender = db.Column(db.String(10))  # 性别
    avatar_index = db.Column(db.Integer, default=0)  # 头像索引
    
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
        
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'nickname': self.nickname or self.email.split('@')[0],
            'gender': self.gender or '保密',
            'avatar_index': self.avatar_index or 0,
            'is_online': self.is_online(),
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S') if self.last_seen else None
        }

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

class ClimateZone(db.Model):
    """气候区划表模型"""
    __tablename__ = '气候区划'
    
    
    id = db.Column(db.Integer, primary_key=True)
    省 = db.Column(db.String(50), primary_key=True, nullable=False)
    地级市 = db.Column(db.String(50), primary_key=True, nullable=False)
    分区名称 = db.Column(db.String(50), nullable=False)
    气候区划 = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<ClimateZone {self.省}-{self.地级市}-{self.分区名称}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'province': self.省,
            'city': self.地级市,
            'district': self.分区名称,
            'climate_zone': self.气候区划
        }
# 添加评价标准的模型
class review_standard(db.Model):
    __tablename__ = '评价标准'
    
    # 使用中文字段名
    序号 = db.Column(db.Integer, primary_key=True)
    条文号 = db.Column(db.String(20))
    分类 = db.Column(db.String(50))
    专业 = db.Column(db.String(50))
    条文内容 = db.Column(db.Text)
    分值 = db.Column(db.String(10))
    审查材料 = db.Column(db.Text)
    属性 = db.Column(db.String(20))  # 属性字段，包含控制项、评分项
    标准名称 = db.Column(db.String(20))  # 标准名称字段
    图片路径 = db.Column(db.String(255))  # 条文图片路径字段

class FormData(db.Model):
    __tablename__ = 'form_data'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    project_name = db.Column(db.String(100))
    building_no = db.Column(db.String(50))
    project_location = db.Column(db.String(200))
    design_no = db.Column(db.String(50))
    construction_unit = db.Column(db.String(100))
    design_unit = db.Column(db.String(100))
    standard_selection = db.Column(db.String(20))
    form_data = db.Column(db.Text)  # 存储JSON格式的表单数据
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class ProjectCollaborator(db.Model):
    """项目协作者模型"""
    __tablename__ = 'project_collaborators'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='参与者')  # 角色：创建者、参与者
    permissions = db.Column(db.String(20), nullable=False, default='只读')  # 权限：只读、编辑、管理
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 定义唯一约束，确保一个用户只能以一种角色参与一个项目
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='uix_project_user'),)
    
    # 定义与Project的关系
    project = db.relationship('Project', backref=db.backref('collaborators', lazy='dynamic', cascade='all, delete-orphan'))
    
    # 定义与User的关系
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('collaborations', lazy='dynamic'))
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'nickname': self.user.nickname or self.user.email.split('@')[0] if self.user else None,
            'role': self.role,
            'permissions': self.permissions,
            'joined_at': self.joined_at.strftime('%Y-%m-%d %H:%M:%S') if self.joined_at else None,
            'invited_by': self.invited_by,
            'inviter_email': self.inviter.email if self.inviter else None
        }

class ProjectInvitation(db.Model):
    """项目邀请模型"""
    __tablename__ = 'project_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    permissions = db.Column(db.String(20), nullable=False, default='只读')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # 定义与Project的关系
    project = db.relationship('Project', backref=db.backref('invitations', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def is_expired(self):
        """检查邀请是否已过期"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'token': self.token,
            'permissions': self.permissions,
            'created_by': self.created_by,
            'creator_email': self.creator.email if self.creator else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }