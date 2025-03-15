from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
import urllib.parse
import traceback
import time
import sqlite3
import pyodbc
from sqlalchemy import text
import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS

# 加载环境变量
load_dotenv()

# 创建日志目录
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('greenscore')
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
logger.addHandler(handler)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.logger = logger

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
# 优先使用环境变量中的数据库连接字符串
db_uri = os.environ.get('DATABASE_URL')
if not db_uri:
    # 如果环境变量未设置，使用默认连接字符串
    db_uri = "mssql+pyodbc://test:123456@acbim.fun/绿色建筑?driver=ODBC+Driver+17+for+SQL+Server"
    app.logger.warning("警告: DATABASE_URL 环境变量未设置，使用默认连接字符串")

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
# 安全地获取数据库URL并打印
masked_url = db_uri.replace(':' + db_uri.split(':')[2].split('@')[0] + '@', ':***@')
app.logger.info(f"使用SQL Server数据库: {masked_url}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = not is_production  # 仅在非生产环境打印SQL语句

# 定义级别与属性的映射关系
LEVEL_TO_ATTRIBUTE = {
    '基本级': '控制项',
    '提高级': '评分项'
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
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
    underground_floor_area = db.Column(db.Float)  # 地下一层建筑面积
    ground_parking_spaces = db.Column(db.Integer)  # 地面停车位数量
    plot_ratio = db.Column(db.Float)  # 容积率
    building_base_area = db.Column(db.Float)  # 建筑基底面积
    building_density = db.Column(db.Float)  # 建筑密度
    green_area = db.Column(db.Float)  # 绿地面积
    green_ratio = db.Column(db.Float)  # 绿地率
    residential_units = db.Column(db.Integer)  # 住宅户数
    building_floors = db.Column(db.String(20))  # 建筑层数（地上/地下）
    building_height = db.Column(db.Float)  # 建筑高度
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
    
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'construction_unit': self.construction_unit,
            'design_unit': self.design_unit,
            'location': self.location,
            'building_area': self.building_area,
            'standard': self.standard,
            'building_type': self.building_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            # 新增字段
            'climate_zone': self.climate_zone,
            'star_rating_target': self.star_rating_target,
            'total_land_area': self.total_land_area,
            'total_building_area': self.total_building_area,
            'above_ground_area': self.above_ground_area,
            'underground_area': self.underground_area,
            'underground_floor_area': self.underground_floor_area,
            'ground_parking_spaces': self.ground_parking_spaces,
            'plot_ratio': self.plot_ratio,
            'building_base_area': self.building_base_area,
            'building_density': self.building_density,
            'green_area': self.green_area,
            'green_ratio': self.green_ratio,
            'residential_units': self.residential_units,
            'building_floors': self.building_floors,
            'building_height': self.building_height,
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
        }

# 添加四川省标和通用国标的模型
class StandardSichuan(db.Model):
    __tablename__ = '四川省标'
    
    # 使用中文字段名
    序号 = db.Column(db.Integer, primary_key=True)
    条文号 = db.Column(db.String(20))
    分类 = db.Column(db.String(50))
    专业 = db.Column(db.String(50))
    条文内容 = db.Column(db.Text)
    分值 = db.Column(db.String(10))
    审查材料 = db.Column(db.Text)
    属性 = db.Column(db.String(20))  # 属性字段，包含控制项、评分项

class StandardNational(db.Model):
    __tablename__ = '国标'
    
    # 使用中文字段名
    序号 = db.Column(db.Integer, primary_key=True)
    条文号 = db.Column(db.String(20))
    分类 = db.Column(db.String(50))
    专业 = db.Column(db.String(50))
    条文内容 = db.Column(db.Text)
    分值 = db.Column(db.String(10))
    审查材料 = db.Column(db.Text)
    属性 = db.Column(db.String(20))  # 属性字段，包含控制项、评分项

class Standard(db.Model):
    __tablename__ = '成都市标'
    
    # 使用中文字段名
    序号 = db.Column(db.Integer, primary_key=True)
    条文号 = db.Column(db.String(20))
    分类 = db.Column(db.String(50))
    专业 = db.Column(db.String(50))
    条文内容 = db.Column(db.Text)
    分值 = db.Column(db.String(10))
    审查材料 = db.Column(db.Text)
    属性 = db.Column(db.String(20))  # 属性字段，包含控制项、评分项

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

# 缓存所有数据的函数
@cache.cached(key_prefix='all_standards')
def get_all_standards():
    print("从数据库获取所有标准数据...")
    start_time = time.time()
    standards = Standard.query.all()
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
    
    # 根据标准名称选择对应的模型
    if standard_name == '成都市标':
        model_class = Standard
    elif standard_name == '四川省标':
        model_class = StandardSichuan
    elif standard_name == '国标':
        model_class = StandardNational
    else:
        model_class = Standard
    
    # 尝试多种筛选方法
    standards = []
    
    # 方法1: 使用属性字段精确匹配
    if attribute and specialty:
        try:
            query1 = model_class.query.filter(getattr(model_class, '属性') == attribute).filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            standards1 = query1.all()
            print(f"方法1 (属性精确匹配): 找到 {len(standards1)} 条记录")
            if standards1:
                standards = standards1
        except Exception as e:
            print(f"方法1查询错误: {str(e)}")
    
    # 方法2: 使用属性字段模糊匹配
    if not standards and attribute:
        try:
            query2 = model_class.query
            query2 = query2.filter(getattr(model_class, '属性').like(f'%{attribute}%'))
            if specialty:
                query2 = query2.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            standards2 = query2.all()
            print(f"方法2 (属性模糊匹配): 找到 {len(standards2)} 条记录")
            if standards2:
                standards = standards2
        except Exception as e:
            print(f"方法2查询错误: {str(e)}")
    
    # 方法3: 只按专业筛选
    if not standards and specialty:
        try:
            query3 = model_class.query.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            standards3 = query3.all()
            print(f"方法3 (仅按专业): 找到 {len(standards3)} 条记录")
            if standards3:
                standards = standards3
        except Exception as e:
            print(f"方法3查询错误: {str(e)}")
    
    # 方法4: 使用SQL文本查询
    if not standards:
        try:
            sql = f"SELECT * FROM [{model_class.__tablename__}]"
            conditions = []
            if attribute:
                conditions.append(f"属性 = N'{attribute}'")
            if specialty:
                conditions.append(f"专业 LIKE N'%{specialty}%'")
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            print(f"执行SQL: {sql}")
            result = db.session.execute(text(sql))
            standards = [dict(zip(result.keys(), row)) for row in result]
            print(f"方法4 (SQL文本查询): 找到 {len(standards)} 条记录")
        except Exception as e:
            print(f"方法4查询错误: {str(e)}")
    
    # 如果所有方法都失败，返回所有记录
    if not standards:
        try:
            standards = model_class.query.all()
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
    if standard_name == '成都市标':
        return Standard.query.all()
    elif standard_name == '四川省标':
        return StandardSichuan.query.all()
    elif standard_name == '通用国标' or standard_name == '国标':
        return StandardNational.query.all()
    else:
        # 默认返回成都市标
        return Standard.query.all()

# 获取项目信息
def get_project(project_id=None):
    try:
        if project_id:
            # 获取指定ID的项目
            project = Project.query.get(project_id)
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
        project_id = form_data.get('project_id')
        if project_id:
            try:
                project_id = int(project_id)
            except ValueError:
                project_id = None
        
        # 如果有项目ID，获取现有项目；否则创建新项目
        if project_id:
            project = Project.query.get(project_id)
            if not project:
                print(f"未找到ID为{project_id}的项目，创建新项目")
                project = Project()
        else:
            print("未提供项目ID，创建新项目")
            project = Project()
        
        # 检查是否是详细信息表单
        is_detail_form = form_data.get('detail_form') == '1'
        print(f"表单类型: {'详细信息表单' if is_detail_form else '基本信息表单'}")
        
        # 如果不是详细信息表单，则更新基本信息
        if not is_detail_form:
            # 更新项目属性 - 基本信息
            project.name = form_data.get('project_name', '')
            project.code = form_data.get('project_code', '')
            project.construction_unit = form_data.get('construction_unit', '')
            project.design_unit = form_data.get('design_unit', '')
            project.location = form_data.get('project_location', '')
            project.building_type = form_data.get('building_type', '')
            project.standard = form_data.get('standard_selection', '')  # 保存评价标准
            project.climate_zone = form_data.get('climate_zone', '')
            project.star_rating_target = form_data.get('star_rating_target', '')
        
        # 处理数值字段 - 建筑面积相关（无论是哪种表单都处理这些字段）
        try_parse_float(form_data, 'building_area', project, 'building_area')
        try_parse_float(form_data, 'total_land_area', project, 'total_land_area')
        try_parse_float(form_data, 'total_building_area', project, 'total_building_area')
        try_parse_float(form_data, 'above_ground_area', project, 'above_ground_area')
        try_parse_float(form_data, 'underground_area', project, 'underground_area')
        try_parse_float(form_data, 'first_floor_underground_area', project, 'underground_floor_area')  # 注意字段名不同
        try_parse_float(form_data, 'plot_ratio', project, 'plot_ratio')
        try_parse_float(form_data, 'building_base_area', project, 'building_base_area')
        try_parse_float(form_data, 'building_density', project, 'building_density')
        try_parse_float(form_data, 'green_area', project, 'green_area')
        try_parse_float(form_data, 'green_ratio', project, 'green_ratio')
        try_parse_float(form_data, 'building_height', project, 'building_height')
        
        # 处理整数字段
        try_parse_int(form_data, 'ground_parking_spaces', project, 'ground_parking_spaces')
        try_parse_int(form_data, 'residential_units', project, 'residential_units')
        
        # 处理字符串字段
        project.building_floors = form_data.get('building_floors', '')
        
        # 处理选择字段（如果不是详细信息表单，star_rating_target已在上面处理）
        if is_detail_form:
            # 详细信息表单中不更新star_rating_target，因为它属于基本信息
            pass
        
        project.air_conditioning_type = form_data.get('ac_type', '')  # 注意字段名不同
        project.average_floors = form_data.get('avg_floors', '')  # 注意字段名不同
        project.has_garbage_room = form_data.get('has_garbage_room', '')
        project.has_elevator = form_data.get('has_elevator', '')
        project.has_underground_garage = form_data.get('has_underground_garage', '')
        project.construction_type = form_data.get('construction_type', '')
        project.has_water_landscape = form_data.get('has_water_landscape', '')
        project.is_fully_decorated = form_data.get('is_fully_decorated', '')
        project.public_building_type = form_data.get('public_building_type', '')
        
        # 处理public_green_space字段
        public_green_space = form_data.get('public_green_space', '')
        print(f"处理public_green_space字段: {public_green_space}")
        project.public_green_space = public_green_space
        
        # 打印调试信息
        print(f"保存项目信息: ID={project.id}, 名称={project.name}, 评价标准={project.standard}, 公建类型={project.public_building_type}, 绿地向公众开放={project.public_green_space}")
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        print(f"项目保存成功: ID={project.id}")
        
        # 自动保存基本级和提高级各专业的评分信息
        try:
            # 定义要保存的专业列表
            specialties = ['建筑专业', '结构专业', '给排水专业', '暖通专业', '电气专业']
            levels = ['基本级', '提高级']
            
            # 为每个等级和专业创建初始评分记录
            for level in levels:
                for specialty in specialties:
                    # 创建空的评分数据
                    score_data = {
                        'level': level,
                        'specialty': specialty,
                        'project_id': project.id,
                        'scores': [],
                        'standard': project.standard
                    }
                    
                    # 调用保存评分的函数
                    save_score_for_new_project(score_data)
            
            print(f"已为项目 {project.id} 自动创建评分记录")
        except Exception as e:
            print(f"自动创建评分记录失败: {str(e)}")
            # 不影响项目创建，继续执行
        
        return project
    except Exception as e:
        db.session.rollback()
        print(f"保存项目信息时出错: {str(e)}")
        print(traceback.format_exc())
        return None

# 辅助函数：尝试解析浮点数
def try_parse_float(form_data, form_field, model_obj, model_field):
    value = form_data.get(form_field, '')
    if value:
        try:
            setattr(model_obj, model_field, float(value))
        except ValueError as ve:
            print(f"{form_field}转换错误: {str(ve)}")
            pass

# 辅助函数：尝试解析整数
def try_parse_int(form_data, form_field, model_obj, model_field):
    value = form_data.get(form_field, '')
    if value:
        try:
            setattr(model_obj, model_field, int(value))
        except ValueError as ve:
            print(f"{form_field}转换错误: {str(ve)}")
            pass

# 项目管理页面路由
@app.route('/projects')
def project_management():
    try:
        return render_template('project_management.html')
    except Exception as e:
        print(f"项目管理页面出错: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

# 创建项目路由
@app.route('/create_project', methods=['POST'])
def create_project():
    try:
        # 获取表单数据
        project_name = request.form.get('project_name')
        project_code = request.form.get('project_code')
        construction_unit = request.form.get('construction_unit')
        design_unit = request.form.get('design_unit')
        project_location = request.form.get('project_location')
        standard_selection = request.form.get('standard_selection')
        building_type = request.form.get('building_type')  # 获取建筑类型
        star_rating_target = request.form.get('star_rating_target')  # 获取目标星级
        import_star_case = request.form.get('import_star_case') == 'on'  # 是否导入一星级案例数据
        
        print(f"收到创建项目请求: 名称={project_name}, 标准={standard_selection}, 建筑类型={building_type}, 星级目标={star_rating_target}, 导入一星级案例={import_star_case}")
        print(f"表单数据: {request.form}")
        
        # 验证必填字段
        if not project_name:
            raise ValueError("项目名称不能为空")
        if not standard_selection:
            raise ValueError("评价标准不能为空")
        if not building_type:
            raise ValueError("建筑类型不能为空")
        
        # 创建新项目
        project = Project(
            name=project_name,
            code=project_code,
            construction_unit=construction_unit,
            design_unit=design_unit,
            location=project_location,
            standard=standard_selection,
            building_type=building_type,  # 设置建筑类型
            star_rating_target=star_rating_target  # 设置目标星级
        )
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        print(f"项目创建成功: ID={project.id}, 名称={project_name}, 标准={standard_selection}")
        
        # 自动导入星级案例数据
        try:
            print(f"开始自动导入星级案例数据到项目 {project.id}")
            # 调用API导入星级案例数据，根据项目的评价标准和星级目标
            import_url = f"/api/star_case_scores?target_project_id={project.id}"
            with app.test_client() as client:
                response = client.get(import_url)
                result = response.get_json()
                if result and result.get('success'):
                    print(f"成功导入星级案例数据: {result.get('message')}")
                else:
                    error_msg = result.get('message') if result else "未知错误"
                    print(f"导入星级案例数据失败: {error_msg}")
                    # 如果导入失败，则使用默认方式创建评分记录
                    print("使用默认方式创建评分记录...")
                    # 直接使用SQL为新项目生成所有条文号的默认得分数据
                    create_default_scores(project.id, project.name, standard_selection)
            
        except Exception as import_error:
            print(f"导入星级案例数据出错: {str(import_error)}")
            traceback.print_exc()
            # 如果导入出错，则使用默认方式创建评分记录
            print("使用默认方式创建评分记录...")
            # 直接使用SQL为新项目生成所有条文号的默认得分数据
            create_default_scores(project.id, project.name, standard_selection)
        
        # 重定向到项目详情页面
        return redirect(url_for('project_detail', project_id=project.id))
    except Exception as e:
        db.session.rollback()
        print(f"创建项目出错: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

# 项目详情页面路由
@app.route('/project/<int:project_id>')
def project_detail(project_id):
    try:
        # 获取页面参数
        page = request.args.get('page', 'project_info')
        
        # 获取项目信息
        project = get_project(project_id)
        if not project:
            print(f"项目不存在: ID={project_id}")
            return render_template('error.html', error="项目不存在")
        
        # 获取项目对应标准的数据
        standards = get_standards_by_name(project.standard)
        
        # 打印项目信息，确保建筑类型和标准正确传递
        print(f"项目详情: ID={project.id}, 名称={project.name}, 建筑类型={project.building_type}, 评价标准={project.standard}, 页面={page}")
        print(f"获取到标准数据: {len(standards)}条记录")
        
        # 如果是评分汇总页面，获取评分数据
        score_summary = {}
        if page == 'score_summary':
            # 获取评分汇总数据，强制刷新确保获取最新数据
            score_summary = get_score_summary(project_id, force_refresh=True)
            print(f"获取评分汇总数据: {score_summary}")
        
        # 渲染项目详情页面
        print(f"渲染页面: index.html, current_page={page}")
        return render_template('index.html', 
                              standards=standards, 
                              current_page=page,
                              project=project,
                              score_summary=score_summary)
    except Exception as e:
        print(f"项目详情页面出错: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

# 获取项目列表API
@app.route('/api/projects')
def api_projects():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return jsonify({
            'success': True,
            'projects': [project.to_dict() for project in projects]
        })
    except Exception as e:
        print(f"获取项目列表API出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 删除项目API
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        # 查找项目
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': '项目不存在'
            }), 404
        
        # 删除项目
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'项目 {project.name} 已成功删除'
        })
    except Exception as e:
        db.session.rollback()
        print(f"删除项目API出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/')
def index():
    try:
        # 重定向到项目管理页面
        return redirect(url_for('project_management'))
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

@app.route('/', methods=['POST'])
def handle_form():
    try:
        form_type = request.form.get('form_type', '')
        print(f"接收到表单提交: form_type={form_type}")
        
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
                # 重定向回项目详情页面
                return redirect(url_for('project_detail', project_id=project.id))
            else:
                print("项目信息保存失败，重定向到项目管理页面")
                # 如果保存失败，重定向到项目管理页面
                return redirect(url_for('project_management'))
        else:
            print(f"未知的表单类型: {form_type}")
        
        # 如果不是已知的表单类型，返回首页
        return redirect(url_for('index'))
    except Exception as e:
        print(f"处理表单时发生错误: {str(e)}")
        print(traceback.format_exc())
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
            project = Project.query.get(project_id)
        
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
        
        # 根据标准名称选择对应的模型
        if standard_name == '成都市标':
            model_class = Standard
        elif standard_name == '四川省标':
            model_class = StandardSichuan
        elif standard_name == '国标':
            model_class = StandardNational
        else:
            # 默认使用成都市标
            model_class = Standard
            standard_name = '成都市标'
        
        # 获取属性值
        attribute = LEVEL_TO_ATTRIBUTE.get(level, '')
        
        # 查询数据
        try:
            query = model_class.query
            if attribute:
                query = query.filter(getattr(model_class, '属性') == attribute)
            if specialty:
                query = query.filter(getattr(model_class, '专业').like(f'%{specialty}%'))
            
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
                
                standards = query.all()
                print(f"使用宽松条件从 {standard_name} 获取标准数据: specialty={specialty}, 找到{len(standards)}条记录")
            except Exception as e:
                print(f"宽松查询标准数据出错: {str(e)}")
                print(traceback.format_exc())
        
        # 打印调试信息
        print(f"过滤标准: level={level}, specialty={specialty}, standard={standard_name}, 找到{len(standards)}条记录")
        
        # 渲染模板
        return render_template(
            'index.html', 
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
def calculator():
    try:
        return redirect('/static/calculator.html')
    except Exception as e:
        print(f"加载计算器页面时发生错误: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

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
        data = request.json
        
        if not data:
            return jsonify({'error': '没有收到数据'}), 400
            
        # 检查当前项目
        project = Project.query.first()
        project_id = project.id if project else None
        
        # 查找现有表单数据或创建新的
        form_data = FormData.query.first()
        if not form_data:
            form_data = FormData()
            form_data.project_id = project_id
        
        # 更新表单数据
        form_data.project_name = data.get('projectName', '')
        form_data.building_no = data.get('buildingNo', '')
        form_data.project_location = data.get('projectLocation', '')
        form_data.design_no = data.get('designNo', '')
        form_data.construction_unit = data.get('constructionUnit', '')
        form_data.design_unit = data.get('designUnit', '')
        form_data.standard_selection = data.get('standardSelection', 'municipal')
        
        # 将form_data对象转换为JSON字符串存储
        form_data.form_data = json.dumps(data.get('formData', {}), ensure_ascii=False)
        
        # 保存到数据库
        db.session.add(form_data)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '数据保存成功'})
    except Exception as e:
        db.session.rollback()
        print(f"保存表单数据时出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_form', methods=['GET'])
def load_form():
    try:
        import json
        
        # 获取最新的表单数据
        form_data = FormData.query.order_by(FormData.updated_at.desc()).first()
        
        if not form_data:
            return jsonify({'error': '没有找到保存的数据'}), 404
            
        result = {
            'projectName': form_data.project_name,
            'buildingNo': form_data.building_no,
            'projectLocation': form_data.project_location,
            'designNo': form_data.design_no,
            'constructionUnit': form_data.construction_unit,
            'designUnit': form_data.design_unit,
            'standardSelection': form_data.standard_selection,
            'formData': json.loads(form_data.form_data) if form_data.form_data else {}
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"加载表单数据时出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/project_info', methods=['GET'])
def get_project_info():
    try:
        # 获取项目信息
        project = Project.query.first()
        
        # 获取最新的表单数据
        form_data = FormData.query.order_by(FormData.updated_at.desc()).first()
        
        result = {
            'projectName': project.name if project else '',
            'projectCode': project.code if project else '',
            'constructionUnit': project.construction_unit if project else '',
            'designUnit': project.design_unit if project else '',
            'projectLocation': project.location if project else '',
            'buildingArea': project.building_area if project else '',
            'buildingType': project.building_type if project else '',  # 添加建筑类型
            'buildingNo': form_data.building_no if form_data else '',
            'designNo': form_data.design_no if form_data else '',
            'standardSelection': form_data.standard_selection if form_data else 'municipal'
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"获取项目信息时出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_template', methods=['GET'])
def get_template():
    try:
        template_path = os.path.join(app.static_folder, '绿色建材应用比例计算书.docx')
        if not os.path.exists(template_path):
            return jsonify({'error': '模板文件不存在'}), 404
            
        return send_file(template_path, as_attachment=True)
    except Exception as e:
        print(f"获取模板文件时出错: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

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
        
        # 验证必要字段
        if not level or not specialty:
            return jsonify({'error': '缺少必要字段: level, specialty'}), 400
        
        # 如果没有提供项目ID，尝试从第一个评分记录中获取项目名称
        project_name = None
        if not project_id and scores and len(scores) > 0:
            project_name = scores[0].get('project_name')
        
        # 记录请求信息
        app.logger.info(f"保存评分数据: 级别={level}, 专业={specialty}, 项目ID={project_id}, 项目名称={project_name}, 评价标准={standard}, 评分数量={len(scores)}")
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except Exception as db_error:
            app.logger.error(f"数据库连接失败: {str(db_error)}")
            return jsonify({'error': f'数据库连接失败: {str(db_error)}'}), 500
        
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
        
        # 开始事务
        conn.autocommit = False
        
        try:
            # 如果提供了项目ID，先删除该项目该专业该级别的所有评分记录
            if project_id:
                delete_query = """
                DELETE FROM [得分表]
                WHERE [项目ID] = ? AND [专业] = ? AND [评价等级] = ?
                """
                cursor.execute(delete_query, (project_id, specialty, level))
                app.logger.info(f"删除项目 {project_id} 的 {specialty} 专业 {level} 级别的评分记录: {cursor.rowcount} 条")
            
            # 如果提供了项目名称但没有项目ID，先删除该项目名称该专业该级别的所有评分记录
            elif project_name:
                delete_query = """
                DELETE FROM [得分表]
                WHERE [项目名称] = ? AND [专业] = ? AND [评价等级] = ?
                """
                cursor.execute(delete_query, (project_name, specialty, level))
                app.logger.info(f"删除项目 '{project_name}' 的 {specialty} 专业 {level} 级别的评分记录: {cursor.rowcount} 条")
            
            # 插入新的评分记录
            insert_count = 0
            for score_data in scores:
                # 获取评分数据
                clause_number = score_data.get('clause_number')
                category = score_data.get('category')
                is_achieved = score_data.get('is_achieved')
                score = score_data.get('score', '0')
                technical_measures = score_data.get('technical_measures', '')
                
                # 如果没有条文号，跳过
                if not clause_number:
                    continue
                
                # 插入评分记录
                insert_query = """
                INSERT INTO [得分表] (
                    [项目ID], [项目名称], [专业], [评价等级], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(
                    insert_query,
                    (
                        project_id, project_name, specialty, level,
                        clause_number, category, is_achieved, score,
                        technical_measures, standard
                    )
                )
                insert_count += 1
            
            # 提交事务
            conn.commit()
            app.logger.info(f"成功插入 {insert_count} 条评分记录")
            
            # 关闭数据库连接
            conn.close()
            
            # 清除缓存
            cache_key = get_scores_cache_key(level, specialty, project_id, standard)
            if cache.has(cache_key):
                cache.delete(cache_key)
                app.logger.info(f"清除缓存: {cache_key}")
            
            return jsonify({
                'success': True,
                'message': f'成功保存 {insert_count} 条评分记录'
            }), 200
        
        except Exception as e:
            # 回滚事务
            conn.rollback()
            app.logger.error(f"保存评分数据失败: {str(e)}")
            traceback.print_exc()
            
            # 关闭数据库连接
            conn.close()
            
            return jsonify({'error': f'保存评分数据失败: {str(e)}'}), 500
    
    except Exception as e:
        app.logger.error(f"处理保存评分请求失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500

@app.route('/api/load_scores', methods=['GET'])
def load_scores():
    """加载评分数据的API端点"""
    try:
        # 获取请求参数
        level = request.args.get('level')
        specialty = request.args.get('specialty')
        project_id = request.args.get('project_id')
        standard = request.args.get('standard', '成都市标')  # 获取评价标准，默认为成都市标
        
        # 验证必要参数
        if not level or not specialty:
            return jsonify({'error': '缺少必要参数: level, specialty'}), 400
        
        # 记录请求信息
        app.logger.info(f"加载评分数据: 级别={level}, 专业={specialty}, 项目ID={project_id}, 评价标准={standard}")
        
        # 如果提供了项目ID，获取项目信息
        project_name = None
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
        
        # 构建缓存键
        cache_key = get_scores_cache_key(level, specialty, project_id, standard)
        
        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            app.logger.info(f"从缓存获取评分数据: {cache_key}")
            return jsonify(cached_data)
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except Exception as db_error:
            app.logger.error(f"数据库连接失败: {str(db_error)}")
            return jsonify({'error': f'数据库连接失败: {str(db_error)}'}), 500
        
        # 构建查询条件
        query_conditions = ["[评价等级] = ?", "[专业] = ?"]
        query_params = [level, specialty]
        
        # 如果指定了项目ID，添加到查询条件
        if project_id:
            query_conditions.append("[项目ID] = ?")
            query_params.append(project_id)
            
            # 如果项目有评价标准，添加到查询条件
            if standard:
                query_conditions.append("[评价标准] = ?")
                query_params.append(standard)
        # 如果指定了项目名称，添加到查询条件
        elif project_name:
            query_conditions.append("[项目名称] = ?")
            query_params.append(project_name)
            
            # 如果项目有评价标准，添加到查询条件
            if standard:
                query_conditions.append("[评价标准] = ?")
                query_params.append(standard)
        # 如果没有指定项目ID和项目名称，但指定了评价标准，添加到查询条件
        elif standard:
            query_conditions.append("[评价标准] = ?")
            query_params.append(standard)
        
        # 构建查询语句
        query = f"""
        SELECT [条文号], [分类], [是否达标], [得分], [技术措施]
        FROM [得分表]
        WHERE {' AND '.join(query_conditions)}
        ORDER BY [条文号]
        """
        
        # 打印查询语句和参数，用于调试
        app.logger.info(f"执行查询1 (所有条件): {query}")
        app.logger.info(f"查询参数: {query_params}")
        
        # 执行查询
        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        
        # 打印查询结果的行数，用于调试
        app.logger.info(f"查询结果1: {len(rows)} 行")
        
        # 如果没有结果，尝试只按项目ID查询
        if len(rows) == 0 and project_id:
            query_conditions = ["[项目ID] = ?"]
            query_params = [project_id]
            
            query = f"""
            SELECT [条文号], [分类], [是否达标], [得分], [技术措施]
            FROM [得分表]
            WHERE {' AND '.join(query_conditions)}
            ORDER BY [条文号]
            """
            
            app.logger.info(f"执行查询2 (只按项目ID): {query}")
            app.logger.info(f"查询参数: {query_params}")
            
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            app.logger.info(f"查询结果2: {len(rows)} 行")
        
        # 如果仍然没有结果，尝试不加任何条件查询
        if len(rows) == 0:
            query = """
            SELECT TOP 10 [条文号], [分类], [是否达标], [得分], [技术措施]
            FROM [得分表]
            """
            
            app.logger.info(f"执行查询3 (不加条件): {query}")
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            app.logger.info(f"查询结果3: {len(rows)} 行")
        
        # 处理查询结果
        scores = []
        for row in rows:
            scores.append({
                'clause_number': row[0],
                'category': row[1],
                'is_achieved': row[2],
                'score': row[3],
                'technical_measures': row[4]
            })
        
        # 关闭数据库连接
        conn.close()
        
        # 构建响应数据
        response_data = {
            'success': True,
            'scores': scores,
            'count': len(scores),
            'level': level,
            'specialty': specialty,
            'project_id': project_id,
            'standard': standard
        }
        
        # 缓存响应数据
        cache.set(cache_key, response_data)
        app.logger.info(f"缓存评分数据: {cache_key}, 记录数: {len(scores)}")
        
        return jsonify(response_data)
    
    except Exception as e:
        app.logger.error(f"加载评分数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'加载评分数据失败: {str(e)}'}), 500

@app.route('/api/project_scores', methods=['GET'])
def get_project_scores():
    try:
        project_id = request.args.get('project_id')
        by_category = request.args.get('by_category', 'false').lower() == 'true'
        
        # 如果提供了项目ID，转换为整数
        if project_id:
            project_id = int(project_id)
        
        # 计算各专业得分
        specialty_scores = calculate_specialty_scores(project_id, by_category)
        
        # 计算总得分
        if by_category:
            total_score = sum(specialty_scores.values())
            
            # 计算各分类的总分
            categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
            category_totals = {category: 0 for category in categories}
            
            for specialty, scores in specialty_scores.items():
                for category in categories:
                    category_totals[category] += scores
            
            # 确保所有分类得分都四舍五入到两位小数
            for category in categories:
                category_totals[category] = round(category_totals[category], 2)
        else:
            total_score = sum(specialty_scores.values())
            category_totals = None
        
        return jsonify({
            'success': True,
            'specialty_scores': specialty_scores,
            'total_score': round(total_score, 2),
            'category_totals': category_totals
        }), 200
    
    except Exception as e:
        app.logger.error(f"获取专业得分失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'获取专业得分失败: {str(e)}'}), 500

@app.route('/api/get_score_summary', methods=['GET'])
def api_get_score_summary():
    """获取评分汇总数据的API端点"""
    try:
        # 获取项目ID参数
        project_id = request.args.get('project_id')
        
        # 获取force_refresh参数
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # 如果没有提供项目ID，返回错误
        if not project_id:
            return jsonify({'error': '缺少项目ID参数'}), 400
        
        # 转换项目ID为整数
        project_id = int(project_id)
        
        # 获取项目信息，确定评价标准
        project = get_project(project_id)
        project_standard = project.standard if project and project.standard else '成都市标'
        
        # 记录请求信息
        app.logger.info(f"获取评分汇总数据: 项目ID={project_id}, 评价标准={project_standard}, 强制刷新={force_refresh}")
        
        # 清除相关缓存
        # 清除专业得分缓存
        for specialty in ['建筑', '结构', '给排水', '电气', '暖通', '景观']:
            cache_key = get_scores_cache_key('提高级', specialty, project_id, project_standard)
            if cache.has(cache_key):
                cache.delete(cache_key)
                app.logger.info(f"清除缓存: {cache_key}")
        
        # 获取评分汇总数据
        score_summary = get_score_summary(project_id, force_refresh=True)
        
        # 添加项目评价标准信息到返回结果
        score_summary['project_standard'] = project_standard
        
        # 返回评分汇总数据
        return jsonify(score_summary)
    
    except Exception as e:
        app.logger.error(f"获取评分汇总数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'获取评分汇总数据失败: {str(e)}'}), 500

# 移除缓存装饰器，确保每次都从数据库获取最新数据
def get_min_scores():
    """
    获取各专业的最低得分要求，直接返回硬编码的值
    
    返回值:
        包含各专业最低得分要求的字典
    """
    # 直接返回硬编码的最低得分要求
    return {
        '建筑专业': 16,
        '结构专业': 8,
        '给排水专业': 8,
        '电气专业': 8,
        '暖通专业': 8,
        '景观专业': 8
    }

# 在应用启动时检查并添加缺失的列
def check_and_add_missing_columns():
    """检查并添加缺失的列到projects表中"""
    try:
        # 获取数据库连接
        conn = db.engine.connect()
        
        # 获取当前表结构
        result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects'"))
        existing_columns = [row[0] for row in result]
        
        # 定义需要添加的列及其类型
        columns_to_add = {
            'climate_zone': 'NVARCHAR(10)',
            'star_rating_target': 'NVARCHAR(10)',
            'total_land_area': 'FLOAT',
            'total_building_area': 'FLOAT',
            'above_ground_area': 'FLOAT',
            'underground_area': 'FLOAT',
            'underground_floor_area': 'FLOAT',
            'ground_parking_spaces': 'INT',
            'plot_ratio': 'FLOAT',
            'building_base_area': 'FLOAT',
            'building_density': 'FLOAT',
            'green_area': 'FLOAT',
            'green_ratio': 'FLOAT',
            'residential_units': 'INT',
            'building_floors': 'NVARCHAR(20)',
            'building_height': 'FLOAT',
            'air_conditioning_type': 'NVARCHAR(50)',
            'average_floors': 'NVARCHAR(50)',
            'has_garbage_room': 'NVARCHAR(10)',
            'has_elevator': 'NVARCHAR(10)',
            'has_underground_garage': 'NVARCHAR(10)',
            'construction_type': 'NVARCHAR(50)',
            'has_water_landscape': 'NVARCHAR(10)',
            'is_fully_decorated': 'NVARCHAR(10)',
            'public_building_type': 'NVARCHAR(50)',
            'public_green_space': 'NVARCHAR(10)',
        }
        
        # 检查并添加缺失的列
        for column_name, column_type in columns_to_add.items():
            if column_name.lower() not in [col.lower() for col in existing_columns]:
                print(f"添加列: {column_name} ({column_type})")
                conn.execute(text(f"ALTER TABLE projects ADD {column_name} {column_type}"))
        
        # 使用事务提交更改
        db.session.commit()
        print("数据库表结构更新完成")
        
    except Exception as e:
        print(f"更新数据库表结构时出错: {str(e)}")
        print(traceback.format_exc())
    finally:
        if 'conn' in locals():
            conn.close()

# 在应用启动时检查并添加缺失的列
with app.app_context():
    try:
        check_and_add_missing_columns()
    except Exception as e:
        print(f"初始化数据库结构时出错: {str(e)}")
        print(traceback.format_exc())

# 初始化数据库
def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表已创建")

# 获取数据库连接
def get_db_connection():
    """获取数据库连接"""
    retry_count = 0
    max_retries = 3
    retry_delay = 2  # 秒
    
    while retry_count < max_retries:
        try:
            # 获取数据库连接字符串
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"尝试连接数据库 (尝试 {retry_count + 1}/{max_retries})...")
            
            # 解析连接字符串
            if 'sqlite' in db_uri:
                # SQLite连接
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                print(f"SQLite数据库连接成功: {db_path}")
                return conn
            elif 'mssql' in db_uri:
                # SQL Server连接
                # 从连接字符串中提取参数
                conn_parts = db_uri.replace('mssql+pyodbc://', '').split('?')[0].split('@')
                user_pass = conn_parts[0].split(':')
                server_db = conn_parts[1].split('/')
                
                username = user_pass[0]
                password = user_pass[1]
                server = server_db[0]
                database = server_db[1]
                
                # 构建连接字符串
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
                
                # 创建连接
                conn = pyodbc.connect(conn_str)
                print(f"SQL Server数据库连接成功: 服务器={server}, 数据库={database}, 用户={username}")
                return conn
            else:
                # 其他数据库类型
                raise ValueError(f"不支持的数据库类型: {db_uri}")
        except Exception as e:
            retry_count += 1
            print(f"获取数据库连接失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            traceback.print_exc()
            
            if retry_count < max_retries:
                print(f"将在 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                print("已达到最大重试次数，放弃连接")
                raise

# 获取评分汇总数据的函数
def get_score_summary(project_id, force_refresh=False):
    """获取评分汇总数据的函数"""
    try:
        # 获取项目信息，确定评价标准
        project = get_project(project_id)
        project_standard = project.standard if project and project.standard else '成都市标'
        
        app.logger.info(f"获取评分汇总数据: 项目ID={project_id}, 评价标准={project_standard}, 强制刷新={force_refresh}")
        
        # 构建缓存键
        cache_key = f"score_summary_{project_id}_{project_standard}"
        
        # 如果强制刷新或缓存中没有数据，则重新计算
        if force_refresh or not cache.get(cache_key):
            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 获取得分表中的记录数
            try:
                cursor.execute("SELECT COUNT(*) FROM [得分表]")
                count = cursor.fetchone()[0]
                app.logger.info(f"得分表中共有 {count} 条记录")
                
                # 获取得分表中项目ID为当前项目的记录数
                cursor.execute("SELECT COUNT(*) FROM [得分表] WHERE [项目ID] = ?", [project_id])
                project_count = cursor.fetchone()[0]
                app.logger.info(f"得分表中项目ID={project_id}的记录有 {project_count} 条")
                
                # 如果项目没有记录，则返回硬编码的测试数据
                if project_count == 0:
                    app.logger.warning(f"项目ID={project_id}在得分表中没有记录，返回测试数据")
                    conn.close()
                    return get_test_score_data()
                
                # 获取所有专业的得分数据
                specialties = ['建筑专业', '结构专业', '给排水专业', '电气专业', '暖通专业', '景观专业']
                
                # 专业名称映射，用于处理数据库中的专业名称与预定义专业名称的不完全匹配
                specialty_mapping = {
                    '建筑': '建筑专业',
                    '结构': '结构专业',
                    '给排水': '给排水专业',
                    '电气': '电气专业',
                    '暖通': '暖通专业',
                    '景观': '景观专业',
                    '建筑专业': '建筑专业',
                    '结构专业': '结构专业',
                    '给排水专业': '给排水专业',
                    '电气专业': '电气专业',
                    '暖通空调专业': '暖通专业',
                    '暖通专业': '暖通专业',
                    '景观专业': '景观专业'
                }
                
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
                
                # 使用更直接的SQL查询获取数据
                # 不使用参数化查询，直接构建SQL语句
                sql_query = f"""
                SELECT [专业], [分类], [是否达标], [得分]
                FROM [得分表]
                WHERE [项目ID] = {project_id}
                """
                
                app.logger.info(f"执行SQL查询: {sql_query}")
                
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                
                app.logger.info(f"查询结果: {len(rows)} 行")
                
                # 如果没有结果，尝试不带条件查询
                if len(rows) == 0:
                    sql_query = """
                    SELECT TOP 100 [专业], [分类], [是否达标], [得分], [项目ID]
                    FROM [得分表]
                    """
                    
                    app.logger.info(f"执行无条件SQL查询: {sql_query}")
                    
                    cursor.execute(sql_query)
                    rows = cursor.fetchall()
                    
                    app.logger.info(f"无条件查询结果: {len(rows)} 行")
                    app.logger.info(f"查询到的项目ID: {[row[4] for row in rows]}")
                
                # 处理查询结果
                for row in rows:
                    specialty = row[0]
                    category = row[1]
                    is_achieved = row[2]
                    score = row[3]
                    
                    app.logger.info(f"处理记录: 专业={specialty}, 分类={category}, 是否达标={is_achieved}, 得分={score}")
                    
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
                        except (ValueError, TypeError) as e:
                            app.logger.error(f"得分转换失败: {score}, 错误: {str(e)}")
                    
                    app.logger.info(f"映射后: 专业={mapped_specialty}, 是否达标={is_achieved_flag}, 得分={score_value}")
                    
                    # 如果达标且得分大于0，累加得分
                    if is_achieved_flag and score_value > 0:
                        specialty_scores[mapped_specialty] += score_value
                        
                        # 按分类累加得分
                        if category in specialty_scores_by_category[mapped_specialty]:
                            specialty_scores_by_category[mapped_specialty][category] += score_value
                            app.logger.info(f"累加得分: 专业={mapped_specialty}, 分类={category}, 得分={score_value}, 累计={specialty_scores_by_category[mapped_specialty][category]}")
                
                # 计算各专业的总分
                for specialty in specialties:
                    category_scores = specialty_scores_by_category[specialty]
                    category_scores['总分'] = sum(score for category, score in category_scores.items() if category != '总分')
                    app.logger.info(f"专业总分: {specialty}={category_scores['总分']}")
                
                # 关闭数据库连接
                conn.close()
                
                # 构建汇总数据
                summary_data = {
                    'specialty_scores': specialty_scores,
                    'specialty_scores_by_category': specialty_scores_by_category,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 缓存结果
                cache.set(cache_key, summary_data)
                
                return summary_data
            except Exception as e:
                app.logger.error(f"查询得分表失败: {str(e)}")
                app.logger.error(traceback.format_exc())
                conn.close()
                return get_test_score_data()
        else:
            # 从缓存中获取数据
            app.logger.info(f"从缓存中获取评分汇总数据: {cache_key}")
            return cache.get(cache_key)
    
    except Exception as e:
        app.logger.error(f"获取评分汇总数据失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return get_test_score_data()

# 获取测试评分数据
def get_test_score_data():
    """返回测试用的评分数据"""
    specialty_scores = {
        '建筑专业': 25.5,
        '结构专业': 18.2,
        '给排水专业': 15.8,
        '电气专业': 20.3,
        '暖通专业': 22.7,
        '景观专业': 16.9
    }
    
    specialty_scores_by_category = {
        '建筑专业': {
            '安全耐久': 5.5,
            '健康舒适': 6.0,
            '生活便利': 4.0,
            '资源节约': 5.0,
            '环境宜居': 3.0,
            '提高与创新': 2.0,
            '总分': 25.5
        },
        '结构专业': {
            '安全耐久': 8.2,
            '健康舒适': 3.0,
            '生活便利': 2.0,
            '资源节约': 3.0,
            '环境宜居': 1.0,
            '提高与创新': 1.0,
            '总分': 18.2
        },
        '给排水专业': {
            '安全耐久': 2.8,
            '健康舒适': 4.0,
            '生活便利': 3.0,
            '资源节约': 4.0,
            '环境宜居': 1.0,
            '提高与创新': 1.0,
            '总分': 15.8
        },
        '电气专业': {
            '安全耐久': 3.3,
            '健康舒适': 5.0,
            '生活便利': 4.0,
            '资源节约': 5.0,
            '环境宜居': 2.0,
            '提高与创新': 1.0,
            '总分': 20.3
        },
        '暖通专业': {
            '安全耐久': 2.7,
            '健康舒适': 7.0,
            '生活便利': 3.0,
            '资源节约': 6.0,
            '环境宜居': 3.0,
            '提高与创新': 1.0,
            '总分': 22.7
        },
        '景观专业': {
            '安全耐久': 1.9,
            '健康舒适': 3.0,
            '生活便利': 2.0,
            '资源节约': 4.0,
            '环境宜居': 5.0,
            '提高与创新': 1.0,
            '总分': 16.9
        }
    }
    
    return {
        'specialty_scores': specialty_scores,
        'specialty_scores_by_category': specialty_scores_by_category,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_test_data': True
    }

@app.route('/update_score', methods=['POST'])
def update_score():
    """
    接收并处理更新项目得分的请求
    """
    try:
        # 获取JSON数据
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '未接收到数据'}), 400
        
        # 提取必要的字段
        project_id = data.get('project_id')
        standard = data.get('standard')
        clause_number = data.get('clause_number')
        score = data.get('score')
        page = data.get('page')
        level = data.get('level')
        
        # 验证必要字段
        if not all([project_id, standard, clause_number, score is not None]):
            return jsonify({'success': False, 'message': '缺少必要的字段'}), 400
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查项目是否存在
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        
        if not project:
            conn.close()
            return jsonify({'success': False, 'message': '项目不存在'}), 404
        
        # 检查得分记录是否已存在
        cursor.execute(
            "SELECT id FROM project_scores WHERE project_id = ? AND standard = ? AND clause_number = ?",
            (project_id, standard, clause_number)
        )
        existing_score = cursor.fetchone()
        
        if existing_score:
            # 更新现有记录
            cursor.execute(
                """
                UPDATE project_scores 
                SET score = ?, page = ?, level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND standard = ? AND clause_number = ?
                """,
                (score, page, level, project_id, standard, clause_number)
            )
            app.logger.info(f"更新项目 {project_id} 的得分记录，条文号: {clause_number}, 分值: {score}")
        else:
            # 创建新记录
            cursor.execute(
                """
                INSERT INTO project_scores (project_id, standard, clause_number, score, page, level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (project_id, standard, clause_number, score, page, level)
            )
            app.logger.info(f"创建项目 {project_id} 的新得分记录，条文号: {clause_number}, 分值: {score}")
        
        # 提交事务并关闭连接
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '得分更新成功'})
        
    except Exception as e:
        app.logger.error(f"更新得分时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

# 添加新的路由用于直接更新得分
@app.route('/api/update_score_direct', methods=['POST'])
def update_score_direct():
    """
    直接更新数据库中的得分
    
    请求参数:
    {
        "project_id": 1,                 // 项目ID
        "clause_number": "3.1.2.14",     // 条文号
        "score": 12,                     // 得分值
        "standard": "成都市标",           // 评价标准
        "specialty": "建筑专业",          // 专业，可选
        "level": "提高级",               // 评价等级，可选
        "category": "资源节约",           // 分类，可选
        "is_achieved": "true"            // 是否达标，可选
    }
    
    响应:
    {
        "success": true,                 // 是否成功
        "message": "更新成功",            // 消息
        "data": {                        // 更新后的数据
            "project_id": 1,
            "clause_number": "3.1.2.14",
            "score": 12,
            "standard": "成都市标"
        }
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
        score = data.get('score')
        standard = data.get('standard', '成都市标')
        
        # 可选参数
        specialty = data.get('specialty', '建筑专业')
        level = data.get('level', '提高级')
        category = data.get('category', '资源节约')
        is_achieved = data.get('is_achieved', 'true')
        technical_measures = data.get('technical_measures', '')
        
        # 记录请求信息
        app.logger.info(f"接收到更新请求: 项目ID={project_id}, 条文号={clause_number}, 得分={score}, 标准={standard}")
        
        # 验证必要参数
        if not all([project_id, clause_number, score is not None]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数: project_id, clause_number, score'
            }), 400
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            app.logger.info("数据库连接成功")
        except Exception as e:
            app.logger.error(f"数据库连接失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'数据库连接失败: {str(e)}'
            }), 500
        
        try:
            # 开始事务
            conn.autocommit = False
            
            # 先检查记录是否存在
            check_query = """
            SELECT COUNT(*) FROM [得分表]
            WHERE [项目ID] = ? AND [条文号] = ? AND [评价标准] = ?
            """
            cursor.execute(check_query, (project_id, clause_number, standard))
            count = cursor.fetchone()[0]
            
            if count > 0:
                # 更新现有记录，只修改得分字段
                update_query = """
                UPDATE [得分表]
                SET [得分] = ?
                WHERE [项目ID] = ? AND [条文号] = ? AND [评价标准] = ?
                """
                cursor.execute(
                    update_query,
                    (score, project_id, clause_number, standard)
                )
                app.logger.info(f"更新记录: 影响行数={cursor.rowcount}")
            else:
                # 插入新记录
                insert_query = """
                INSERT INTO [得分表] (
                    [项目ID], [项目名称], [专业], [评价等级], [条文号], 
                    [分类], [是否达标], [得分], [技术措施], [评价标准]
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(
                    insert_query,
                    (project_id, f'项目{project_id}', specialty, level, clause_number,
                     category, is_achieved, score, technical_measures, standard)
                )
                app.logger.info(f"插入记录: 影响行数={cursor.rowcount}")
            
            # 提交事务
            conn.commit()
            app.logger.info("事务提交成功")
            
            # 验证更新是否成功
            verify_query = """
            SELECT [得分] FROM [得分表]
            WHERE [项目ID] = ? AND [条文号] = ? AND [评价标准] = ?
            """
            cursor.execute(verify_query, (project_id, clause_number, standard))
            result = cursor.fetchone()
            
            if result:
                actual_score = result[0]
                app.logger.info(f"验证成功: 条文 {clause_number} 的得分为 {actual_score}")
                
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
            else:
                app.logger.error(f"验证失败: 未找到条文 {clause_number} 的记录")
                return jsonify({
                    'success': False,
                    'message': f'验证失败: 未找到条文 {clause_number} 的记录'
                }), 500
        
        except Exception as e:
            # 回滚事务
            conn.rollback()
            app.logger.error(f"数据库操作失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'数据库操作失败: {str(e)}'
            }), 500
        
        finally:
            # 关闭数据库连接
            cursor.close()
            conn.close()
            app.logger.info("数据库连接已关闭")
    
    except Exception as e:
        app.logger.error(f"处理请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

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
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            app.logger.info("数据库连接成功")
        except Exception as e:
            app.logger.error(f"数据库连接失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'数据库连接失败: {str(e)}'
            }), 500
        
        try:
            # 查询记录
            query = """
            SELECT [条文号], [分类], [专业], [是否达标], [得分]
            FROM [得分表]
            WHERE [项目ID] = ? AND [条文号] = ? AND [评价标准] = ?
            """
            cursor.execute(query, (project_id, clause_number, standard))
            result = cursor.fetchone()
            
            # 关闭数据库连接
            cursor.close()
            conn.close()
            
            if result:
                # 返回成功响应
                return jsonify({
                    'success': True,
                    'message': '查询成功',
                    'clause_number': result[0],
                    'category': result[1],
                    'specialty': result[2],
                    'is_achieved': result[3],
                    'score': result[4]
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'未找到条文 {clause_number} 的记录'
                }), 404
        
        except Exception as e:
            app.logger.error(f"数据库查询失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            
            # 关闭数据库连接
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
                
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

# 添加新的路由用于执行SQL语句
@app.route('/api/execute_sql', methods=['POST'])
def execute_sql():
    """
    执行SQL语句
    
    请求参数:
    {
        "sql": "SQL语句",
        "params": [参数1, 参数2, ...] (可选)
    }
    
    响应:
    {
        "success": true,
        "message": "执行成功",
        "results": [
            {
                "column1": "value1",
                "column2": "value2"
            }
        ]
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
        
        # 获取SQL语句和参数
        sql = data.get('sql')
        params = data.get('params', [])
        
        if not sql:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: sql'
            }), 400
        
        # 记录请求信息
        app.logger.info(f"接收到SQL执行请求: {sql}, 参数: {params}")
        
        # 安全检查：禁止执行危险操作
        sql_lower = sql.lower().strip()
        
        # 禁止执行的操作列表
        forbidden_operations = [
            'drop table', 'drop database', 'truncate table', 
            'alter table', 'create table', 'create database',
            'exec ', 'execute ', 'sp_', 'xp_'
        ]
        
        # 检查是否包含禁止的操作
        for op in forbidden_operations:
            if op in sql_lower:
                app.logger.warning(f"尝试执行危险SQL操作: {sql}")
                return jsonify({
                    'success': False,
                    'message': f'禁止执行危险操作: {op}'
                }), 403
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            app.logger.info("数据库连接成功")
        except Exception as e:
            app.logger.error(f"数据库连接失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'数据库连接失败: {str(e)}'
            }), 500
        
        try:
            # 开始事务
            conn.autocommit = False
            
            # 执行SQL语句
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # 如果是SELECT语句，获取结果
            results = []
            if sql_lower.startswith('select'):
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
            
            # 提交事务
            conn.commit()
            app.logger.info("SQL执行成功，事务已提交")
            
            # 关闭数据库连接
            cursor.close()
            conn.close()
            
            # 返回成功响应
            return jsonify({
                'success': True,
                'message': '执行成功',
                'results': results
            })
        
        except Exception as e:
            # 回滚事务
            conn.rollback()
            app.logger.error(f"SQL执行失败: {str(e)}")
            app.logger.error(traceback.format_exc())
            
            # 关闭数据库连接
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': False,
                'message': f'SQL执行失败: {str(e)}'
            }), 500
    
    except Exception as e:
        app.logger.error(f"处理请求失败: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

@app.route('/api/project_scores', methods=['GET'])
def check_project_scores():
    """检查项目是否有得分数据的API端点"""
    try:
        # 获取请求参数
        project_id = request.args.get('project_id')
        standard = request.args.get('standard', '成都市标')
        
        if not project_id:
            return jsonify({'error': '缺少必要参数: project_id'}), 400
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询项目得分数据
        query = """
        SELECT COUNT(*) AS count
        FROM [得分表]
        WHERE [项目ID] = ?
        """
        
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()
        
        # 获取得分记录数
        score_count = result[0] if result else 0
        
        # 如果有得分记录，返回一些示例得分数据
        scores = []
        if score_count > 0:
            sample_query = """
            SELECT TOP 5 [条文号], [分类], [是否达标], [得分], [技术措施], [专业], [评价等级]
            FROM [得分表]
            WHERE [项目ID] = ?
            """
            cursor.execute(sample_query, (project_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                scores.append({
                    'clause_number': row[0],
                    'category': row[1],
                    'is_achieved': row[2],
                    'score': row[3],
                    'technical_measures': row[4],
                    'specialty': row[5],
                    'level': row[6]
                })
        
        # 关闭数据库连接
        conn.close()
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'standard': standard,
            'has_scores': score_count > 0,
            'score_count': score_count,
            'scores': scores
        })
        
    except Exception as e:
        app.logger.error(f"检查项目得分数据时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def save_score_for_new_project(data):
    """为新创建的项目保存初始评分数据"""
    try:
        # 获取评价等级和专业
        level = data.get('level')
        specialty = data.get('specialty')
        project_id = data.get('project_id')
        standard = data.get('standard', '成都市标')
        
        print(f"开始为项目 {project_id} 创建 {level}-{specialty} 的初始评分记录，标准: {standard}")
        
        # 获取项目信息
        project_name = None
        if project_id:
            try:
                project = get_project(project_id)
                if project:
                    project_name = project.name
                    print(f"获取到项目信息: ID={project_id}, 名称={project_name}")
                else:
                    print(f"未找到项目: ID={project_id}")
                    return False
            except Exception as e:
                print(f"获取项目信息失败: {str(e)}")
                traceback.print_exc()
                return False
        
        # 根据标准获取条文数据
        try:
            # 获取该标准下该专业该级别的所有条文
            standards_data = get_standards_by_name(standard)
            print(f"获取到 {len(standards_data)} 条 {standard} 标准数据")
            
            # 过滤出该专业该级别的条文
            filtered_standards = []
            for std in standards_data:
                # 检查专业是否匹配
                if std.专业 == specialty:
                    # 检查级别是否匹配
                    if (level == '基本级' and std.属性 == '控制项') or \
                       (level == '提高级' and std.属性 == '评分项'):
                        filtered_standards.append(std)
            
            print(f"找到 {len(filtered_standards)} 条 {standard} 的 {specialty} 专业 {level} 级别条文")
            
            # 如果没有找到条文，返回失败
            if not filtered_standards:
                print(f"未找到 {standard} 的 {specialty} 专业 {level} 级别条文")
                return False
            
            # 生成默认评分数据
            scores = []
            for std in filtered_standards:
                # 基本级默认达标，提高级默认不达标
                is_achieved = '是' if level == '基本级' else '否'
                
                # 创建评分数据
                score_data = {
                    'clause_number': std.条文号,
                    'category': std.分类,
                    'is_achieved': is_achieved,
                    'score': '0',  # 默认得分为0
                    'technical_measures': '',  # 默认技术措施为空
                    'project_name': project_name
                }
                
                scores.append(score_data)
            
            print(f"已生成 {len(scores)} 条默认评分数据")
        except Exception as e:
            print(f"生成默认评分数据失败: {str(e)}")
            traceback.print_exc()
            return False
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            print("数据库连接成功")
        except Exception as db_error:
            print(f"数据库连接失败: {str(db_error)}")
            traceback.print_exc()
            return False
        
        # 检查得分表是否存在
        try:
            cursor.execute("SELECT TOP 1 * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '得分表'")
            if not cursor.fetchone():
                print("得分表不存在，尝试创建")
                # 尝试创建得分表
                create_table_query = """
                CREATE TABLE [得分表] (
                    [ID] INT IDENTITY(1,1) PRIMARY KEY,
                    [项目ID] INT,
                    [项目名称] NVARCHAR(100),
                    [专业] NVARCHAR(50),
                    [评价等级] NVARCHAR(20),
                    [条文号] NVARCHAR(50),
                    [分类] NVARCHAR(50),
                    [是否达标] NVARCHAR(10),
                    [得分] NVARCHAR(10),
                    [技术措施] NVARCHAR(MAX),
                    [评价标准] NVARCHAR(50)
                )
                """
                cursor.execute(create_table_query)
                conn.commit()
                print("得分表创建成功")
        except Exception as e:
            print(f"检查或创建得分表失败: {str(e)}")
            traceback.print_exc()
            conn.close()
            return False
        
        # 开始事务
        try:
            # 如果提供了项目ID，先删除该项目该专业该级别的所有评分记录
            if project_id:
                delete_query = """
                DELETE FROM [得分表]
                WHERE [项目ID] = ? AND [专业] = ? AND [评价等级] = ?
                """
                cursor.execute(delete_query, (project_id, specialty, level))
                print(f"删除项目 {project_id} 的 {specialty} 专业 {level} 级别的评分记录: {cursor.rowcount} 条")
            
            # 插入评分数据
            insert_count = 0
            for score_data in scores:
                # 获取评分数据
                clause_number = score_data.get('clause_number')
                category = score_data.get('category')
                is_achieved = score_data.get('is_achieved')
                score = score_data.get('score', '0')
                technical_measures = score_data.get('technical_measures', '')
                
                # 插入评分记录
                insert_query = """
                INSERT INTO [得分表] (
                    [项目ID], [项目名称], [专业], [评价等级], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                try:
                    cursor.execute(
                        insert_query,
                        (
                            project_id, project_name, specialty, level,
                            clause_number, category, is_achieved, score,
                            technical_measures, standard
                        )
                    )
                    insert_count += 1
                except Exception as insert_error:
                    print(f"插入评分记录失败: {str(insert_error)}, 条文号: {clause_number}")
                    continue
            
            # 提交事务
            conn.commit()
            
            # 关闭数据库连接
            conn.close()
            
            # 同时也保存到缓存
            cache_key = get_scores_cache_key(level, specialty, project_id, standard)
            cache.set(cache_key, scores)
            
            print(f"已为项目 {project_id} 创建 {level}-{specialty} 的初始评分记录，共 {insert_count} 条")
            return True
        except Exception as e:
            # 回滚事务
            try:
                conn.rollback()
            except:
                pass
            
            try:
                conn.close()
            except:
                pass
            
            print(f"保存评分记录失败: {str(e)}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"保存初始评分记录失败: {str(e)}")
        traceback.print_exc()
        return False

@app.route('/api/star_case_scores', methods=['GET'])
def get_star_case_scores():
    """
    从"星级案例"表获取项目的得分数据
    
    请求参数:
    - target_project_id: 目标项目ID（可选，如果提供则直接导入数据到该项目）
    
    响应:
    {
        "success": true,             // 是否成功
        "message": "获取成功",        // 消息
        "data": {                    // 数据
            "standard": "评价标准",
            "star_rating_target": "星级目标",
            "scores": [...]          // 得分数据列表
        }
    }
    """
    try:
        # 获取目标项目ID（可选）
        target_project_id = request.args.get('target_project_id')
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'数据库连接失败: {str(e)}'
            }), 500
        
        try:
            # 如果提供了目标项目ID，获取项目信息和评价标准
            standard = '成都市标'  # 默认标准
            star_rating_target = '一星级'  # 默认星级目标
            
            if target_project_id:
                target_project = get_project(target_project_id)
                if not target_project:
                    return jsonify({
                        'success': False,
                        'message': f'目标项目(ID={target_project_id})不存在'
                    }), 404
                standard = target_project.standard
                star_rating_target = target_project.star_rating_target or '一星级'
                print(f"目标项目评价标准: {standard}, 星级目标: {star_rating_target}")
            
            # 从"星级案例"表获取数据，同时匹配评价标准和星级目标
            scores_query = """
            SELECT [专业], [评价等级], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准]
            FROM [星级案例]
            WHERE [评价标准] = ? AND [星级目标] = ?
            """
            cursor.execute(scores_query, (standard, star_rating_target))
            scores = cursor.fetchall()
            
            # 如果没有找到完全匹配的数据，则只匹配评价标准
            if not scores:
                print(f"未找到评价标准为\"{standard}\"且星级目标为\"{star_rating_target}\"的星级案例数据，尝试只匹配评价标准")
                scores_query = """
                SELECT [专业], [评价等级], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准]
                FROM [星级案例]
                WHERE [评价标准] = ?
                """
                cursor.execute(scores_query, (standard,))
                scores = cursor.fetchall()
                
                if not scores:
                    return jsonify({
                        'success': False,
                        'message': f'未找到评价标准为"{standard}"的星级案例数据'
                    }), 404
                
                print(f"获取到评价标准为\"{standard}\"的 {len(scores)} 条星级案例数据")
            else:
                print(f"获取到评价标准为\"{standard}\"且星级目标为\"{star_rating_target}\"的 {len(scores)} 条星级案例数据")
            
            # 如果提供了目标项目ID，则导入数据
            if target_project_id:
                # 开始事务
                conn.autocommit = False
                
                # 先删除目标项目的所有得分数据
                delete_query = """
                DELETE FROM [得分表]
                WHERE [项目ID] = ?
                """
                cursor.execute(delete_query, (target_project_id,))
                deleted_count = cursor.rowcount
                print(f"删除目标项目的 {deleted_count} 条得分数据")
                
                # 插入新的得分数据
                inserted_count = 0
                for score in scores:
                    specialty, level, clause_number, category, is_achieved, score_value, technical_measures, standard = score
                    
                    insert_query = """
                    INSERT INTO [得分表] (
                        [项目ID], [项目名称], [专业], [评价等级], [条文号], 
                        [分类], [是否达标], [得分], [技术措施], [评价标准]
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(
                        insert_query,
                        (target_project_id, target_project.name, specialty, level, clause_number,
                         category, is_achieved, score_value, technical_measures, standard)
                    )
                    inserted_count += 1
                    
                    # 每100条提交一次，避免事务过大
                    if inserted_count % 100 == 0:
                        conn.commit()
                        print(f"已提交 {inserted_count} 条记录")
                
                # 提交事务
                conn.commit()
                print(f"事务提交成功，共导入 {inserted_count} 条记录")
                
                # 清除目标项目的缓存
                cache_key = f"score_summary_{target_project_id}_{target_project.standard}"
                if cache.has(cache_key):
                    cache.delete(cache_key)
                    print(f"清除目标项目的评分汇总缓存: {cache_key}")
                
                return jsonify({
                    'success': True,
                    'message': f'成功导入 {inserted_count} 条得分数据到项目"{target_project.name}"',
                    'data': {
                        'standard': standard,
                        'star_rating_target': star_rating_target,
                        'imported_count': inserted_count
                    }
                })
            
            # 如果没有提供目标项目ID，则只返回数据
            scores_data = []
            for score in scores:
                specialty, level, clause_number, category, is_achieved, score_value, technical_measures, standard = score
                scores_data.append({
                    'specialty': specialty,
                    'level': level,
                    'clause_number': clause_number,
                    'category': category,
                    'is_achieved': is_achieved,
                    'score': score_value,
                    'technical_measures': technical_measures,
                    'standard': standard
                })
            
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'standard': standard,
                    'star_rating_target': star_rating_target,
                    'scores_count': len(scores),
                    'scores': scores_data[:10]  # 只返回前10条数据作为示例
                }
            })
        
        except Exception as e:
            # 回滚事务
            if target_project_id:
                conn.rollback()
            print(f"数据库操作失败: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'数据库操作失败: {str(e)}'
            }), 500
        
        finally:
            # 关闭数据库连接
            cursor.close()
            conn.close()
            print("数据库连接已关闭")
    
    except Exception as e:
        print(f"处理请求失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

def create_default_scores(project_id, project_name, standard_selection):
    """
    为项目创建默认评分记录
    
    参数:
    - project_id: 项目ID
    - project_name: 项目名称
    - standard_selection: 评价标准
    """
    try:
        # 连接数据库
        print("尝试连接数据库...")
        conn = get_db_connection()
        cursor = conn.cursor()
        print("数据库连接成功")
        
        # 检查得分表是否存在，如果不存在则创建
        try:
            print("检查得分表是否存在...")
            cursor.execute("SELECT TOP 1 * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '得分表'")
            table_exists = cursor.fetchone()
            if not table_exists:
                print("得分表不存在，创建新表")
                create_table_sql = """
                CREATE TABLE [得分表] (
                    [ID] INT IDENTITY(1,1) PRIMARY KEY,
                    [项目ID] INT,
                    [项目名称] NVARCHAR(100),
                    [专业] NVARCHAR(50),
                    [评价等级] NVARCHAR(20),
                    [条文号] NVARCHAR(50),
                    [分类] NVARCHAR(50),
                    [是否达标] NVARCHAR(10),
                    [得分] NVARCHAR(10),
                    [技术措施] NVARCHAR(MAX),
                    [评价标准] NVARCHAR(50)
                )
                """
                cursor.execute(create_table_sql)
                conn.commit()
                print("得分表创建成功")
            else:
                print("得分表已存在")
        except Exception as e:
            print(f"检查或创建得分表失败: {str(e)}")
            traceback.print_exc()
        
        # 获取标准数据
        print(f"获取标准数据: {standard_selection}")
        standards_data = get_standards_by_name(standard_selection)
        if standards_data:
            print(f"获取到 {len(standards_data)} 条 {standard_selection} 标准数据")
            # 打印前5条标准数据的示例
            if len(standards_data) > 0:
                print("标准数据示例:")
                for i, std in enumerate(standards_data[:5]):
                    try:
                        print(f"  {i+1}. 条文号: {std.条文号}, 专业: {std.专业}, 属性: {std.属性}, 分类: {std.分类}")
                    except Exception as attr_error:
                        print(f"  {i+1}. 无法显示标准数据: {str(attr_error)}")
        else:
            print(f"未获取到 {standard_selection} 标准数据")
            # 尝试获取默认标准数据
            print("尝试获取默认标准数据")
            standards_data = get_standards_by_name('成都市标')
            if standards_data:
                print(f"获取到 {len(standards_data)} 条默认标准数据")
                # 打印前5条标准数据的示例
                if len(standards_data) > 0:
                    print("默认标准数据示例:")
                    for i, std in enumerate(standards_data[:5]):
                        try:
                            print(f"  {i+1}. 条文号: {std.条文号}, 专业: {std.专业}, 属性: {std.属性}, 分类: {std.分类}")
                        except Exception as attr_error:
                            print(f"  {i+1}. 无法显示标准数据: {str(attr_error)}")
            else:
                print("未获取到任何标准数据")
                raise Exception("未获取到任何标准数据")
        
        # 定义要处理的专业和级别
        specialties = ['建筑专业', '结构专业', '给排水专业', '暖通专业', '电气专业']
        levels = ['基本级', '提高级']
        
        # 为每个专业和级别生成评分数据
        total_inserted = 0
        for specialty in specialties:
            for level in levels:
                # 过滤出该专业该级别的条文
                filtered_standards = []
                for std in standards_data:
                    try:
                        if std.专业 == specialty:
                            if (level == '基本级' and std.属性 == '控制项') or \
                               (level == '提高级' and std.属性 == '评分项'):
                                filtered_standards.append(std)
                    except Exception as attr_error:
                        print(f"处理标准数据时出错: {str(attr_error)}, 标准数据: {std}")
                        continue
                
                print(f"找到 {len(filtered_standards)} 条 {standard_selection} 的 {specialty} 专业 {level} 级别条文")
                
                # 如果找到了条文，则插入评分数据
                if filtered_standards:
                    # 先删除该项目该专业该级别的所有评分记录
                    try:
                        delete_sql = """
                        DELETE FROM [得分表]
                        WHERE [项目ID] = ? AND [专业] = ? AND [评价等级] = ?
                        """
                        cursor.execute(delete_sql, (project_id, specialty, level))
                        print(f"删除项目 {project_id} 的 {specialty} 专业 {level} 级别的评分记录: {cursor.rowcount} 条")
                    except Exception as delete_error:
                        print(f"删除评分记录失败: {str(delete_error)}")
                        traceback.print_exc()
                    
                    # 插入新的评分记录
                    insert_count = 0
                    insert_errors = 0
                    for std in filtered_standards:
                        # 基本级默认达标，提高级默认不达标
                        is_achieved = '是' if level == '基本级' else '否'
                        
                        # 插入评分记录
                        insert_sql = """
                        INSERT INTO [得分表] (
                            [项目ID], [项目名称], [专业], [评价等级], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准]
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        
                        try:
                            cursor.execute(
                                insert_sql,
                                (
                                    project_id, project_name, specialty, level,
                                    std.条文号, std.分类, is_achieved, '0',
                                    '', standard_selection
                                )
                            )
                            insert_count += 1
                            # 每插入10条记录提交一次事务，避免事务过大
                            if insert_count % 10 == 0:
                                conn.commit()
                                print(f"已提交 {insert_count} 条记录")
                        except Exception as insert_error:
                            insert_errors += 1
                            print(f"插入评分记录失败: {str(insert_error)}, 条文号: {std.条文号}")
                            if insert_errors <= 3:  # 只打印前3个错误的详细信息
                                traceback.print_exc()
                            continue
                    
                    print(f"为项目 {project_id} 的 {specialty} 专业 {level} 级别插入了 {insert_count} 条评分记录，失败 {insert_errors} 条")
                    total_inserted += insert_count
        
        # 提交事务并关闭连接
        try:
            conn.commit()
            print("最终提交事务成功")
        except Exception as commit_error:
            print(f"提交事务失败: {str(commit_error)}")
            traceback.print_exc()
        
        try:
            conn.close()
            print("数据库连接关闭成功")
        except Exception as close_error:
            print(f"关闭数据库连接失败: {str(close_error)}")
            traceback.print_exc()
        
        print(f"为项目 {project_id} 总共插入了 {total_inserted} 条评分记录")
        return True
    
    except Exception as e:
        print(f"生成项目评分数据失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 根据环境变量决定是否开启调试模式
    debug_mode = not is_production
    app.logger.info(f"应用启动: 调试模式={debug_mode}")
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 