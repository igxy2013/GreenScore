# 导入必要的系统模块
import os
import platform
import base64
import json
import random
import string
import time
import traceback
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

# 导入数据库相关模块
import pymysql
import sqlite3
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 导入Flask相关模块
from flask import (
    Flask, Blueprint, Response, flash, jsonify, redirect, 
    render_template, request, send_file, send_from_directory,
    session, url_for, abort
)
from flask_caching import Cache
from flask_cors import CORS
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)

# 导入项目内部模块
from dotenv import load_dotenv
from word_template import process_template, replace_placeholders
from export import (
    generate_word, generate_dwg,
    generate_self_assessment_report,
    generate_generateljzpwb
)
from models import (
    db, User, InvitationCode, LogRecord,
    Project, review_standard, FormData,
    ProjectCollaborator, ProjectInvitation
)
from admin import admin_app
from utils.extract_word_info import extract_project_info
from map_helper import init_routes
# 导入公共交通分析报告生成函数
from generate_transport_report import generate_transport_report
# 导入初始化数据库的函数
try:
    from init_db import init_db
except ImportError:
    # 如果无法导入，定义一个空函数
    def init_db():
        print("未找到init_db模块，跳过数据库初始化")
        pass

# 导入日志模块
import logging
from logging.handlers import RotatingFileHandler

# 导入异常处理
import werkzeug.exceptions

# 定义等级到属性的映射
LEVEL_TO_ATTRIBUTE = {
    '基本级': '控制项',
    '提高级': '评分项'
}

# 加载环境变量
load_dotenv()

# 创建应用
app = Flask(__name__, static_folder='static', static_url_path='/static')

# 从map_helper获取路由函数但不自动注册
map_routes = init_routes(app)
# 手动注册elevation路由，这是我们缺少的路由
app.add_url_rule('/api/elevation', view_func=map_routes['get_elevation'], methods=['GET'])
app.add_url_rule('/api/google_elevation', view_func=map_routes['get_google_elevation'], methods=['GET'])

# 设置配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXPORT_FOLDER'] = 'static/exports'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大上传文件限制为16MB

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 将日志级别从INFO改为WARNING
logger = logging.getLogger('greenscore')
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.WARNING)  # 将处理器的级别从INFO改为WARNING
logger.addHandler(handler)
app.logger = logger

# 禁用其他库的冗余日志
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('flask_cors').setLevel(logging.WARNING)

# 配置 session
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_123')  # 添加一个默认的密钥
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 判断是否为生产环境
is_production = os.environ.get('FLASK_ENV') == 'production'

# 配置缓存
cache_config = {
    "DEBUG": not is_production,
    "CACHE_TYPE": "FileSystemCache" if is_production else "SimpleCache",
    "CACHE_DIR": "cache" if is_production else None,
    "CACHE_DEFAULT_TIMEOUT": 3600  # 缓存过期时间，单位秒（1小时）
}
cache = Cache(app, config=cache_config)

# 配置数据库连接
db_uri = os.environ.get('DATABASE_URL')
if not db_uri:
    # MySQL数据库连接配置
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_database = os.environ.get('MYSQL_DATABASE', '绿色建筑')
    mysql_username = os.environ.get('MYSQL_USERNAME', 'root')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 'password')
    
    # 构建MySQL连接字符串
    db_uri = f'mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    app.logger.warning("警告: DATABASE_URL 环境变量未设置，使用默认连接字符串")

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # 禁用SQLAlchemy的ECHO功能，不管是开发环境还是生产环境

# 初始化数据库
db.init_app(app)

# 初始化数据库迁移
migrate = Migrate(app, db)

# 初始化login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.admin_login'  # 修改这里，指向管理员登录页面
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

# 添加请求处理器来更新用户的last_seen时间
@app.before_request
def update_last_seen():
    """更新用户的最后访问时间"""
    if current_user.is_authenticated:
        try:
            # 尝试使用timezone.utc (Python 3.8+)
            current_user.last_seen = datetime.now(timezone.utc)
        except (AttributeError, TypeError):
            # 回退到旧方法
            current_user.last_seen = datetime.utcnow()
        db.session.commit()

# 添加请求日志中间件
@app.before_request
def log_request_info():
    # 只记录GET和POST请求
    if request.method in ['GET', 'POST', 'PUT', 'DELETE']:
        try:
            # 获取用户ID（如果已登录）
            user_id = current_user.id if current_user.is_authenticated else None
            
            # 记录请求信息，但排除静态文件和某些特定路径
            path = request.path
            if not path.startswith('/static/') and not path.startswith('/favicon.ico'):
                LogRecord.add_log(
                    level="INFO",
                    message=f"请求: {request.method} {path}",
                    source="HTTP_REQUEST",
                    user_id=user_id,
                    ip_address=request.remote_addr,
                    path=path,
                    method=request.method,
                    user_agent=request.user_agent.string
                )
        except Exception as e:
            app.logger.error(f"记录请求日志时出错: {str(e)}")

# 添加响应日志中间件
@app.after_request
def log_response_info(response):
    try:
        # 只记录错误响应
        if response.status_code >= 400:
            path = request.path
            if not path.startswith('/static/') and not path.startswith('/favicon.ico'):
                user_id = current_user.id if current_user.is_authenticated else None
                
                LogRecord.add_log(
                    level="ERROR" if response.status_code >= 500 else "WARNING",
                    message=f"响应错误: {request.method} {path} 状态码: {response.status_code}",
                    source="HTTP_RESPONSE",
                    user_id=user_id,
                    ip_address=request.remote_addr,
                    path=path,
                    method=request.method,
                    user_agent=request.user_agent.string
                )
    except Exception as e:
        app.logger.error(f"记录响应日志时出错: {str(e)}")
    
    return response

# 添加异常日志中间件
@app.errorhandler(Exception)
def log_exception(e):
    try:
        # 获取请求相关信息
        path = request.path if request else "未知路径"
        method = request.method if request else "未知方法"
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        
        # 对静态文件的404错误进行特殊处理，减少日志记录
        if isinstance(e, werkzeug.exceptions.NotFound) and (path.startswith('/static/') or path == '/favicon.ico'):
            # 静态文件404不记录详细日志，只在DEBUG模式下记录
            if app.debug:
                app.logger.debug(f"静态文件未找到: {path}")
            return render_template('error.html', error="文件未找到"), 404
        
        # 记录异常信息
        LogRecord.add_log(
            level="ERROR",
            message=f"系统异常: {str(e)}",
            source="EXCEPTION",
            user_id=user_id,
            ip_address=request.remote_addr if request else None,
            path=path,
            method=method,
            user_agent=request.user_agent.string if request else None
        )
        
        # 记录详细的异常堆栈到应用日志
        app.logger.error(f"系统异常: {str(e)}", exc_info=True)
        
    except Exception as log_err:
        app.logger.error(f"记录异常日志时出错: {str(log_err)}")
    
    # 返回通用的错误页面
    return render_template('error.html', error=str(e)), 500

# 添加专门的404错误处理器
@app.errorhandler(404)
def page_not_found(e):
    # 获取请求路径
    path = request.path
    
    # 对静态文件的请求进行特殊处理
    if path.startswith('/static/') or path == '/favicon.ico':
        # 静态文件不存在的情况，返回简单的404响应而不记录详细日志
        return "File not found", 404
    
    # 非静态文件的404，记录日志
    app.logger.warning(f"页面未找到: {request.method} {path}")
    
    # 返回自定义404页面
    return render_template('error.html', error="页面未找到"), 404

# 添加405错误处理器
@app.errorhandler(405)
def method_not_allowed(e):
    # 检查是否为非应用路径的请求
    non_app_paths = ['/dns-query', '/robots.txt', '/favicon.ico']
    if request.path in non_app_paths:
        app.logger.debug(f"忽略对非应用路径的请求: {request.method} {request.path}")
        return '', 204  # 返回无内容状态码
    
    # 记录其他405错误
    app.logger.warning(f"方法不允许: {request.method} {request.path}")
    return render_template('error.html', 
                          error_code=405, 
                          error_message="请求方法不被允许"), 405

# 邀请码相关API路由
@app.route('/api/invite-codes', methods=['POST'])
@login_required
def generate_invite_code():
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '只有管理员可以生成邀请码'}), 403
    
    try:
        # 生成随机邀请码
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # 创建新的邀请码记录
        new_code = InvitationCode(code=code)
        db.session.add(new_code)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '邀请码生成成功',
            'code': code
            
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'生成邀请码失败: {str(e)}')
        return jsonify({'success': False, 'message': '生成邀请码失败'}), 500

@app.route('/api/invite-codes/<int:code_id>', methods=['DELETE'])
@login_required
def delete_invite_code(code_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '只有管理员可以删除邀请码'}), 403
    
    try:
        code = InvitationCode.query.get_or_404(code_id)
        db.session.delete(code)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '邀请码删除成功'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除邀请码失败: {str(e)}')
        return jsonify({'success': False, 'message': '删除邀请码失败'}), 500

# 添加登录要求装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def sync_score_tables(project_id):
    """同步得分表数据（注：project_scores表已移除）"""
    if not project_id:
        logger.warning("项目ID不能为空，无法同步数据")
        return False
    
    try:
        logger.info(f"项目ID={project_id}的数据同步功能已更新：project_scores表已移除，不再需要同步操作")
        
        # 获取项目信息
        project = get_project(project_id)
        if not project:
            logger.error(f"项目不存在: ID={project_id}")
            return False
            
        # 返回成功，表示处理完成
        return True
            
    except Exception as e:
        logger.error(f"处理项目数据时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False


# 缓存所有数据的函数
@cache.cached(key_prefix='all_standards')
def get_all_standards():
    print("从数据库获取所有标准数据...")
    start_time = time.time()
    standards = review_standard.query.all()
    end_time = time.time()
    print(f"查询耗时: {end_time - start_time:.2f}秒，获取到 {len(standards)} 条记录")
    return standards

# 按专业和级别缓存数据的函数
@cache.memoize()
def get_filtered_standards(level, specialty):
    print(f"从数据库获取筛选数据: 级别={level}, 专业={specialty}")
    start_time = time.time()
    # 将级别转换为对应的属性值
    attribute = LEVEL_TO_ATTRIBUTE.get(level, '')
    if attribute:
        print(f"级别 '{level}' 对应属性值 '{attribute}'")
    
    # 获取当前项目
    project = get_project()
    standard_name = project.standard if project and project.standard else '成都市标'
    print(f"当前评价标准: {standard_name}")
    
    # 使用新的评价标准模型
    model_class = review_standard
    
    # 尝试多种筛选方法
    standards = []
    
    # 方法1: 使用属性字段精确匹配并按标准名称筛选
    if attribute and specialty:
        try:
            query1 = model_class.query.filter(getattr(model_class, '属性') == attribute)
            query1 = query1.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            query1 = query1.filter(getattr(model_class, '标准名称') == standard_name)
            # 添加按序号排序
            query1 = query1.order_by(getattr(model_class, '序号'))
            standards1 = query1.all()
            print(f"方法1 (属性精确匹配): 找到 {len(standards1)} 条记录")
            if standards1:
                standards = standards1
        except Exception as e:
            print(f"方法1查询错误: {str(e)}")
    
    # 方法2: 使用属性字段模糊匹配并按标准名称筛选
    if not standards and attribute:
        try:
            query2 = model_class.query
            query2 = query2.filter(getattr(model_class, '属性').like(f'%{attribute}%'))
            if specialty:
                query2 = query2.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            query2 = query2.filter(getattr(model_class, '标准名称') == standard_name)
            # 添加按序号排序
            query2 = query2.order_by(getattr(model_class, '序号'))
            standards2 = query2.all()
            print(f"方法2 (属性模糊匹配): 找到 {len(standards2)} 条记录")
            if standards2:
                standards = standards2
        except Exception as e:
            print(f"方法2查询错误: {str(e)}")
    
    # 方法3: 只按专业和标准名称筛选
    if not standards and specialty:
        try:
            query3 = model_class.query.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            query3 = query3.filter(getattr(model_class, '标准名称') == standard_name)
            # 添加按序号排序
            query3 = query3.order_by(getattr(model_class, '序号'))
            standards3 = query3.all()
            print(f"方法3 (仅按专业): 找到 {len(standards3)} 条记录")
            if standards3:
                standards = standards3
        except Exception as e:
            print(f"方法3查询错误: {str(e)}")
    
    # 方法4: 使用SQL文本查询
    if not standards:
        try:
            sql = f"SELECT * FROM `{model_class.__tablename__}`"
            conditions = []
            if attribute:
                conditions.append(f"属性 = '{attribute}'")
            if specialty:
                conditions.append(f"专业 LIKE '%{specialty}%'")
            conditions.append(f"标准名称 = '{standard_name}'")
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            # 添加按序号排序
            sql += " ORDER BY 序号"
            
            print(f"执行SQL: {sql}")
            result = db.session.execute(text(sql))
            standards = [dict(zip(result.keys(), row)) for row in result]
            print(f"方法4 (SQL文本查询): 找到 {len(standards)} 条记录")
        except Exception as e:
            print(f"方法4查询错误: {str(e)}")
    
    # 如果所有方法都失败，返回当前标准下的所有记录（同样按序号排序）
    if not standards:
        try:
            standards = model_class.query.filter(getattr(model_class, '标准名称') == standard_name).order_by(getattr(model_class, '序号')).all()
            print(f"所有筛选方法都失败，返回所有 {len(standards)} 条记录")
        except Exception as e:
            print(f"获取所有记录错误: {str(e)}")
            standards = []
    
    end_time = time.time()
    print(f"筛选查询耗时: {end_time - start_time:.2f}秒")
    
    return standards

# 根据标准名称获取对应的标准数据
def get_standards_by_name(standard_name):
    print(f"获取标准数据: {standard_name}")
    return review_standard.query.filter(review_standard.标准名称 == standard_name).all()

# 获取项目信息
def get_project(project_id=None):
    try:
        if project_id:
            # 获取指定ID的项目
            project = db.session.get(Project, project_id)
        else:
            # 获取第一个项目
            project = Project.query.first()
        return project
    except Exception as e:
        print(f"获取项目信息时出错: {str(e)}")
        return None

# 保存项目信息
def save_project_info(form_data):
    try:
        # 获取项目ID
        project_id = form_data.get('project_id', '')
        if project_id:
            try:
                project_id = int(project_id)
            except ValueError:
                project_id = None
        
        # 如果有项目ID，获取现有项目；否则创建新项目
        if project_id:
            project = db.session.get(Project, project_id)
            if not project:
                print(f"未找到ID为{project_id}的项目，创建新项目")
                project = Project()
        else:
            print("未提供项目ID，创建新项目")
            project = Project()
        
        # 检查是否是详细信息表单
        is_detail_form = form_data.get('detail_form') == '1'
        print(f"表单类型: {'详细信息表单' if is_detail_form else '基本信息表单'}")
        
        # 获取新的项目名称
        new_project_name = form_data.get('project_name', '')
        if not new_project_name:
            print("错误：未提供项目名称")
            return None
        
        # 获取当前登录用户的ID
        user_id = session.get('user_id')
        if not user_id:
            print("错误：用户未登录")
            return None
        
        # 检查项目标准
        standard = form_data.get('standard_selection', '')
        if not standard:
            print("错误：未提供评价标准")
            return None
            
        # 检查建筑类型
        building_type = form_data.get('building_type', '')
        
        # 检查星级目标
        star_rating_target = form_data.get('star_rating_target', '')
        
        # 基本信息表单数据
        project.name = new_project_name
        project.user_id = user_id
        project.standard = standard
        project.building_type = building_type
        project.star_rating_target = star_rating_target
        project.code = form_data.get('project_code', '')
        project.construction_unit = form_data.get('construction_unit', '')
        project.design_unit = form_data.get('design_unit', '')
        project.location = form_data.get('project_location', '')
        project.climate_zone = form_data.get('climate_zone', '')
        # 设置项目状态为"进行中"
        project.status = '进行中'
        
        # 始终处理详细字段，不再依赖is_detail_form标志
        # 尝试将表单值转换为浮点数
        try_parse_float(form_data, 'total_land_area', project, 'total_land_area')
        try_parse_float(form_data, 'total_building_area', project, 'total_building_area')
        try_parse_float(form_data, 'above_ground_area', project, 'above_ground_area')
        try_parse_float(form_data, 'underground_area', project, 'underground_area')
        try_parse_float(form_data, 'first_floor_underground_area', project, 'underground_floor_area')
        try_parse_float(form_data, 'plot_ratio', project, 'plot_ratio')
        try_parse_float(form_data, 'building_base_area', project, 'building_base_area')
        try_parse_float(form_data, 'building_density', project, 'building_density')
        
        # 特别记录绿地面积的处理
        green_area_value = form_data.get('green_area', '')
        print(f"处理绿地面积字段: 原始值={green_area_value}")
        try_parse_float(form_data, 'green_area', project, 'green_area')
        print(f"绿地面积处理后的值: {project.green_area}")
        
        try_parse_float(form_data, 'green_ratio', project, 'green_ratio')
        try_parse_float(form_data, 'building_height', project, 'building_height')
        
        # 尝试将表单值转换为整数
        try_parse_int(form_data, 'ground_parking_spaces', project, 'ground_parking_spaces')
        try_parse_int(form_data, 'residential_units', project, 'residential_units')
        
        # 设置其他字段
        project.building_floors = form_data.get('building_floors', '')
        project.air_conditioning_type = form_data.get('ac_type', '')
        project.average_floors = form_data.get('avg_floors', '')
        project.has_garbage_room = form_data.get('has_garbage_room', '')
        project.has_elevator = form_data.get('has_elevator', '')
        project.has_underground_garage = form_data.get('has_underground_garage', '')
        project.construction_type = form_data.get('construction_type', '')
        project.has_water_landscape = form_data.get('has_water_landscape', '')
        project.is_fully_decorated = form_data.get('is_fully_decorated', '')
        project.public_building_type = form_data.get('public_building_type', '')
        project.public_green_space = form_data.get('public_green_space', '')
        
        # 记录将要保存的数据内容
        print(f"正在保存项目信息，详细字段包括：总用地面积={project.total_land_area}, 总建筑面积={project.total_building_area}, 地上建筑面积={project.above_ground_area}, 地下建筑面积={project.underground_area}")
        
        # 保存项目信息到数据库
        db.session.add(project)
        db.session.commit()
        db.session.refresh(project)  # 刷新对象以获取最新值
        
        print(f"项目信息保存成功: ID={project.id}, 名称={project.name}")
        # 打印详细字段是否成功保存
        print(f"详细字段保存结果：总用地面积={project.total_land_area}, 总建筑面积={project.total_building_area}, 地上建筑面积={project.above_ground_area}, 地下建筑面积={project.underground_area}")
        
        return project
    except Exception as e:
        db.session.rollback()
        print(f"保存项目信息时出错: {str(e)}")
        print(traceback.format_exc())
        return None

# 辅助函数：尝试解析浮点数
def try_parse_float(form_data, form_field, model_obj, model_field):
    """尝试将表单字段解析为浮点数并赋值给模型对象"""
    try:
        value = form_data.get(form_field, '')
        if value is not None and value != '':
            # 清理数值字符串，移除可能的非数字字符
            clean_value = str(value).replace(',', '').strip()
            # 尝试转换为浮点数
            float_value = float(clean_value)
            # 确保值为0也被正确保存，而不是被当作空值处理
            model_obj.__setattr__(model_field, float_value)
            
            if form_field == 'green_area':
                print(f"成功将绿地面积 '{value}' 转换为浮点数: {float_value}")
        else:
            if form_field == 'green_area':
                print(f"绿地面积字段为空或无效: '{value}'")
            model_obj.__setattr__(model_field, None)
    except (ValueError, TypeError) as e:
        print(f"无法将字段 {form_field} 值 '{value}' 转换为浮点数: {str(e)}")
        # 如果转换失败，设置为None
        model_obj.__setattr__(model_field, None)

# 辅助函数：尝试解析整数
def try_parse_int(form_data, form_field, model_obj, model_field):
    """尝试将表单字段解析为整数并赋值给模型对象"""
    try:
        value = form_data.get(form_field, '')
        if value is not None and value != '':
            # 清理数值字符串，移除可能的非数字字符
            clean_value = str(value).replace(',', '').strip()
            # 尝试转换为整数
            int_value = int(float(clean_value))  # 先转为float再转为int，处理可能的小数点
            # 确保值为0也被正确保存，而不是被当作空值处理
            model_obj.__setattr__(model_field, int_value)
            print(f"成功将字段 {form_field} 值 '{value}' 转换为整数: {int_value}")
        else:
            model_obj.__setattr__(model_field, None)
            print(f"字段 {form_field} 为空，设置为None")
    except (ValueError, TypeError) as e:
        print(f"无法将字段 {form_field} 值 '{value}' 转换为整数: {str(e)}")
        # 如果转换失败，设置为None
        model_obj.__setattr__(model_field, None)

# 项目管理页面路由
@app.route('/projects')
@app.route('/project_management')
@login_required
def project_management():
    try:
        username = session.get('username', '未登录')
        return render_template('project_management.html', username=username)
    except Exception as e:
        print(f"项目管理页面出错: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

# 创建项目路由
@app.route('/create_project', methods=['POST'])
@login_required
def create_project():
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': '用户未登录'}), 401
        
        data = request.get_json()
        project_name = data.get('name')
        standard = data.get('standard')
        star_rating_target = data.get('star_rating_target')
        building_type = data.get('building_type')
        
        if not project_name:
            return jsonify({'error': '项目名称不能为空'}), 400
        
        if not standard:
            return jsonify({'error': '请选择评价标准'}), 400
        
        try:
            # 创建新项目
            project = Project(
                name=project_name,
                user_id=user_id,
                standard=standard,
                building_type=building_type,
                star_rating_target=star_rating_target,
                code=data.get('code'),
                construction_unit=data.get('construction_unit'),
                design_unit=data.get('design_unit'),
                location=data.get('location'),
                climate_zone=data.get('climate_zone'),
                total_land_area=data.get('total_land_area'),
                total_building_area=data.get('total_building_area'),
                above_ground_area=data.get('above_ground_area'),
                underground_area=data.get('underground_area'),
                plot_ratio=data.get('plot_ratio'),
                building_base_area=data.get('building_base_area'),
                building_density=data.get('building_density'),
                green_area=data.get('green_area'),
                green_ratio=data.get('green_ratio'),
                building_height=data.get('building_height'),
                building_floors=data.get('building_floors'),
                air_conditioning_type=data.get('air_conditioning_type'),
                has_garbage_room=data.get('has_garbage_room'),
                has_elevator=data.get('has_elevator'),
                has_underground_garage=data.get('has_underground_garage'),
                construction_type=data.get('construction_type'),
                has_water_landscape=data.get('has_water_landscape'),
                is_fully_decorated=data.get('is_fully_decorated'),
                public_building_type=data.get('public_building_type'),
                public_green_space=data.get('public_green_space')
            )
            
            # 尝试添加项目并提交事务
            db.session.add(project)
            db.session.flush()  # 获取项目ID但不提交事务
            
            project_id = project.id
            app.logger.info(f"项目创建成功: ID={project_id}, 名称={project_name}")
            
            # 添加创建者作为协作者记录
            collaborator = ProjectCollaborator(
                project_id=project_id,
                user_id=user_id,
                role='创建者',
                permissions='管理'
            )
            db.session.add(collaborator)
            
            # 为项目创建默认评分数据
            try:
                app.logger.info(f"创建项目默认评分数据: 项目ID={project_id}, 名称={project_name}, 标准={standard}")
                create_default_scores(project_id, project_name, standard)
            except Exception as score_error:
                app.logger.error(f"创建默认评分数据失败: {str(score_error)}")
                app.logger.error(traceback.format_exc())
                # 继续执行，不影响项目创建
            
            # 提交事务
            db.session.commit()
            return jsonify({
                'id': project_id,
                'name': project.name,
                'message': '项目创建成功'
            })
        except Exception as db_error:
            db.session.rollback()
            app.logger.error(f"数据库操作失败: {str(db_error)}")
            app.logger.error(traceback.format_exc())
            
            # 检查是否是ID字段无默认值错误
            if "Field 'id' doesn't have a default value" in str(db_error):
                return jsonify({
                    'error': '数据库配置错误：ID字段未配置为自动递增。请检查数据库表结构或联系管理员。'
                }), 500
            else:
                return jsonify({
                    'error': f'数据库写入失败: {str(db_error)}'
                }), 500
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建项目失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'创建项目失败: {str(e)}'}), 500

# 在文件末尾添加create_default_scores函数
def create_default_scores(project_id, project_name, standard_selection):
    """
    为项目创建默认评分记录
    
    参数:
    - project_id: 项目ID
    - project_name: 项目名称
    - standard_selection: 评价标准
    """
    try:
        app.logger.info(f"开始创建默认评分记录...")
        
        # 获取标准数据
        app.logger.info(f"获取标准数据: {standard_selection}")
        standards_data = get_standards_by_name(standard_selection)
        if standards_data:

            # 插入新的评分记录
            insert_count = 0
            insert_errors = 0
            for std in standards_data:
                # 所有条文默认达标为"是"
                is_achieved = '是'
                    # 映射评价等级：控制项 → 基本级，评分项 → 提高级
                level_mapping = {
                    '控制项': '基本级',
                    '评分项': '提高级'
                }
                # 获取映射后的评价等级，如果找不到映射则保持原值
                normalized_level = std.属性.strip()  # 去除前后空格
                mapped_level = level_mapping.get(normalized_level, normalized_level)
                # 插入评分记录
                try:
                    db.session.execute(
                        text("""
                        INSERT INTO `得分表` (
                            `项目ID`, `项目名称`, `专业`, `评价等级`, `条文号`, `分类`, 
                            `是否达标`, `得分`, `技术措施`, `评价标准`
                        ) VALUES (
                            :project_id, :project_name, :specialty, :level, :clause_number, 
                            :category, :is_achieved, :score, :technical_measures, :standard
                        )
                        """),
                        {
                            "project_id": project_id,
                            "project_name": project_name,
                            "specialty": std.专业,
                            "level": mapped_level,  # 使用映射后的值,
                            "clause_number": std.条文号,
                            "category": std.分类,
                            "is_achieved": is_achieved,
                            "score": '0',
                            "technical_measures": '',
                            "standard": standard_selection
                        }
                    )
                    # 每插入10条记录提交一次事务，避免事务过大
                    if insert_count % 10 == 0:
                        db.session.commit()
                        app.logger.info(f"已提交 {insert_count} 条记录")
                except Exception as insert_error:
                    app.logger.error(f"插入评分记录失败: {str(insert_error)}, 条文号: {std.条文号}")
        
        # 提交最后的事务
        try:
            db.session.commit()
            app.logger.info(f"最终提交事务成功")
        except Exception as commit_error:
            app.logger.error(f"提交事务失败: {str(commit_error)}")
            db.session.rollback()
            app.logger.error(traceback.format_exc())
        return True
    
    except Exception as e:
        app.logger.error(f"生成项目评分数据失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return False

# 修改项目访问权限检查
def check_project_access(project_id):
    """检查当前用户是否有权限访问指定项目"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
        
        # 检查是否为项目创建者
        project = Project.query.filter_by(id=project_id, user_id=user_id).first()
        if project:
            return True
        
        # 检查是否为项目协作者
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id, 
            user_id=user_id
        ).first()
        
        return collaborator is not None
    except Exception as e:
        print(f"检查项目访问权限失败: {str(e)}")
        return False

# 修改项目详情页面访问
@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    # 检查访问权限
    if not check_project_access(project_id):
        flash('您没有权限访问该项目', 'error')
        return redirect(url_for('project_management'))
    
    try:
        project = Project.query.get_or_404(project_id)
        
        # 获取请求参数并处理可能的URL编码问题
        page = request.args.get('page', 'project_info')
        
        # 处理特殊情况：如果URL中包含等号，说明可能是错误格式的参数
        # 例如i3l2page=green_materials.js这种格式
        for key, value in request.args.items():
            if '=' in key:
                parts = key.split('=', 1)
                if parts[1] == 'green_materials':
                    page = 'green_materials'
                    app.logger.warning(f"检测到特殊格式的页面参数: {key}，已修正为: page={page}")
        
        # 获取用户的项目权限信息
        user_permissions = get_project_permissions(project_id)
        
        # 如果页面类型为公共交通分析，使用iframe加载页面
        if page == 'public_transport_analysis':
            app.logger.info(f"访问项目 ID: {project_id}, 名称: {project.name}, 页面: {page}")
            return render_template('dashboard.html', project=project, current_page=page, user_permissions=user_permissions)
        
        # 如果页面类型为规范查询库，获取所有PDF文件并传递给模板
        if page == 'standards_library':
            pdf_files = get_pdf_standards()
            app.logger.info(f"访问项目 ID: {project_id}, 名称: {project.name}, 页面: {page}, PDF文件数量: {len(pdf_files)}")
            return render_template('dashboard.html', project=project, current_page=page, pdf_files=pdf_files, user_permissions=user_permissions)
        
        app.logger.info(f"访问项目 ID: {project_id}, 名称: {project.name}, 页面: {page}")
        return render_template('dashboard.html', project=project, current_page=page, user_permissions=user_permissions)
    except Exception as e:
        app.logger.error(f"获取项目详情失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return render_template('error.html', error=f"获取项目详情失败: {str(e)}")

# 获取PDF规范文件列表
def get_pdf_standards():
    """获取PDF规范文件列表"""
    pdf_dir = os.path.join(app.static_folder, 'pdf')
    pdf_files = []
    
    try:
        if os.path.exists(pdf_dir):
            for filename in os.listdir(pdf_dir):
                if filename.lower().endswith('.pdf'):
                    # 提取文件名作为标题，去掉扩展名
                    title = os.path.splitext(filename)[0]
                    
                    # 添加文件信息
                    pdf_files.append({
                        'filename': filename,
                        'title': title,
                        'description': '绿色建筑相关规范文件',
                    })
    except Exception as e:
        app.logger.error(f"获取PDF文件列表失败: {str(e)}")
    
    return pdf_files

# 修改项目删除函数
@app.route('/delete_project/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    try:
        # 检查访问权限
        if not check_project_access(project_id):
            return jsonify({'error': '您没有权限删除该项目'}), 403
        
        project = db.session.get(Project, project_id)
        if not project:
            return abort(404)  # 返回404错误，项目不存在
            
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"删除项目失败: {str(e)}")
        return jsonify({'error': '删除项目失败'}), 500

@app.route('/reset_password')
def reset_password_page():
    """处理密码重置页面路由"""
    try:
        return render_template('reset_password.html')
    except Exception as e:
        app.logger.error(f"渲染密码重置页面错误: {str(e)}")
        return "页面加载失败", 500
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def handle_form():
    try:
        form_type = request.form.get('form_type', '')
        print(f"接收到表单提交: form_type={form_type}")
        
        # 检查是否为AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or 'application/json' in request.headers.get('Accept', '')
        print(f"是否是AJAX请求: {is_ajax}")
        
        # 打印所有表单字段
        print("表单数据:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        
        if form_type == 'project_info':
            # 处理项目信息表单提交
            print("处理项目信息表单...")
            # 检查是否是详细信息表单
            is_detail_form = request.form.get('detail_form') == '1'
            print(f"表单类型: {'详细信息表单' if is_detail_form else '基本信息表单'}")
            
            # 检查public_green_space字段
            public_green_space = request.form.get('public_green_space', '')
            print(f"绿地向公众开放: {public_green_space}")
            
            project = save_project_info(request.form)
            if project:
                print(f"项目信息保存成功: ID={project.id}, 名称={project.name}, 标准={project.standard}, 绿地向公众开放={project.public_green_space}")
                
                if is_ajax:
                    # 如果是AJAX请求，返回JSON响应
                    return jsonify({
                        'success': True,
                        'message': '项目信息保存成功',
                        'project_id': project.id,
                        'project_name': project.name,
                        'is_detail_form': is_detail_form  # 添加这个字段以便前端知道是详细表单
                    })
                else:
                    # 如果是传统表单提交，重定向回项目详情页面
                    return redirect(url_for('project_detail', project_id=project.id))
            else:
                print("项目信息保存失败")
                
                if is_ajax:
                    # 如果是AJAX请求，返回错误JSON响应
                    return jsonify({
                        'success': False,
                        'message': '项目信息保存失败'
                    }), 400
                else:
                    # 如果是传统表单提交，重定向到项目管理页面
                    return redirect(url_for('project_management'))
        else:
            print(f"未知的表单类型: {form_type}")
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': f'未知的表单类型: {form_type}'
                }), 400
        
        # 如果不是已知的表单类型且不是AJAX请求，返回首页
        return redirect(url_for('index'))
    except Exception as e:
        print(f"处理表单时发生错误: {str(e)}")
        print(traceback.format_exc())
        
        # 检查是否为AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or 'application/json' in request.headers.get('Accept', '')
        
        if is_ajax:
            # 如果是AJAX请求，返回错误JSON响应
            return jsonify({
                'success': False,
                'message': f'处理表单时发生错误: {str(e)}'
            }), 500
        else:
            # 如果是传统表单提交，渲染错误页面
            return render_template('error.html', error=str(e))

@app.route('/filter')
def filter_standards():
    try:
        level = request.args.get('level', '基本级')
        specialty = request.args.get('specialty', '建筑')
        project_id = request.args.get('project_id')
        
        # 获取项目信息
        project = None
        if project_id:
            project = db.session.get(Project, project_id)
        
        # 获取项目对应的标准名称
        standard_name = None
        if project and project.standard:
            standard_name = project.standard
            print(f"使用项目设置的评价标准: {standard_name}")
        else:
            standard_name = request.args.get('standard', '成都市标')
            print(f"项目未设置评价标准，使用默认标准: {standard_name}")
        
        # 获取过滤后的标准
        standards = []
        
        # 使用新的评价标准模型
        model_class = review_standard
        
        # 获取属性值
        attribute = LEVEL_TO_ATTRIBUTE.get(level, '')
        
        # 查询数据
        try:
            query = model_class.query
            if attribute:
                query = query.filter(getattr(model_class, '属性') == attribute)
            if specialty:
                query = query.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            # 按标准名称筛选
            query = query.filter(getattr(model_class, '标准名称') == standard_name)
            
            # 添加按序号排序
            query = query.order_by(getattr(model_class, '序号').asc())
            standards = query.all()
            print(f"从 {standard_name} 获取标准数据: level={level}, specialty={specialty}, 找到{len(standards)}条记录")
        except Exception as e:
            print(f"查询标准数据出错: {str(e)}")
            print(traceback.format_exc())
        
        # 如果没有找到数据，尝试使用更宽松的条件
        if not standards:
            try:
                query = model_class.query
                if specialty:
                    query = query.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
                # 按标准名称筛选
                query = query.filter(getattr(model_class, '标准名称') == standard_name)
                
                # 添加按序号排序
                query = query.order_by(getattr(model_class, '序号').asc())
                standards = query.all()
                print(f"使用宽松条件从 {standard_name} 获取标准数据: specialty={specialty}, 找到{len(standards)}条记录")
            except Exception as e:
                print(f"宽松查询标准数据出错: {str(e)}")
                print(traceback.format_exc())
        
        # 打印调试信息
        print(f"过滤标准: level={level}, specialty={specialty}, standard={standard_name}, 找到{len(standards)}条记录")
        
        # 渲染模板
        return render_template(
            'dashboard.html', 
            standards=standards, 
            current_level=level, 
            current_specialty=specialty,
            current_page='specialty',  # 设置为specialty页面，确保保存按钮正常工作
            project=project
        )
    except Exception as e:
        app.logger.error(f"过滤标准时出错: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error=str(e))

@app.route('/calculator')
@login_required
def calculator():
    # 获取项目ID参数
    project_id = request.args.get('project_id')
    # 如果没有提供项目ID，则使用当前用户的第一个项目
    if not project_id:
        project = Project.query.first()
        if project:
            project_id = project.id
            
    return render_template('components/calculator.html', current_project_id=project_id)

@app.route('/decorative_cost_calculator')
@login_required
def decorative_cost_calculator():
    # 获取项目ID参数
    project_id = request.args.get('project_id')
    # 重定向到主页面，并添加查询参数指示显示装饰性构件造价比例计算
    return redirect(url_for('user_dashboard', show_decorative=1, project_id=project_id))

@app.route('/solar_calculator')
@login_required
def solar_calculator():
    # 获取项目ID参数
    project_id = request.args.get('project_id')
    # 重定向到主页面，并添加查询参数指示显示太阳能计算器
    return redirect(url_for('dashboard', show_solar=1, project_id=project_id))

# 添加清除缓存的路由（可选，用于管理员手动刷新缓存）
@app.route('/clear_cache')
def clear_cache():
    try:
        cache.clear()
        return "缓存已清除"
    except Exception as e:
        return f"清除缓存时出错: {str(e)}"

@app.route('/api/save_form', methods=['POST'])
def save_form():
    try:
        import json
        from sqlalchemy import text
        data = request.json
        
        if not data:
            return jsonify({'error': '没有收到数据'}), 400
            
        # 获取当前用户的项目ID
        project_id = data.get('project_id')
        if not project_id:
            # 没有提供项目ID时，获取第一个项目
            project = Project.query.first()
            project_id = project.id if project else None
        
        if not project_id:
            return jsonify({'error': '无效的项目ID'}), 400
        
        # 记录请求信息，方便排查问题
        app.logger.info(f"保存表单 - 项目ID: {project_id}")
        
        # 提取表单数据
        building_no = data.get('buildingNo', '')
        standard_selection = data.get('standardSelection', 'municipal')
        form_data_json = json.dumps(data.get('formData', {}), ensure_ascii=False)
        
        # 首先尝试检查是否已存在记录
        existing_record = None
        try:
            existing_record = db.session.query(FormData).filter(FormData.project_id == project_id).order_by(FormData.updated_at.desc()).first()
        except Exception as query_error:
            app.logger.error(f"查询表单记录失败: {str(query_error)}")
        
        # 不使用subtransactions参数，SQLAlchemy较新版本已移除该参数
        # db.session.begin(subtransactions=True)
        
        try:
            if existing_record:
                # 已存在记录，进行更新
                app.logger.info(f"更新现有表单记录 - ID: {existing_record.id}")
                
                # 更新记录的各个字段
                existing_record.building_no = building_no
                existing_record.standard_selection = standard_selection
                existing_record.form_data = form_data_json
                
                # 直接使用SQL更新时间戳，避免ORM可能的问题
                update_sql = text("UPDATE form_data SET updated_at=NOW() WHERE id=:id")
                db.session.execute(update_sql, {"id": existing_record.id})
                
                result_id = existing_record.id
                is_new = False
            else:
                # 不存在记录，创建新的
                app.logger.info(f"创建新表单记录 - 项目ID: {project_id}")
                
                # 创建新记录
                new_record = FormData(
                    project_id=project_id,
                    building_no=building_no,
                    standard_selection=standard_selection,
                    form_data=form_data_json
                )
                
                # 添加到数据库
                db.session.add(new_record)
                db.session.flush()  # 获取新记录的ID
                
                result_id = new_record.id
                is_new = True
            
            # 提交事务
            db.session.commit()
            app.logger.info(f"表单保存成功 - 记录ID: {result_id}, 是新记录: {is_new}")
            
            return jsonify({
                'success': True, 
                'message': '数据保存成功', 
                'is_new': is_new,
                'form_id': result_id
            })
            
        except Exception as db_error:
            # 回滚事务
            db.session.rollback()
            app.logger.error(f"保存表单数据失败: {str(db_error)}")
            
            if hasattr(db_error, 'orig') and db_error.orig:
                app.logger.error(f"原始数据库错误: {db_error.orig}")
            
            return jsonify({'error': f'数据库操作失败: {str(db_error)}'}), 500
            
    except Exception as e:
        # 确保回滚任何打开的事务
        try:
            db.session.rollback()
        except:
            pass
            
        app.logger.error(f"处理表单保存请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/api/load_form', methods=['GET'])
def load_form():
    """加载保存的表单数据"""
    # 获取项目ID
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({"error": "缺少项目ID参数"}), 400
        
    try:
        app.logger.info(f"尝试加载项目ID {project_id} 的表单数据")
        
        # 从数据库查询数据 - 使用SQLAlchemy而不是直接的mysql连接
        form_data = FormData.query.filter_by(project_id=project_id).order_by(FormData.updated_at.desc()).first()
        
        # 检查是否找到数据
        if not form_data:
            app.logger.info(f"项目ID {project_id} 没有保存的表单数据")
            return jsonify({"error": "没有找到保存的表单数据"}), 404
            
        # 提取JSON数据
        form_data_json = form_data.form_data
        if not form_data_json:
            app.logger.warning(f"项目ID {project_id} 的表单数据为空")
            return jsonify({"error": "表单数据为空"}), 404
            
        # 解析JSON数据
        try:
            # 如果存储的是JSON字符串，则解析它
            if isinstance(form_data_json, str):
                form_data_dict = json.loads(form_data_json)
            else:
                # 如果已经是字典，直接使用
                form_data_dict = form_data_json
                
            # 构建完整的响应数据
            response_data = {
                'buildingNo': form_data.building_no,
                'standardSelection': form_data.standard_selection,
                'formData': form_data_dict
            }
            
            app.logger.info(f"成功加载项目ID {project_id} 的表单数据")
            return jsonify(response_data)
        except json.JSONDecodeError as e:
            app.logger.error(f"解析表单数据JSON失败: {str(e)}")
            return jsonify({"error": f"解析表单数据失败: {str(e)}"}), 500
            
    except Exception as e:
        app.logger.error(f"加载表单数据时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"加载表单数据失败: {str(e)}"}), 500

@app.route('/api/project_info', methods=['GET'])
def get_project_info():
    from flask import request
    try:
        # 获取项目ID参数
        project_id = request.args.get('project_id')
        print(f"\n=== API: 获取项目信息 ===")
        print(f"请求参数: project_id = {project_id}")
        
        # 根据项目ID获取项目信息
        if project_id:
            project = Project.query.filter_by(id=project_id).first()
            print(f"查询项目: ID = {project_id}, 结果: {'找到' if project else '未找到'}")
            if not project:
                print(f"警告: 未找到ID为{project_id}的项目")
        else:
            # 如果没有提供项目ID，则获取第一个项目
            project = Project.query.first()
            project_id = project.id if project else None
            print(f"未提供项目ID，获取第一个项目: {'找到' if project else '未找到'}")
        
        # 获取该项目的表单数据
        form_data = None
        if project_id:
            form_data = FormData.query.filter_by(project_id=project_id).order_by(FormData.updated_at.desc()).first()
            print(f"获取项目ID={project_id}的表单数据: {'找到' if form_data else '未找到'}")
        
        # 辅助函数：格式化浮点数，保留2位小数
        def format_float(value):
            if value is not None:
                return round(value, 2)
            return ''
        
        # 如果项目不存在，打印警告
        if not project:
            print("警告: 项目不存在，将返回空值")
            result = {
                'projectName': '',
                'projectCode': '',
                'constructionUnit': '',
                'designUnit': '',
                'projectLocation': '',
                'buildingArea': '',
                'buildingType': '',
                'buildingHeight': '',
                'buildingFloors': '',
                'error': '未找到项目信息'
            }
        else:
            # 构建结果对象
            result = {
                '项目名称': project.name if project.name is not None else '',
                '项目地点': project.location if project.location is not None else '',
                '项目编号': project.code if project.code is not None else '',
                '建设单位': project.construction_unit if project.construction_unit is not None else '',
                '设计单位': project.design_unit if project.design_unit is not None else '',
                '建筑类型': project.building_type if project.building_type is not None else '',
                '建筑高度': project.building_height,
                '建筑层数': project.building_floors if project.building_floors is not None else '',
                '总用地面积': project.total_land_area,
                '总建筑面积': project.total_building_area,
                '地上建筑面积': project.above_ground_area,
                '地下建筑面积': project.underground_area,
                '绿地率': project.green_ratio,
                '容积率': project.plot_ratio,
                '建筑密度': project.building_density,
                '建筑基底面积': project.building_base_area,
            }   
            
            # 如果有表单数据，添加到结果中
            if form_data:
                result['buildingNo'] = form_data.building_no if form_data.building_no is not None else ''
                result['designNo'] = form_data.design_no if form_data.design_no is not None else ''
                result['standardSelection'] = form_data.standard_selection if form_data.standard_selection is not None else 'municipal'
        
        # 打印最终结果
        print(f"返回结果:")
        for key, value in result.items():
            print(f"  - {key}: {value}")
        
        return jsonify(result)
    except Exception as e:
        print(f"获取项目信息时出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册处理"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': '请求数据无效'}), 400
            
        email = data.get('email')
        password = data.get('password')
        invitation_code = data.get('invitation_code')
        
        app.logger.info(f"收到注册请求: email={email}")
        
        # 基本验证
        if not email or not password or not invitation_code:
            return jsonify({'message': '请输入邮箱、密码和邀请码'}), 400
            
        # 邮箱格式验证
        if not '@' in email or not '.' in email:
            return jsonify({'message': '请输入有效的邮箱地址'}), 400
            
        # 密码长度验证
        if len(password) < 8:
            return jsonify({'message': '密码长度不能少于8位'}), 400
            
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'message': '该邮箱已被注册'}), 400

        # 验证邀请码
        invite = InvitationCode.query.filter_by(code=invitation_code).first()
        if not invite:
            return jsonify({'message': '无效的邀请码'}), 400
            
        if invite.usage_count >= invite.max_usage:
            return jsonify({'message': '邀请码已达到使用上限'}), 400

        try:
            # 创建新用户
            new_user = User(
                email=email,
                role='user'
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()  # 获取新用户的ID
            
            # 更新邀请码使用情况
            invite.usage_count += 1
            try:
                # 尝试使用timezone.utc (Python 3.8+)
                invite.used_at = datetime.now(timezone.utc)
            except (AttributeError, TypeError):
                # 回退到旧方法
                invite.used_at = datetime.utcnow()
            invite.used_by = new_user.id
            
            db.session.commit()
            app.logger.info(f"用户注册成功: {email}")
            return jsonify({'success': True, 'message': '注册成功'}), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"数据库操作失败: {str(e)}")
            return jsonify({'message': '注册失败，请稍后重试'}), 500
            
    except Exception as e:
        app.logger.error(f"注册过程出错: {str(e)}")
        return jsonify({'message': '注册失败，请稍后重试'}), 500

@app.route('/api/check_user', methods=['POST'])
def check_user():
    try:
        data = request.get_json()
        username = data.get('username')
        
        app.logger.info(f"检查用户是否存在: username={username}")
        
        if not username:
            return jsonify({'error': '请输入用户名'}), 400
            
        user = User.query.filter_by(email=username).first()
        return jsonify({'exists': bool(user)})
        
    except Exception as e:
        app.logger.error(f"检查用户错误: {str(e)}")
        return jsonify({'error': '服务器错误'}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        app.logger.info(f"收到重置密码请求: username={username}")
        
        if not username or not password:
            return jsonify({'error': '请输入用户名和新密码'}), 400
            
        user = User.query.filter_by(email=username).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 更新密码
        try:
            user.set_password(password)
            db.session.commit()
            app.logger.info(f"密码重置成功: username={username}")
            return jsonify({'success': True})
        except Exception as db_error:
            db.session.rollback()
            app.logger.error(f"数据库操作失败: {str(db_error)}")
            return jsonify({'error': '重置密码失败，请稍后重试'}), 500
            
    except Exception as e:
        app.logger.error(f"重置密码错误: {str(e)}")
        return jsonify({'error': '重置密码失败，请稍后重试'}), 500

@app.route('/user_guide')
@login_required
def user_guide():
    """用户使用指南页面"""
    try:
        return render_template('user_guide.html')
    except Exception as e:
        app.logger.error(f"访问用户指南页面出错: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_page'))
@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    try:
        # 获取当前用户ID
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取该用户创建的所有项目
        own_projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
        
        # 获取用户自己创建的项目ID列表，用于后面去重
        own_project_ids = [project.id for project in own_projects]
        
        # 获取该用户作为协作者参与的所有项目，排除自己创建的项目
        collaborated_project_ids = db.session.query(ProjectCollaborator.project_id) \
                                  .filter_by(user_id=user_id) \
                                  .filter(~ProjectCollaborator.project_id.in_(own_project_ids)) \
                                  .all()
        
        collaborated_project_ids = [pid[0] for pid in collaborated_project_ids]
        collaborated_projects = []
        
        if collaborated_project_ids:
            collaborated_projects = Project.query.filter(Project.id.in_(collaborated_project_ids)) \
                                   .order_by(Project.created_at.desc()) \
                                   .all()
        
        # 合并两类项目并转换为JSON格式
        projects_data = []
        
        # 添加用户创建的项目
        for project in own_projects:
            # 确保项目对象有效
            if project is None:
                continue
                
            # 使用to_dict方法获取项目数据
            project_data = project.to_dict()
            # 标记为自己创建的项目
            project_data['is_owner'] = True
            project_data['role'] = '创建者'
            project_data['permissions'] = '管理'
            projects_data.append(project_data)
        
        # 添加用户作为协作者参与的项目
        for project in collaborated_projects:
            if project is None:
                continue
            
            project_data = project.to_dict()
            
            # 获取协作者信息
            collaborator = ProjectCollaborator.query.filter_by(
                project_id=project.id,
                user_id=user_id
            ).first()
            
            # 标记为协作项目
            project_data['is_owner'] = False
            project_data['role'] = collaborator.role if collaborator else '参与者'
            project_data['permissions'] = collaborator.permissions if collaborator else '只读'
            projects_data.append(project_data)
        
        return jsonify({
            'success': True,
            'projects': projects_data
        })
    except Exception as e:
        app.logger.error(f"获取项目列表时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': '获取项目列表失败'}), 500

# 添加项目信息页面路由
@app.route('/project_info_page')
def project_info_page():
    try:
        # 获取项目ID参数
        project_id = request.args.get('project_id')
        
        if project_id:
            # 根据项目ID获取项目信息
            project = Project.query.filter_by(id=project_id).first()
            if not project:
                app.logger.warning(f"未找到项目ID: {project_id}")
                # 如果项目不存在，返回空项目信息
                return render_template('project_info.html', project=None)
            
            app.logger.info(f"访问项目信息页面: 项目ID={project_id}, 名称={project.name}")
            return render_template('project_info.html', project=project)
        else:
            app.logger.warning("访问项目信息页面，但未提供项目ID")
            return render_template('project_info.html', project=None)
    except Exception as e:
        app.logger.error(f"访问项目信息页面出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return render_template('error.html', error=f"获取项目信息失败: {str(e)}")
# 添加新的路由用于直接更新得分
@app.route('/api/update_score_direct', methods=['POST'])
def update_score_direct():

    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '未接收到JSON数据'
            }), 400
        
        # 验证必要参数
        project_id = data.get('project_id')
        clause_number = data.get('clause_number')
        score = data.get('score')
        standard = data.get('standard', '成都市标')
        
        # 可选参数
        is_achieved = data.get('is_achieved', '是')
        technical_measures = data.get('technical_measures', '')
        
        # 记录请求信息
        app.logger.info(f"接收到更新请求: 项目ID={project_id}, 条文号={clause_number}, 得分={score}, 标准={standard}")
        
        # 验证必要参数
        if not all([project_id, clause_number, score is not None]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: project_id, clause_number, score'
            }), 400
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 使用SQLAlchemy事务管理
                app.logger.info("开始数据库操作")
                
                with db.session.begin():
                    # 先检查记录是否存在
                    check_query = """
                    SELECT COUNT(*) FROM `得分表`
                    WHERE `项目ID` = :project_id AND `条文号` = :clause_number AND `评价标准` = :standard
                    """
                    result = db.session.execute(
                        text(check_query), 
                        {"project_id": project_id, "clause_number": clause_number, "standard": standard}
                    )
                    count = result.fetchone()[0]
                    
                    if count > 0:
                        # 更新现有记录，只修改得分字段
                        update_query = """
                        UPDATE `得分表`
                        SET `得分` = :score
                        WHERE `项目ID` = :project_id AND `条文号` = :clause_number AND `评价标准` = :standard
                        """
                        result = db.session.execute(
                            text(update_query),
                            {"score": score, "project_id": project_id, "clause_number": clause_number, "standard": standard}
                        )
                        app.logger.info(f"更新记录: 影响行数={result.rowcount}")
                    else:
                        # 插入新记录
                        insert_query = """
                        INSERT INTO `得分表` (
                            `项目ID`, `条文号`, 
                             `是否达标`, `得分`, `技术措施`, `评价标准`
                        )
                        VALUES (:project_id, :clause_number, 
                               :is_achieved, :score, :technical_measures, :standard)
                        """
                        result = db.session.execute(
                            text(insert_query),
                            {
                                "project_id": project_id, 
                                "clause_number": clause_number,
                                "is_achieved": is_achieved, 
                                "score": score, 
                                "technical_measures": technical_measures, 
                                "standard": standard
                            }
                        )
                        app.logger.info(f"插入记录: 影响行数={result.rowcount}")
                    
                    # 验证更新是否成功
                    verify_query = """
                    SELECT `得分` FROM `得分表`
                    WHERE `项目ID` = :project_id AND `条文号` = :clause_number AND `评价标准` = :standard
                    """
                    result = db.session.execute(
                        text(verify_query), 
                        {"project_id": project_id, "clause_number": clause_number, "standard": standard}
                    )
                    row = result.fetchone()
                    
                    if not row:
                        raise Exception("验证失败：未找到更新后的记录")
                    
                    actual_score = row[0]
                    app.logger.info(f"验证成功: 条文 {clause_number} 的得分为 {actual_score}")
                
                # 清除评分汇总缓存
                cache_key = f"score_summary_{project_id}_{standard}"
                if cache.has(cache_key):
                    cache.delete(cache_key)
                    app.logger.info(f"清除评分汇总缓存: {cache_key}")
                
                # 清除专业得分缓存
                specialty_cache_key = get_scores_cache_key('提高级', '建筑专业', project_id, standard)
                if cache.has(specialty_cache_key):
                    cache.delete(specialty_cache_key)
                    app.logger.info(f"清除专业得分缓存: {specialty_cache_key}")
                
                # 返回成功响应
                return jsonify({
                    'success': True,
                    'message': '更新成功',
                    'data': {
                        'project_id': project_id,
                        'clause_number': clause_number,
                        'score': actual_score,
                        'standard': standard
                    }
                })
                
            except Exception as e:
                # 回滚事务
                db.session.rollback()
                app.logger.error(f"数据库操作失败: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    app.logger.info(f"正在进行第{retry_count}次重试...")
                    time.sleep(1)  # 等待1秒后重试
                else:
                    app.logger.error("已达到最大重试次数，操作失败")
                    app.logger.error(traceback.format_exc())
                    return jsonify({
                        'success': False,
                        'message': f'数据库操作失败: {str(e)}'
                    }), 500
    
    except Exception as e:
        app.logger.error(f"处理请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500
# 添加一个函数来生成得分表缓存的键
def get_scores_cache_key(level, specialty, project_id=None, standard=None):
    """
    生成评分数据的缓存键
    
    参数:
        level: 评价等级
        specialty: 专业
        project_id: 项目ID
        standard: 评价标准
        
    返回值:
        缓存键字符串
    """
    # 构建基本缓存键
    cache_key = f"scores_{level}_{specialty}"
    
    # 如果有项目ID，添加到缓存键
    if project_id:
        cache_key += f"_{project_id}"
    
    # 如果有评价标准，添加到缓存键
    if standard:
        cache_key += f"_{standard}"
    
    return cache_key

@app.route('/api/star_case_scores', methods=['GET'])
def get_star_case_scores():
    try:
        # 获取目标项目ID
        target_project_id = request.args.get('target_project_id')
        if not target_project_id:
            return jsonify({
                'success': False,
                'message': '请提供目标项目ID'
            }), 400

        # 获取项目信息
        target_project = db.session.get(Project, target_project_id)
        if not target_project:
            return jsonify({
                'success': False,
                'message': f'目标项目(ID={target_project_id})不存在'
            }), 404

        # 获取项目的评价标准和星级目标
        standard = target_project.standard or '成都市标'
        star_rating_target = target_project.star_rating_target or '一星级'
        building_type = target_project.building_type
        project_location = target_project.location  # 获取项目地点

        try:
            # 首先获取当前项目适用的条文号列表
            app.logger.info(f"获取项目 {target_project_id} 适用的条文列表")
            result = db.session.execute(text(f"""
                SELECT 条文号 
                FROM 评价标准 
                WHERE 标准名称 = :standard_name
            """), {"standard_name": standard})
            valid_clauses = set([row[0] for row in result.fetchall()])
            app.logger.info(f"找到 {len(valid_clauses)} 条适用的条文")

            # 构建基本查询条件
            query_conditions = ["评价标准 = :standard"]
            query_params = {"standard": standard}
            
            # 放宽匹配条件，只保留评价标准必须匹配，其他条件可选
            # 添加星级目标和建筑类型作为可选条件，优先匹配完全相同的记录
            query_optional_conditions = []
            
            try:
                # 标准查询，优先查找完全匹配的记录
                query = f"""
                    SELECT DISTINCT 条文号, 分类, 是否达标, 得分, 技术措施, 专业, 评价等级
                    FROM 星级案例
                    WHERE {' AND '.join(query_conditions)}
                    AND 星级目标 = :star_rating_target 
                    AND 建筑类型 = :building_type
                """
                
                app.logger.info(f"执行精确匹配查询: {query}")
                result = db.session.execute(text(query), {
                    **query_params,
                    "star_rating_target": star_rating_target,
                    "building_type": building_type
                })
                case_data = result.fetchall()
                
                # 如果没有找到完全匹配的记录，则放宽条件只匹配评价标准
                if not case_data:
                    app.logger.info("未找到完全匹配的记录，尝试仅匹配评价标准")
                    query = f"""
                        SELECT DISTINCT 条文号, 分类, 是否达标, 得分, 技术措施, 专业, 评价等级
                        FROM 星级案例
                        WHERE {' AND '.join(query_conditions)}
                    """
                    
                    app.logger.info(f"执行宽松匹配查询: {query}")
                    result = db.session.execute(text(query), query_params)
                    case_data = result.fetchall()
            except Exception as e:
                app.logger.error(f"查询星级案例出错: {str(e)}")
                case_data = []
            
            if case_data:
                app.logger.info(f"找到 {len(case_data)} 条匹配的星级案例数据")
                
                # 过滤出当前标准中有效的条文
                filtered_case_data = []
                for record in case_data:
                    if record[0] in valid_clauses:
                        filtered_case_data.append(record)
                    else:
                        app.logger.info(f"过滤掉不适用的条文: {record[0]}")
                
                app.logger.info(f"过滤后剩余 {len(filtered_case_data)} 条有效的星级案例数据")
                
                # 如果过滤后没有数据，则使用原始数据（放宽条件）
                if not filtered_case_data:
                    app.logger.warning("过滤后没有有效数据，将使用所有匹配的数据")
                    filtered_case_data = case_data
                
                # 先删除目标项目的所有得分数据
                delete_query = """
                DELETE FROM 得分表
                WHERE 项目ID = :project_id
                """
                result = db.session.execute(text(delete_query), {"project_id": target_project_id})
                deleted_count = result.rowcount
                app.logger.info(f"删除目标项目的 {deleted_count} 条得分数据")

                # 插入新的得分数据
                inserted_count = 0
                # 用于跟踪已插入的条文号，防止重复
                inserted_clauses = set()
                
                for record in filtered_case_data:
                    clause_number, category, is_achieved, score, technical_measures, specialty, level = record
                    
                    # 跳过已经插入过的条文号
                    if clause_number in inserted_clauses:
                        app.logger.info(f"跳过重复条文: {clause_number}")
                        continue
                    
                    inserted_clauses.add(clause_number)

                    insert_query = """
                    INSERT INTO 得分表 (
                        项目ID, 项目名称, 专业, 评价等级, 条文号, 
                        分类, 是否达标, 得分, 技术措施, 评价标准
                    ) VALUES (:project_id, :project_name, :specialty, :level, :clause_number,
                            :category, :is_achieved, :score, :technical_measures, :standard)
                    """
                    db.session.execute(
                        text(insert_query),
                        {
                            "project_id": target_project_id,
                            "project_name": target_project.name,
                            "specialty": specialty,
                            "level": level,
                            "clause_number": clause_number,
                            "category": category,
                            "is_achieved": is_achieved,
                            "score": score,
                            "technical_measures": technical_measures,
                            "standard": standard
                        }
                    )
                    inserted_count += 1

                    # 每100条提交一次，避免事务过大
                    if inserted_count % 100 == 0:
                        db.session.commit()
                        app.logger.info(f"已提交 {inserted_count} 条记录")

                # 提交事务
                db.session.commit()
                app.logger.info(f"事务提交成功，共导入 {inserted_count} 条记录")

                # 清除目标项目的缓存
                cache_key = f"score_summary_{target_project_id}_{standard}"
                if cache.has(cache_key):
                    cache.delete(cache_key)
                    app.logger.info(f"清除目标项目的评分汇总缓存: {cache_key}")

                return jsonify({
                    'success': True,
                    'message': f'成功导入 {inserted_count} 条星级案例数据',
                    'data': {
                        'standard': standard,
                        'star_rating_target': star_rating_target,
                        'imported_count': inserted_count,
                        'location_matched': bool(case_data)
                    }
                })
            else:
                app.logger.warning(f"未找到匹配的星级案例数据")
                return jsonify({
                    'success': False,
                    'message': f'未找到匹配的星级案例数据'
                }), 404

        except Exception as e:
            # 回滚事务
            db.session.rollback()
            app.logger.error(f"数据库操作失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'数据库操作失败: {str(e)}'
            }), 500

    except Exception as e:
        app.logger.error(f"处理请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500
# 添加获取百度地图API密钥的API端点
@app.route('/api/map_api_key', methods=['GET'])
def get_map_api_key():
    try:
        # 从环境变量获取百度地图API密钥
        api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')  # 使用环境变量中的密钥，提供一个默认值
        
        # 返回API密钥
        return jsonify({'api_key': api_key})
    except Exception as e:
        app.logger.error(f"获取地图API密钥时出错: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
# 添加获取高德地图API密钥的API端点
@app.route('/api/gaode_map_api_key', methods=['GET'])
def get_gaode_map_api_key():
    try:
        # 从环境变量获取高德地图API密钥和安全密钥
        api_key = os.environ.get('GAODE_MAP_AK')
        security_js_code = os.environ.get('GAODE_MAP_SEC_CODE')
        
        if not api_key or not security_js_code:
            return jsonify({'error': '高德地图API密钥未配置'}), 500
        
        # 返回API密钥和安全密钥
        return jsonify({
            'api_key': api_key,
            'security_js_code': security_js_code
        })
    except Exception as e:
        app.logger.error(f"获取高德地图API密钥时出错: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
# 添加百度地图API代理
@app.route('/api/map_proxy', methods=['GET', 'POST'])
def map_api_proxy():
    try:
        app.logger.info(f"百度地图API代理请求: {request.url}")
        
        # 获取百度地图API密钥
        api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')
        
        # 获取所有请求参数
        params = request.args.to_dict()
        
        # 获取服务路径
        service_path = params.pop('service_path', 'api')
        
        # 判断是否是静态资源请求（图片等）
        is_static_resource = service_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js'))
        
        # 如果不是静态资源请求，则添加API密钥
        if not is_static_resource:
            params['ak'] = api_key
        
        # 构建百度地图API请求URL
        base_url = f"https://api.map.baidu.com/{service_path}"
        app.logger.info(f"代理到URL: {base_url}, 参数: {params}")
        
        # 发送请求
        import requests
        
        if request.method == 'GET':
            response = requests.get(base_url, params=params, timeout=10)
        else:  # POST请求
            post_data = request.get_data()
            headers = {'Content-Type': request.headers.get('Content-Type', 'application/x-www-form-urlencoded')}
            response = requests.post(base_url, params=params, data=post_data, headers=headers, timeout=10)
        
        # 根据不同的资源类型设置不同的Content-Type
        content_type = response.headers.get('Content-Type')
        if is_static_resource:
            if service_path.endswith('.png'):
                content_type = 'image/png'
            elif service_path.endswith('.jpg') or service_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif service_path.endswith('.gif'):
                content_type = 'image/gif'
            elif service_path.endswith('.css'):
                content_type = 'text/css'
            elif service_path.endswith('.js'):
                content_type = 'application/javascript'
        
        app.logger.info(f"代理响应状态码: {response.status_code}, Content-Type: {content_type}")
        
        # 返回百度地图API的响应
        return Response(
            response.content, 
            status=response.status_code,
            content_type=content_type or 'application/json'
        )
    except Exception as e:
        app.logger.error(f"百度地图API代理出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'代理请求失败: {str(e)}'}), 500

# 添加百度地图JavaScript API代理
@app.route('/api/map_js_api', methods=['GET'])
def map_js_api_proxy():
    try:
        # 获取百度地图API密钥
        api_key = os.environ.get('BAIDU_MAP_API_KEY', 'J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL')
        
        # 获取请求参数
        params = request.args.to_dict()
        
        # 添加API密钥
        params['ak'] = api_key
        
        # 构建百度地图JavaScript API的URL
        url = "https://api.map.baidu.com/api"
        
        # 发送请求
        import requests
        response = requests.get(url, params=params, timeout=10)
        
        # 返回JavaScript内容
        return Response(
            response.content, 
            status=response.status_code,
            content_type='application/javascript'
        )
    except Exception as e:
        app.logger.error(f"百度地图JavaScript API代理出错: {str(e)}")
        return Response(
            f"console.error('加载地图API失败: {str(e)}');", 
            status=500,
            content_type='application/javascript'
        )

# 添加一个新的路由处理评分汇总页面的请求
@app.route('/score_summary_page/<project_id>')
def score_summary_page(project_id):
    # 查询项目信息
    project = Project.query.filter_by(id=project_id).first()
    
    # 将项目信息传递给模板
    return render_template('score_summary.html', project=project, session=session)
@app.route('/api/get_score_summary', methods=['GET'])
def api_get_score_summary():
    """获取评分汇总数据的API端点"""
    try:
        # 获取项目ID参数
        project_id = request.args.get('project_id')
        
        # 获取force_refresh参数
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        app.logger.info(f"收到评分汇总请求: 项目ID={project_id}, 强制刷新={force_refresh}")
        
        # 如果没有提供项目ID，返回错误
        if not project_id:
            app.logger.warning("评分汇总请求缺少项目ID参数")
            return jsonify({'error': '缺少项目ID参数'}), 400
        
        # 转换项目ID为整数
        project_id = int(project_id)
        
        # 获取项目信息，确定评价标准
        project = get_project(project_id)
        if not project:
            app.logger.warning(f"找不到ID为{project_id}的项目")
            return jsonify({'error': f'找不到ID为{project_id}的项目'}), 404
            
        project_standard = project.standard if project and project.standard else '成都市标'
        app.logger.info(f"项目标准: {project_standard}")
        
        # 缓存键
        cache_key = f"score_summary_{project_id}_{project_standard}"
        
        # 如果强制刷新，清除缓存
        if force_refresh and cache.has(cache_key):
            cache.delete(cache_key)
            app.logger.info(f"清除评分汇总缓存: {cache_key}")
        
        # 获取评分汇总数据
        app.logger.info(f"开始获取评分汇总数据")
        score_summary = get_score_summary(project_id, force_refresh=force_refresh)
        app.logger.info(f"获取评分汇总数据完成")
        
        # 检查返回的评分汇总数据评价标准是否与项目标准一致（只在强制刷新时检查）
        if force_refresh and score_summary.get('project_standard') != project_standard:
            app.logger.warning(f"评分汇总数据的评价标准({score_summary.get('project_standard')})与项目评价标准({project_standard})不一致，重新获取")
            cache.delete(cache_key)
            score_summary = get_score_summary(project_id, force_refresh=True)
        
        # 检查数据是否完整
        if 'specialty_scores' not in score_summary or not score_summary['specialty_scores']:
            app.logger.warning(f"评分汇总数据不完整，专业得分为空")
            if 'specialty_scores' not in score_summary:
                score_summary['specialty_scores'] = {}
            # 添加一个时间戳，帮助调试
            score_summary['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 返回评分汇总数据
        app.logger.info(f"返回评分汇总数据: {len(str(score_summary))} 字节")
        return jsonify(score_summary)
    
    except ValueError as e:
        app.logger.error(f"参数错误: {str(e)}")
        return jsonify({'error': f'参数错误: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"获取评分汇总数据失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        # 返回错误信息
        return jsonify({
            'error': '获取评分汇总数据失败',
            'message': str(e),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500
# 获取评分汇总数据的函数
def get_score_summary(project_id, force_refresh=False):
    """获取评分汇总数据的函数"""
    try:
        # 获取项目信息，确定评价标准
        project = get_project(project_id)
        project_standard = project.standard if project and project.standard else '成都市标'
        
        # 只在强制刷新或开发环境下记录详细日志
        if force_refresh or app.debug:
            app.logger.info(f"获取评分汇总数据: 项目ID={project_id}, 评价标准={project_standard}, 强制刷新={force_refresh}")
        
        # 构建缓存键
        cache_key = f"score_summary_{project_id}_{project_standard}"
        
        # 标记是否需要更新项目表
        need_update_project = force_refresh
        summary_data = None
        
        # 如果强制刷新或缓存中没有数据，则重新计算
        if force_refresh or not cache.get(cache_key):
            # 专业名称映射，用于处理数据库中的专业名称与预定义专业名称的不完全匹配
            specialty_mapping = {
                '建筑': '建筑专业',
                '结构': '结构专业',
                '给排水': '给排水专业',
                '电气': '电气专业',
                '暖通': '暖通专业',
                '景观': '景观专业',
                '环境健康与节能': '环境健康与节能专业',
                '建筑专业': '建筑专业',
                '结构专业': '结构专业',
                '给排水专业': '给排水专业',
                '电气专业': '电气专业',
                '暖通空调专业': '暖通专业',
                '暖通专业': '暖通专业',
                '景观专业': '景观专业'
            }
            
            # 获取所有专业的得分数据
            specialties = ['建筑专业', '结构专业', '给排水专业', '电气专业', '暖通专业', '景观专业']
            
            # 如果是四川省标，添加环境健康与节能专业
            if project_standard == '四川省标':
                specialties.append('环境健康与节能专业')
            
            # 存储各专业得分
            specialty_scores = {specialty: 0 for specialty in specialties}
            # 存储各专业按分类的得分
            specialty_scores_by_category = {}
            
            # 初始化各专业的分类得分
            for specialty in specialties:
                specialty_scores_by_category[specialty] = {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0,
                    '总分': 0
                }
            
            try:
                # 优化SQL查询：一次获取所有需要的数据
                sql_query = """
                SELECT `专业`, `分类`, `是否达标`, `得分`, `评价等级`
                FROM `得分表`
                WHERE `项目ID` = :project_id AND `评价标准` = :standard
                """
                
                # 执行查询并获取所有结果
                result = db.session.execute(
                    text(sql_query), 
                    {"project_id": project_id, "standard": project_standard}
                )
                rows = result.fetchall()
                
                # 减少日志输出，只记录结果行数
                if app.debug:
                    app.logger.info(f"查询结果: {len(rows)} 行")
                
                # 处理查询结果
                for row in rows:
                    specialty = row[0]
                    category = row[1]
                    is_achieved = row[2]
                    score = row[3]
                    level = row[4]
                    
                    # 减少日志记录，提高性能
                    # 映射专业名称
                    mapped_specialty = specialty_mapping.get(specialty)
                    if not mapped_specialty:
                        # 如果没有精确匹配，尝试部分匹配
                        for key, value in specialty_mapping.items():
                            if key in specialty or specialty in key:
                                mapped_specialty = value
                                break
                    
                    # 如果仍然没有匹配，跳过
                    if not mapped_specialty:
                        if app.debug:
                            app.logger.warning(f"未能映射专业名称: {specialty}")
                        continue
                    
                    # 处理是否达标字段
                    is_achieved_value = is_achieved.lower() if isinstance(is_achieved, str) else str(is_achieved).lower()
                    is_achieved_flag = is_achieved_value in ['是', 'yes', 'true', '1', 'y']
                    
                    # 处理得分字段
                    score_value = 0
                    if score is not None:
                        try:
                            if isinstance(score, (int, float)):
                                score_value = float(score)
                            elif isinstance(score, str) and score.strip():
                                score_value = float(score)
                        except (ValueError, TypeError):
                            # 简化错误处理，不记录详细日志
                            pass
                    
                    # 基本级条文必须达标才计分，提高级条文有得分就计分
                    if (level == '基本级' and is_achieved_flag) or (level == '提高级' and score_value > 0):
                        specialty_scores[mapped_specialty] += score_value
                        
                        # 按分类累加得分
                        if category in specialty_scores_by_category[mapped_specialty]:
                            specialty_scores_by_category[mapped_specialty][category] += score_value
                
                # 计算各专业的总分
                for specialty in specialties:
                    category_scores = specialty_scores_by_category[specialty]
                    total_score = sum(score for category, score in category_scores.items() if category != '总分')
                    category_scores['总分'] = total_score
                    specialty_scores[specialty] = total_score  # 更新专业总分
                
                # 计算总分（所有专业分数之和）
                total_score = sum(specialty_scores.values())
                
                # 根据总分确定评定结果
                if total_score >= 85:
                    evaluation_result = '三星级绿色建筑'
                elif total_score >= 70:
                    evaluation_result = '二星级绿色建筑'
                elif total_score >= 55:
                    evaluation_result = '一星级绿色建筑'
                else:
                    evaluation_result = '未达标'
                
                # 构建汇总数据
                summary_data = {
                    'specialty_scores': specialty_scores,
                    'specialty_scores_by_category': specialty_scores_by_category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_score': total_score,
                    'project_standard': project_standard,
                    'evaluation_result': evaluation_result
                }
                
                # 缓存结果 - 设置较长的过期时间（8小时）
                cache.set(cache_key, summary_data, timeout=28800)
                
                # 一定需要更新项目表
                need_update_project = True
                
            except Exception as e:
                app.logger.error(f"查询得分表失败: {str(e)}")
                if app.debug:
                    app.logger.error(traceback.format_exc())
                need_update_project = False
        else:
            # 从缓存中获取数据
            if app.debug:
                app.logger.info(f"从缓存中获取评分汇总数据: {cache_key}")
            summary_data = cache.get(cache_key)
            
        # 如果需要更新项目表，并且有有效的汇总数据
        if need_update_project and summary_data and project_id:
            try:
                # 高效更新项目表，不使用with_for_update以避免锁定延迟
                update_project_scores_efficient(project_id, summary_data)
            except Exception as e:
                # 仅记录错误，不影响API响应
                app.logger.error(f"更新项目表评分数据时出错: {str(e)}")
                
        return summary_data
    
    except Exception as e:
        app.logger.error(f"获取评分汇总数据失败: {str(e)}")
        if app.debug:
            app.logger.error(traceback.format_exc())
        # 返回一个基本的数据结构，而不是隐式返回None
        return {
            'specialty_scores': {},
            'specialty_scores_by_category': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_score': 0,
            'project_standard': '未知',
            'evaluation_result': '未评定'
        }

def update_project_scores_efficient(project_id, scores):
    """高效更新项目表中的评分数据，不使用with_for_update以避免锁定延迟"""
    try:
        # 使用单独的会话避免锁定主会话
        project = db.session.get(Project, project_id)
        if not project:
            if app.debug:
                app.logger.warning(f"找不到要更新评分的项目: ID={project_id}")
            return False
            
        # 更新专业评分
        if 'specialty_scores' in scores:
            specialty_scores = scores['specialty_scores']
            project.architecture_score = specialty_scores.get('建筑专业', 0)
            project.structure_score = specialty_scores.get('结构专业', 0)
            project.water_supply_score = specialty_scores.get('给排水专业', 0)
            project.electrical_score = specialty_scores.get('电气专业', 0)
            project.hvac_score = specialty_scores.get('暖通专业', 0)
            project.landscape_score = specialty_scores.get('景观专业', 0)
            project.env_health_energy_score = specialty_scores.get('环境健康与节能专业', 0)
            
        # 更新章节评分
        if 'specialty_scores_by_category' in scores:
            categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
            category_scores = {cat: 0 for cat in categories}
            specialty_count = 0
            
            for specialty_data in scores['specialty_scores_by_category'].values():
                specialty_count += 1
                for category in categories:
                    if category in specialty_data:
                        category_scores[category] += float(specialty_data[category])
            
            if specialty_count > 0:
                project.safety_durability_score = category_scores['安全耐久'] 
                project.health_comfort_score = category_scores['健康舒适'] 
                project.life_convenience_score = category_scores['生活便利']
                project.resource_saving_score = category_scores['资源节约'] 
                project.environment_livability_score = category_scores['环境宜居']
                project.improvement_innovation_score = category_scores['提高与创新'] 
            
        # 更新总分
        project.total_score = scores.get('total_score', 0)
        
        # 设置评定结果
        project.evaluation_result = scores.get('evaluation_result', '未评定')
        
        # 保存更改
        db.session.commit()
        
        if app.debug:
            app.logger.debug(f"成功更新项目评分: 项目ID={project_id}, 总分={project.total_score}")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        if app.debug:
            app.logger.error(f"更新项目评分失败: {str(e)}")
        return False

# 注册export.py中的generate_word函数为app的路由
@app.route('/api/generate_word', methods=['POST'])
def handle_generate_word():
    """
    处理生成Word文档的请求
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 提取必要参数
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({"error": "缺少项目ID参数"}), 400
            
        # 获取标准参数，默认为成都市标
        standard = data.get('standard', '成都市标')
        
        # 添加use_cache参数，默认为False，强制从数据库获取最新数据
        request_data = {
            'project_id': project_id,
            'standard': standard,
            'use_cache': False
        }
        
        # 调用generate_word函数
        return generate_word(request_data)
    except Exception as e:
        app.logger.error(f"处理生成Word请求失败: {str(e)}")
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500

@app.route('/api/generate_decorative_cost_report', methods=['POST'])
def generate_decorative_cost_report():
    try:
        from utils.document_generator import generate_decorative_cost_report_doc
        import os
        
        data = request.json
        
        if not data:
            return jsonify({'error': '没有接收到数据'}), 400
            
        # 调用新模块中的函数生成文档
        output_path, error = generate_decorative_cost_report_doc(data, app)
        
        if error:
            return jsonify({'error': error}), 500
            
        if not output_path:
            return jsonify({'error': '生成文档失败'}), 500
            
        # 获取文件名
        output_filename = os.path.basename(output_path)
        
        # 返回生成的文件
        return send_file(output_path, 
                        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        as_attachment=True, 
                        download_name=output_filename)
    
    except Exception as e:
        app.logger.error(f"生成装饰性构件造价比例计算书失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_dwg', methods=['POST'])
def handle_generate_dwg():
    """
    处理生成DWG文件的请求
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:    
            return jsonify({"error": "请求数据为空"}), 400

        # 提取必要参数
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({"error": "缺少项目ID参数"}), 400
            
        # 添加use_cache参数，默认为False，强制从数据库获取最新数据
        request_data = {
            'project_id': project_id,
            'use_cache': False
        }
        
        # 调用generate_dwg函数
        return generate_dwg(request_data)
    except Exception as e:
        app.logger.error(f"处理生成DWG请求失败: {str(e)}")
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500

@app.route('/api/projects/<int:project_id>/update_status', methods=['PUT'])
def update_project_status(project_id):
    """更新项目状态
    
    请求参数:
    {
        "status": "进行中"  // 新的项目状态
    }
    
    响应:
    {
        "success": true,
        "message": "项目状态更新成功",
        "data": {
            "id": 1,
            "name": "项目名称",
            "status": "进行中"
        }
    }
    """
    try:
        # 检查用户是否登录
        if 'user_id' not in session:
            app.logger.warning("未登录用户尝试更新项目状态")
            return jsonify({'success': False, 'message': '请先登录'}), 401
            
        # 获取用户ID和角色
        user_id = session.get('user_id')
        user_role = session.get('role', 'user')
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'message': '请提供新的项目状态'}), 400
            
        new_status = data['status']
        
        # 获取项目
        project = db.session.get(Project, project_id)
        if not project:
            app.logger.warning(f"项目 {project_id} 不存在")
            return jsonify({'success': False, 'message': '项目不存在'}), 404
            
        app.logger.info(f"找到项目: {project.name}, 所属用户ID: {project.user_id}")
            
        # 检查权限：管理员可以更新任何项目，普通用户只能更新自己的项目
        if user_role != 'admin' and project.user_id != user_id:
            app.logger.warning(f"用户 {user_id} 无权限更新项目 {project_id}")
            return jsonify({'success': False, 'message': '无权限更新此项目'}), 403
        
        # 更新项目状态
        project.status = new_status
        db.session.commit()
        app.logger.info(f"项目 {project_id} 状态更新为 {new_status}")
        
        return jsonify({
            'success': True,
            'message': '项目状态更新成功',
            'data': {
                'id': project.id,
                'name': project.name,
                'status': project.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新项目状态失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'更新项目状态失败: {str(e)}'}), 500
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project_api(project_id):
    try:
        app.logger.info(f"开始删除项目 {project_id}")
        
        # 获取当前用户ID和角色
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        app.logger.info(f"当前用户ID: {user_id}, 角色: {user_role}")
        
        if not user_id:
            app.logger.warning("用户未登录")
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取项目
        project = db.session.get(Project, project_id)
        if not project:
            app.logger.warning(f"项目 {project_id} 不存在")
            return jsonify({'error': '项目不存在'}), 404
            
        app.logger.info(f"找到项目: {project.name}, 所属用户ID: {project.user_id}")
            
        # 检查权限：管理员可以删除任何项目，普通用户只能删除自己的项目
        if user_role != 'admin' and project.user_id != user_id:
            app.logger.warning(f"用户 {user_id} 无权限删除项目 {project_id}")
            return jsonify({'error': '无权限删除此项目'}), 403
        
        try:
            # 删除项目相关的得分记录
            result = db.session.execute(
                text("DELETE FROM `得分表` WHERE `项目ID` = :project_id"),
                {"project_id": project_id}
            )
            app.logger.info(f"删除得分记录: {result.rowcount} 条")
            
            # 删除项目
            db.session.delete(project)
            db.session.commit()
            app.logger.info(f"项目 {project_id} 删除成功")
            
            return jsonify({
                'success': True,
                'message': '项目删除成功'
            })
            
        except Exception as db_error:
            db.session.rollback()
            app.logger.error(f"数据库操作失败: {str(db_error)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'error': f'数据库操作失败: {str(db_error)}'}), 500
        
    except Exception as e:
        app.logger.error(f"删除项目失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'删除项目失败: {str(e)}'}), 500
@app.route('/api/validate-invite-code', methods=['POST'])
def validate_invite_code():
    """验证邀请码"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({
                'valid': False,
                'message': '请输入邀请码'
            }), 400
            
        # 检查邀请码是否有效
        invite = InvitationCode.query.filter_by(code=code).first()
        if not invite:
            return jsonify({
                'valid': False,
                'message': '无效的邀请码'
            }), 400
            
        if invite.usage_count >= invite.max_usage:
            return jsonify({
                'valid': False,
                'message': '邀请码已达到使用上限'
            }), 400
            
        return jsonify({
            'valid': True,
            'message': '邀请码验证成功'
        }), 200
            
    except Exception as e:
        app.logger.error(f"邀请码验证失败: {str(e)}")
        return jsonify({
            'valid': False,
            'message': '验证失败，请稍后重试'
        }), 500
@app.route('/api/save_score', methods=['POST'])
def save_score():
    """保存评分数据的API端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证数据
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
        
        # 获取评价等级和专业
        level = data.get('level')
        specialty = data.get('specialty')
        project_id = data.get('project_id')
        scores = data.get('scores', [])
        standard = data.get('standard', '成都市标')  # 获取评价标准，默认为成都市标
        
        # 规范化专业名称
        # 给排水专业特殊处理，确保统一数据格式
        original_specialty = specialty
        if specialty and ('给' in specialty or '排' in specialty or '水' in specialty):
            app.logger.info(f"规范化给排水专业名称: 原名称={specialty} -> 规范名称=给排水")
            specialty = '给排水'
        
        # 验证必要字段
        if not level or not specialty:
            return jsonify({'error': '缺少必要字段: level, specialty'}), 400
        
        # 如果没有提供项目ID，尝试从第一个评分记录中获取项目名称
        project_name = None
        if not project_id and scores and len(scores) > 0:
            project_name = scores[0].get('project_name')
        
        # 记录请求信息
        app.logger.info(f"保存评分数据: 级别={level}, 专业={specialty}(原始:{original_specialty}), 项目ID={project_id}, 项目名称={project_name}, 评价标准={standard}, 评分数量={len(scores)}")
        
        # 如果提供了项目ID，获取项目信息
        if project_id:
            try:
                project = get_project(project_id)
                if project:
                    project_name = project.name
                    # 如果项目有评价标准，使用项目的评价标准
                    if project.standard:
                        standard = project.standard
                        app.logger.info(f"使用项目的评价标准: {standard}")
            except Exception as e:
                app.logger.error(f"获取项目信息失败: {str(e)}")
        
        try:
            # 开始数据库事务
            # 如果提供了项目ID，先删除该项目该专业该级别的所有评分记录
            if project_id:
                delete_query = """
                DELETE FROM `得分表`
                WHERE `项目ID` = :project_id AND `专业` = :specialty AND `评价等级` = :level
                """
                result = db.session.execute(
                    text(delete_query), 
                    {"project_id": project_id, "specialty": specialty, "level": level}
                )
                app.logger.info(f"删除项目 {project_id} 的 {specialty} 专业 {level} 级别的评分记录: {result.rowcount} 条")
            
            # 如果提供了项目名称但没有项目ID，先删除该项目名称该专业该级别的所有评分记录
            elif project_name:
                delete_query = """
                DELETE FROM `得分表`
                WHERE `项目名称` = :project_name AND `专业` = :specialty AND `评价等级` = :level
                """
                result = db.session.execute(
                    text(delete_query), 
                    {"project_name": project_name, "specialty": specialty, "level": level}
                )
                app.logger.info(f"删除项目 '{project_name}' 的 {specialty} 专业 {level} 级别的评分记录: {result.rowcount} 条")
            
            # 插入新的评分记录
            insert_count = 0
            
            # 跟踪保存的所有条文号（调试用）
            saved_clauses = []
            
            for score_data in scores:
                # 获取评分数据
                clause_number = score_data.get('clause_number') or score_data.get('clause')
                category = score_data.get('category')
                is_achieved = score_data.get('is_achieved')
                score = score_data.get('score', '0')
                technical_measures = score_data.get('technical_measures', '')
                
                # 如果没有条文号，跳过
                if not clause_number:
                    continue
                
                # 记录所有保存的条文号（调试用）
                saved_clauses.append(clause_number)
                
                # 插入评分记录到得分表
                insert_query = """
                INSERT INTO `得分表` (
                    `项目ID`, `项目名称`, `专业`, `评价等级`, `条文号`, `分类`, `是否达标`, `得分`, `技术措施`, `评价标准`
                ) VALUES (:project_id, :project_name, :specialty, :level, :clause_number, :category, 
                         :is_achieved, :score, :technical_measures, :standard)
                """
                
                try:
                    db.session.execute(
                        text(insert_query),
                        {
                            "project_id": project_id,
                            "project_name": project_name,
                            "specialty": specialty,
                            "level": level,
                            "clause_number": clause_number,
                            "category": category,
                            "is_achieved": is_achieved,
                            "score": score,
                            "technical_measures": technical_measures,
                            "standard": standard
                        }
                    )
                    
                    insert_count += 1
                except Exception as insert_error:
                    app.logger.error(f"插入评分记录失败: {str(insert_error)}, 条文号: {clause_number}")
                    continue
            
            # 提交事务
            db.session.commit()
            app.logger.info(f"成功插入 {insert_count} 条评分记录, 条文号: {', '.join(saved_clauses[:10])}...(共{len(saved_clauses)}条)")
            
            # 缓存键
            cache_key = get_scores_cache_key(level, specialty, project_id, standard)
            
            # 清除缓存
            if cache.has(cache_key):
                cache.delete(cache_key)
                app.logger.info(f"清除缓存: {cache_key}")
            
            # 清除所有相关缓存，确保评分信息完全刷新
            cache_keys_to_clear = []
            
            # 1. 清除原始专业名称的缓存
            if original_specialty != specialty:
                original_cache_key = get_scores_cache_key(level, original_specialty, project_id, standard)
                cache_keys_to_clear.append(original_cache_key)
            
            # 2. 清除评分汇总缓存
            summary_cache_key = f"score_summary_{project_id}"
            cache_keys_to_clear.append(summary_cache_key)
            
            # 3. 清除所有专业的缓存
            all_specialties = ['建筑', '结构', '给排水', '暖通', '电气', '智能化', '景观']
            for other_specialty in all_specialties:
                other_cache_key = get_scores_cache_key(level, other_specialty, project_id, standard)
                cache_keys_to_clear.append(other_cache_key)
                
            # 批量清除所有相关缓存
            for key in cache_keys_to_clear:
                if cache.has(key):
                    cache.delete(key)
                    app.logger.info(f"清除相关缓存: {key}")
            
            # 返回成功响应
            return jsonify({
                'success': True,
                'message': f'成功保存 {insert_count} 条评分记录',
                'saved_count': insert_count
            }), 200
        
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            app.logger.error(f"保存评分数据失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            
            return jsonify({'error': f'保存评分数据失败: {str(e)}'}), 500
    
    except Exception as e:
        app.logger.error(f"处理保存评分请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500

# 注册蓝图
app.register_blueprint(admin_app, url_prefix='/admin')  # 使用admin_app，添加/admin前缀

@app.route('/api/project_scores', methods=['GET'])
def get_project_scores():
    """获取项目特定级别和专业的评分数据"""
    try:
        # 获取请求参数
        project_id = request.args.get('project_id')
        level = request.args.get('level')
        specialty = request.args.get('specialty')
        standard = request.args.get('standard', '成都市标')
        
        # 验证必要参数
        if not project_id:
            return jsonify({'error': '缺少必要参数: project_id'}), 400
        
        # 将项目ID转换为整数
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            return jsonify({'error': '项目ID必须是整数'}), 400
        
        # 构建查询条件
        query_conditions = {
            '项目ID': project_id
        }
        
        # 如果指定了级别，添加到查询条件
        if level:
            query_conditions['评价等级'] = level
            
        # 如果指定了专业，添加到查询条件
        if specialty:
            query_conditions['专业'] = specialty
        
        # 查询得分表数据
        query = """
        SELECT `条文号`, `分类`, `是否达标`, `得分`, `技术措施`, `专业`, `评价等级`
        FROM `得分表`
        WHERE `项目ID` = :project_id
        """
        
        params = {"project_id": project_id}
        
        # 添加额外的查询条件
        if level:
            query += " AND `评价等级` = :level"
            params["level"] = level
            
        if specialty:
            query += " AND `专业` = :specialty"
            params["specialty"] = specialty
        
        # 执行查询
        result = db.session.execute(text(query), params)
        
        # 获取结果
        scores = []
        for row in result.fetchall():
            scores.append({
                'clause_number': row[0],
                'category': row[1],
                'is_achieved': row[2],
                'score': row[3],
                'technical_measures': row[4],
                'specialty': row[5],
                'level': row[6]
            })
        
        # 判断是否有记录
        has_scores = len(scores) > 0
        
        # 返回结果
        return jsonify({
            'success': True,
            'has_scores': has_scores,
            'score_count': len(scores),
            'sample_scores': scores
        })
    except Exception as e:
        app.logger.error(f"获取项目评分数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'获取项目评分数据失败: {str(e)}'}), 500
@app.route('/api/self-assessment-report', methods=['POST'])
def handle_self_assessment_report():
    """
    处理生成绿建自评估报告的请求
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 提取必要参数
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({"error": "缺少项目ID参数"}), 400
        
        # 添加use_cache参数，默认为False，强制从数据库获取最新数据
        request_data = {
            'project_id': project_id,
            'use_cache': False
        }
        
        # 调用generate_self_assessment_report函数
        return generate_self_assessment_report(request_data)
    except Exception as e:
        app.logger.error(f"处理生成绿建自评估报告请求失败: {str(e)}")
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500
@app.route('/api/generateljzpwb', methods=['POST'])
def handle_generateljzpwb():
    """
    处理生成绿建专篇文本的请求
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 提取必要参数
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({"error": "缺少项目ID参数"}), 400
        
        # 添加use_cache参数，默认为False，强制从数据库获取最新数据
        request_data = {
            'project_id': project_id,
            'use_cache': False
        }
        
        # 调用generate_self_assessment_report函数
        return generate_generateljzpwb(request_data)
    except Exception as e:
        app.logger.error(f"处理生成绿建专篇文本请求失败: {str(e)}")
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500

# 添加路由处理公共交通报告生成请求
@app.route('/generate_transport_report', methods=['POST'])
def handle_transport_report():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        # 调用报告生成函数
        output_path = generate_transport_report(data)
        
        # 检查生成的文件是否存在
        if not os.path.exists(output_path):
            return jsonify({'success': False, 'error': '报告生成失败，文件未创建'}), 500
        
        # 获取文件名为项目名称加报告类型
        file_name = os.path.basename(output_path)
        
        try:
            # 尝试获取项目名称来为文件命名
            project_info = data.get('project_info', {})
            project_name = ""
            if isinstance(project_info, dict):
                project_name = project_info.get('项目名称') or project_info.get('projectName') or ""
            
            # 如果有项目名称则使用项目名称作为文件名
            if project_name:
                file_name = f"{project_name}_公共交通站点分析报告.docx"
            else:
                file_name = "公共交通站点分析报告.docx"
                
            app.logger.info(f"准备发送文件：{file_name}")
            
            # 直接发送文件给用户下载
            try:
                # 确保文件名是纯ASCII或正确编码的
                # Flask 2.2.3版本的send_file能够自动处理下载文件名的编码
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=file_name,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            except Exception as dlerr:
                app.logger.error(f"直接发送文件失败: {str(dlerr)}")
                # 尝试更简单的方式，让Flask自动处理文件名编码
                return send_file(
                    output_path,
                    as_attachment=True
                )
            
        except Exception as file_error:
            app.logger.error(f"发送文件失败: {str(file_error)}")
            app.logger.error(traceback.format_exc())
            
            # 发送失败时回退到旧方式 - 通过URL方式
            # 复制到static/exports目录
            if not os.path.exists('static/exports'):
                os.makedirs('static/exports', exist_ok=True)
                
            target_path = os.path.join('static/exports', file_name)
            import shutil
            shutil.copy2(output_path, target_path)
            
            # 构建文件URL
            file_url = '/static/exports/' + file_name
            
            app.logger.info(f"使用备用方式发送文件，URL: {file_url}")
            
            # 返回文件URL
            return jsonify({
                'success': True,
                'file_url': file_url,
                'message': '公共交通分析报告生成成功(使用URL方式)'
            })
    
    except Exception as e:
        app.logger.error(f"生成公共交通分析报告失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/extract_project_info', methods=['POST'])
def extract_project_info_api():
    """提取Word文档中的项目信息并返回"""
    try:
        app.logger.info("收到提取项目信息请求")
        app.logger.info(f"请求表单数据: {request.form.keys()}")
        app.logger.info(f"请求文件: {request.files.keys()}")
        
        # 检查是否有文件上传
        if 'word_file' not in request.files and 'image_file' not in request.files and 'file' not in request.files:
            app.logger.error("未找到上传的文件")
            return jsonify({'success': False, 'message': '未找到上传的文件'}), 400
        
        if 'word_file' in request.files:
            # Word文件处理逻辑保持不变...
            file = request.files['word_file']
            if file.filename == '':
                app.logger.error("未选择Word文件")
                return jsonify({'success': False, 'message': '未选择文件'}), 400
                
            # 检查文件扩展名
            if not file.filename.endswith(('.doc', '.docx')):
                app.logger.error(f"不支持的文件格式: {file.filename}")
                return jsonify({'success': False, 'message': '仅支持.doc和.docx格式的Word文档'}), 400
                
            # 创建临时目录（如果不存在）
            temp_dir = os.path.join('static', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 保存上传的文件
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file_path = os.path.join(temp_dir, f"{timestamp}_{werkzeug.utils.secure_filename(file.filename)}")
            file.save(file_path)
            
            app.logger.info(f"已保存Word文件: {file_path}")
            
            # 调用extract_doc_info函数提取信息
            from utils.word_extractor import extract_doc_info
            project_info = extract_doc_info(file_path)
            
            # 文件使用完毕后删除
            try:
                os.remove(file_path)
                app.logger.info(f"已删除临时文件: {file_path}")
            except Exception as e:
                app.logger.warning(f"删除临时文件失败: {str(e)}")
        
        elif 'image_file' in request.files or 'file' in request.files:
            # 支持 'image_file' 或 'file' 参数名
            file = request.files.get('image_file') or request.files.get('file')
            app.logger.info(f"处理图片文件: {file.filename if file else 'None'}")
            
            if file.filename == '':
                app.logger.error("未选择图片文件")
                return jsonify({'success': False, 'message': '未选择文件'}), 400
                
            # 检查文件扩展名
            if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                app.logger.error(f"不支持的图片格式: {file.filename}")
                return jsonify({'success': False, 'message': '仅支持JPG、PNG、BMP和TIFF格式的图片'}), 400
            
            # 使用图像提取函数处理图片
            try:
                from utils.image_extractor import extract_image_info_with_raw_text
                app.logger.info("调用图像提取函数...")
                result = extract_image_info_with_raw_text(file)
                app.logger.info(f"图像提取函数返回结果: {result.keys() if result else 'None'}")
                
                # 解析结果
                if result and 'raw_text' in result:
                    raw_text = result['raw_text']
                    project_info = result['project_info']
                    app.logger.info(f"成功提取到文本，长度: {len(raw_text)}")
                    app.logger.info(f"提取到项目信息: {len(project_info)} 项")
                else:
                    app.logger.warning("图像提取函数返回无效结果，没有raw_text字段")
                    raw_text = ""
                    project_info = {}
                
                # 无论是否成功提取项目信息，都记录原始文本
                if raw_text:
                    app.logger.info("OCR提取的原始文本长度: " + str(len(raw_text)))
                    app.logger.info("OCR文本前200字符: " + raw_text[:200].replace('\n', ' '))
                    # 将完整文本记录到文件中以便分析
                    try:
                        log_dir = 'logs'
                        os.makedirs(log_dir, exist_ok=True)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        log_file = os.path.join(log_dir, f"ocr_text_{timestamp}.txt")
                        with open(log_file, 'w', encoding='utf-8') as f:
                            f.write(raw_text)
                        app.logger.info(f"OCR完整文本已保存到: {log_file}")
                    except Exception as e:
                        app.logger.warning(f"保存OCR文本到文件失败: {str(e)}")
                else:
                    app.logger.warning("未能提取到任何文本")
                    
                if not project_info:
                    app.logger.warning(f"未能从图片中提取到有效信息")
                    return jsonify({
                        'success': False, 
                        'message': '未能从图片中识别到项目信息，请尝试使用更清晰的图片或确保图片中包含项目相关文字'
                    }), 400
                    
                # 记录成功提取的信息
                app.logger.info(f"成功从图片提取到信息: {len(project_info)} 项")
                app.logger.debug(f"提取的信息内容: {project_info}")
                
            except Exception as e:
                error_msg = str(e)
                app.logger.error(f"图片处理出现错误: {error_msg}")
                app.logger.error(traceback.format_exc())
                return jsonify({'success': False, 'message': f'处理图片时出错: {error_msg}'}), 500
        
        if project_info:
            app.logger.info(f"成功提取项目信息: {project_info}")
            return jsonify({'success': True, 'info': project_info})
        else:
            app.logger.error("提取项目信息失败")
            return jsonify({'success': False, 'message': '无法从文件中提取项目信息'}), 400
            
    except Exception as e:
        app.logger.error(f"处理文件时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'处理请求失败: {str(e)}'}), 500

@app.route('/log-js-error', methods=['POST'])
def log_js_error():
    """记录前端JavaScript加载错误"""
    try:
        data = request.get_json()
        error_type = data.get('type', 'unknown')
        error_message = data.get('message', 'No message')
        error_url = data.get('url', 'No URL')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        print(f"前端JS错误: {error_type} - {error_message} - URL: {error_url} - User-Agent: {user_agent}")
        
        # 这里可以将错误记录到日志文件或数据库中
        
        return jsonify({"status": "success", "message": "Error logged successfully"})
    except Exception as e:
        print(f"记录JS错误时出现异常: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/dashboard')
@login_required
def user_dashboard():
    # 获取show_solar参数和show_decorative参数
    show_solar = request.args.get('show_solar', '0')
    show_decorative = request.args.get('show_decorative', '0')
    project_id = request.args.get('project_id')
    
    # 如果请求查看太阳能计算器或装饰性构件造价计算器且有项目ID，获取项目信息
    project = None
    if project_id:
        project = db.session.get(Project, project_id)
    
    # 设置当前页面
    current_page = 'project_info'  # 默认页面
    
    # 根据参数决定显示哪个组件
    if show_solar == '1':
        current_page = 'solar_calculator'
    elif show_decorative == '1':
        current_page = 'decorative_cost_calculator'
    
    return render_template('dashboard.html', project=project, current_page=current_page)

# 项目协作相关API

# 获取项目协作者列表
@app.route('/api/projects/<int:project_id>/collaborators', methods=['GET'])
@login_required
def get_project_collaborators(project_id):
    try:
        # 检查项目访问权限
        permissions = get_project_permissions(project_id)
        if not permissions:
            return jsonify({'error': '您没有权限访问该项目'}), 403
        
        # 获取项目信息
        project = Project.query.get_or_404(project_id)
        
        # 获取项目创建者信息
        creator = User.query.get(project.user_id)
        
        # 获取项目所有协作者
        collaborators = ProjectCollaborator.query.filter_by(project_id=project_id).all()
        
        # 构建协作者列表
        collaborator_list = []
        for collab in collaborators:
            user = User.query.get(collab.user_id)
            if user:
                collaborator_list.append({
                    'id': collab.id,
                    'user_id': user.id,
                    'email': user.email,
                    'nickname': user.nickname or user.email.split('@')[0],  # 添加昵称，如果没有则使用邮箱前缀
                    'role': collab.role,
                    'permissions': collab.permissions,
                    'joined_at': collab.joined_at.strftime('%Y-%m-%d %H:%M:%S') if collab.joined_at else None,
                    'is_creator': (user.id == project.user_id)
                })
        
        # 构建项目信息
        project_info = {
            'id': project.id,
            'name': project.name,
            'creator': {
                'id': creator.id if creator else None,
                'email': creator.email if creator else None,
                'nickname': creator.nickname or creator.email.split('@')[0] if creator else None  # 添加创建者昵称
            },
            'collaborators': collaborator_list
        }
        
        return jsonify({
            'success': True,
            'project': project_info
        })
    except Exception as e:
        app.logger.error(f"获取项目协作者列表失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'获取项目协作者列表失败: {str(e)}'}), 500

# 导入需要的模块
import secrets
import hashlib
from datetime import timedelta

# 生成项目分享链接
@app.route('/api/projects/<int:project_id>/share', methods=['POST'])
@login_required
def generate_share_link(project_id):
    try:
        # 检查是否为项目创建者或有管理权限的协作者
        permissions = get_project_permissions(project_id)
        if not permissions or permissions['permissions'] != '管理':
            return jsonify({'error': '您没有权限分享该项目'}), 403
        
        data = request.get_json()
        expires_days = data.get('expires_days', 7)  # 默认7天有效期
        collaborator_permissions = data.get('permissions', '只读')  # 默认只读权限
        
        # 生成随机令牌
        token = secrets.token_hex(32)
        
        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # 创建邀请记录
        invitation = ProjectInvitation(
            project_id=project_id,
            token=token,
            permissions=collaborator_permissions,
            created_by=session.get('user_id'),
            expires_at=expires_at,
            is_active=True
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        # 构建分享链接
        share_link = f"{request.host_url.rstrip('/')}/join_project?token={token}"
        
        return jsonify({
            'success': True,
            'share_link': share_link,
            'token': token,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'permissions': collaborator_permissions
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"生成项目分享链接失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'生成项目分享链接失败: {str(e)}'}), 500

# 通过分享链接加入项目
@app.route('/join_project', methods=['GET'])
def join_project_page():
    token = request.args.get('token')
    if not token:
        flash('无效的邀请链接', 'error')
        return redirect(url_for('index'))
    
    # 检查令牌是否有效
    invitation = ProjectInvitation.query.filter_by(token=token, is_active=True).first()
    if not invitation or invitation.is_expired():
        flash('邀请链接已过期或无效', 'error')
        return redirect(url_for('index'))
    
    # 检查用户是否已登录
    if 'user_id' not in session:
        # 将令牌保存到session，登录后再处理
        session['pending_invitation'] = token
        flash('请先登录以加入项目', 'info')
        return redirect(url_for('login_page'))
    
    # 检查用户是否已经是项目协作者
    user_id = session.get('user_id')
    existing = ProjectCollaborator.query.filter_by(
        project_id=invitation.project_id,
        user_id=user_id
    ).first()
    
    if existing:
        # 如果已经是协作者，直接进入项目
        flash('您已经是该项目的协作者', 'info')
        return redirect(url_for('project_detail', project_id=invitation.project_id))
    
    # 获取项目信息
    project = Project.query.get_or_404(invitation.project_id)
    
    # 添加用户为项目协作者
    collaborator = ProjectCollaborator(
        project_id=invitation.project_id,
        user_id=user_id,
        role='参与者',
        permissions=invitation.permissions,
        invited_by=invitation.created_by
    )
    
    try:
        db.session.add(collaborator)
        
        # 可选：标记邀请为已使用
        # invitation.is_active = False
        
        db.session.commit()
        flash(f'您已成功加入项目：{project.name}', 'success')
        return redirect(url_for('project_detail', project_id=invitation.project_id))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"加入项目失败: {str(e)}")
        flash('加入项目失败，请稍后重试', 'error')
        return redirect(url_for('index'))

# 处理登录后的待处理邀请
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': '请输入邮箱和密码'}), 400
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin()
        
        # 更新最后在线时间
        user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # 处理待处理的项目邀请
        pending_invitation = session.pop('pending_invitation', None)
        redirect_url = url_for('project_management')
        
        if pending_invitation:
            invitation = ProjectInvitation.query.filter_by(token=pending_invitation, is_active=True).first()
            if invitation and not invitation.is_expired():
                # 检查用户是否已经是项目协作者
                existing = ProjectCollaborator.query.filter_by(
                    project_id=invitation.project_id,
                    user_id=user.id
                ).first()
                
                if not existing:
                    # 添加用户为项目协作者
                    collaborator = ProjectCollaborator(
                        project_id=invitation.project_id,
                        user_id=user.id,
                        role='参与者',
                        permissions=invitation.permissions,
                        invited_by=invitation.created_by
                    )
                    
                    try:
                        db.session.add(collaborator)
                        db.session.commit()
                        redirect_url = url_for('project_detail', project_id=invitation.project_id)
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error(f"处理邀请失败: {str(e)}")
                else:
                    redirect_url = url_for('project_detail', project_id=invitation.project_id)
        
        # 记录登录成功日志
        LogRecord.add_log(
            level="INFO",
            message=f"用户 {email} 登录成功",
            source="login",
            user_id=user.id,
            ip_address=request.remote_addr,
            path=request.path,
            method=request.method,
            user_agent=request.user_agent.string
        )
        
        return jsonify({
            'success': True, 
            'redirect': redirect_url,
            'is_admin': user.is_admin()
        })
    else:
        # 记录登录失败日志
        LogRecord.add_log(
            level="WARNING",
            message=f"用户 {email} 登录失败",
            source="login",
            ip_address=request.remote_addr,
            path=request.path,
            method=request.method,
            user_agent=request.user_agent.string
        )
        
        return jsonify({'error': '邮箱或密码错误'}), 401

# 移除项目协作者
@app.route('/api/projects/<int:project_id>/collaborators/<int:collaborator_id>', methods=['DELETE'])
@login_required
def remove_collaborator(project_id, collaborator_id):
    try:
        # 检查是否为项目创建者或有管理权限的协作者
        permissions = get_project_permissions(project_id)
        if not permissions or permissions['permissions'] != '管理':
            return jsonify({'error': '您没有权限管理协作者'}), 403
        
        # 获取协作者信息
        collaborator = ProjectCollaborator.query.get_or_404(collaborator_id)
        
        # 检查要删除的是否是项目关联的协作者
        if collaborator.project_id != project_id:
            return jsonify({'error': '协作者ID与项目不匹配'}), 400
        
        # 阻止删除创建者
        if collaborator.role == '创建者':
            return jsonify({'error': '无法移除项目创建者'}), 400
        
        # 删除协作者
        db.session.delete(collaborator)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '已移除协作者'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"移除协作者失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'移除协作者失败: {str(e)}'}), 500

# 更新协作者权限
@app.route('/api/projects/<int:project_id>/collaborators/<int:collaborator_id>', methods=['PUT'])
@login_required
def update_collaborator_permissions(project_id, collaborator_id):
    try:
        # 检查是否为项目创建者或有管理权限的协作者
        permissions = get_project_permissions(project_id)
        if not permissions or permissions['permissions'] != '管理':
            return jsonify({'error': '您没有权限管理协作者'}), 403
        
        data = request.get_json()
        new_permissions = data.get('permissions')
        
        if not new_permissions or new_permissions not in ['只读', '编辑', '管理']:
            return jsonify({'error': '无效的权限设置'}), 400
        
        # 获取协作者信息
        collaborator = ProjectCollaborator.query.get_or_404(collaborator_id)
        
        # 检查协作者是否属于当前项目
        if collaborator.project_id != project_id:
            return jsonify({'error': '协作者ID与项目不匹配'}), 400
        
        # 阻止修改创建者权限
        if collaborator.role == '创建者':
            return jsonify({'error': '无法修改项目创建者的权限'}), 400
        
        # 更新权限
        collaborator.permissions = new_permissions
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '协作者权限已更新',
            'collaborator': collaborator.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新协作者权限失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'更新协作者权限失败: {str(e)}'}), 500

# 获取项目分享链接
@app.route('/api/projects/<int:project_id>/invitations', methods=['GET'])
@login_required
def get_project_invitations(project_id):
    try:
        # 检查是否为项目创建者或有管理权限的协作者
        permissions = get_project_permissions(project_id)
        if not permissions or permissions['permissions'] != '管理':
            return jsonify({'error': '您没有权限查看邀请链接'}), 403
        
        # 获取项目的所有活跃邀请
        invitations = ProjectInvitation.query.filter_by(
            project_id=project_id,
            is_active=True
        ).all()
        
        # 构建邀请列表
        invitation_list = []
        for inv in invitations:
            # 跳过已过期的邀请
            if inv.is_expired():
                continue
                
            creator = User.query.get(inv.created_by)
            invitation_list.append({
                'id': inv.id,
                'token': inv.token,
                'permissions': inv.permissions,
                'creator': creator.email if creator else None,
                'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S') if inv.created_at else None,
                'expires_at': inv.expires_at.strftime('%Y-%m-%d %H:%M:%S') if inv.expires_at else None,
                'share_link': f"{request.host_url.rstrip('/')}/join_project?token={inv.token}"
            })
        
        return jsonify({
            'success': True,
            'invitations': invitation_list
        })
    except Exception as e:
        app.logger.error(f"获取项目邀请链接失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'获取项目邀请链接失败: {str(e)}'}), 500

# 撤销项目邀请链接
@app.route('/api/projects/<int:project_id>/invitations/<int:invitation_id>', methods=['DELETE'])
@login_required
def revoke_invitation(project_id, invitation_id):
    try:
        # 检查是否为项目创建者或有管理权限的协作者
        permissions = get_project_permissions(project_id)
        if not permissions or permissions['permissions'] != '管理':
            return jsonify({'error': '您没有权限撤销邀请链接'}), 403
        
        # 获取邀请信息
        invitation = ProjectInvitation.query.get_or_404(invitation_id)
        
        # 检查邀请是否属于当前项目
        if invitation.project_id != project_id:
            return jsonify({'error': '邀请ID与项目不匹配'}), 400
        
        # 撤销邀请
        invitation.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '邀请已撤销'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"撤销邀请失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'撤销邀请失败: {str(e)}'}), 500

# 离开项目（协作者主动离开）
@app.route('/api/projects/<int:project_id>/leave', methods=['POST'])
@login_required
def leave_project(project_id):
    try:
        user_id = session.get('user_id')
        
        # 获取项目信息
        project = Project.query.get_or_404(project_id)
        
        # 检查用户是否为项目创建者
        if project.user_id == user_id:
            return jsonify({'error': '项目创建者不能离开项目'}), 400
        
        # 获取协作者记录
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if not collaborator:
            return jsonify({'error': '您不是该项目的协作者'}), 404
        
        # 删除协作者记录
        db.session.delete(collaborator)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '您已成功离开项目'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"离开项目失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'离开项目失败: {str(e)}'}), 500

# 获取用户对项目的权限
def get_project_permissions(project_id):
    """获取当前用户对项目的权限"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return None
        
        # 检查是否为项目创建者
        project = Project.query.filter_by(id=project_id, user_id=user_id).first()
        if project:
            return {
                'role': '创建者',
                'permissions': '管理'  # 创建者拥有最高权限
            }
        
        # 检查是否为项目协作者
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id, 
            user_id=user_id
        ).first()
        
        if collaborator:
            return {
                'role': collaborator.role,
                'permissions': collaborator.permissions
            }
        
        return None
    except Exception as e:
        print(f"获取项目权限失败: {str(e)}")
        return None

# 获取用户对项目的权限API
@app.route('/api/projects/<int:project_id>/permissions', methods=['GET'])
@login_required
def get_user_project_permissions(project_id):
    try:
        permissions = get_project_permissions(project_id)
        if not permissions:
            return jsonify({
                'success': False,
                'error': '您没有权限访问该项目'
            }), 403
        
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    except Exception as e:
        app.logger.error(f"获取项目权限失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'获取权限失败: {str(e)}'
        }), 500

# 用户个人设置API
@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    # 检查用户是否已登录
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 查询用户信息
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if request.method == 'GET':
        # 返回用户信息
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        
        try:
            # 更新用户信息
            if 'nickname' in data:
                user.nickname = data['nickname']
            if 'gender' in data:
                user.gender = data['gender']
            if 'avatar_index' in data:
                user.avatar_index = data['avatar_index']
            
            # 保存到数据库
            db.session.commit()
            
            # 更新session中的昵称
            session['nickname'] = user.nickname
            
            return jsonify({
                'success': True,
                'message': '个人信息更新成功',
                'user': user.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"更新用户信息时出错: {str(e)}")
            return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500
# 添加新的路由用于根据条文号查询得分
@app.route('/api/get_score_by_clause', methods=['POST'])
def get_score_by_clause():
    """
    根据条文号查询得分
    
    请求参数:
    {
        "project_id": 1,                 // 项目ID
        "clause_number": "3.1.2.14",     // 条文号
        "standard": "成都市标"            // 评价标准
    }
    
    响应:
    {
        "success": true,                 // 是否成功
        "message": "查询成功",            // 消息
        "clause_number": "3.1.2.14",     // 条文号
        "score": 12,                     // 得分值
        "category": "资源节约",           // 分类
        "specialty": "建筑专业",          // 专业
        "is_achieved": "true"            // 是否达标
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '未接收到JSON数据'
            }), 400
        
        # 验证必要参数
        project_id = data.get('project_id')
        clause_number = data.get('clause_number')
        standard = data.get('standard', '成都市标')
        
        # 记录请求信息
        app.logger.info(f"接收到查询请求: 项目ID={project_id}, 条文号={clause_number}, 标准={standard}")
        
        # 验证必要参数
        if not all([project_id, clause_number]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: project_id, clause_number'
            }), 400
        
        try:
            # 查询记录
            query = """
            SELECT `条文号`, `分类`, `专业`, `是否达标`, `得分`
            FROM `得分表`
            WHERE `项目ID` = :project_id AND `条文号` = :clause_number AND `评价标准` = :standard
            """
            result = db.session.execute(
                text(query), 
                {"project_id": project_id, "clause_number": clause_number, "standard": standard}
            )
            row = result.fetchone()
            
            if row:
                # 返回成功响应
                return jsonify({
                    'success': True,
                    'message': '查询成功',
                    'clause_number': row[0],
                    'category': row[1],
                    'specialty': row[2],
                    'is_achieved': row[3],
                    'score': row[4]
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'未找到条文 {clause_number} 的记录'
                }), 404
        
        except Exception as e:
            app.logger.error(f"数据库查询失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'数据库查询失败: {str(e)}'
            }), 500
    
    except Exception as e:
        app.logger.error(f"处理请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    # 根据环境变量决定是否开启调试模式
    debug_mode = not is_production
    app.logger.info(f"应用启动: 调试模式={debug_mode}")
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5050)))