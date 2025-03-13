from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
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
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
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
        
        # 打印接收到的表单数据
        print(f"接收到的表单数据: project_id={project_id}, project_name={form_data.get('project_name')}, standard_selection={form_data.get('standard_selection')}")
        
        # 如果有项目ID，获取现有项目；否则创建新项目
        if project_id:
            project = Project.query.get(project_id)
            if not project:
                print(f"未找到ID为{project_id}的项目，创建新项目")
                project = Project()
        else:
            print("未提供项目ID，创建新项目")
            project = Project()
        
        # 更新项目属性
        project.name = form_data.get('project_name', '')
        project.code = form_data.get('project_code', '')
        project.construction_unit = form_data.get('construction_unit', '')
        project.design_unit = form_data.get('design_unit', '')
        project.location = form_data.get('project_location', '')
        project.building_type = form_data.get('building_type', '')
        project.standard = form_data.get('standard_selection', '')  # 保存评价标准
        
        # 处理建筑面积
        building_area = form_data.get('building_area', '')
        if building_area:
            try:
                project.building_area = float(building_area)
            except ValueError as ve:
                print(f"建筑面积转换错误: {str(ve)}")
                pass
        
        # 打印调试信息
        print(f"保存项目信息: ID={project.id}, 名称={project.name}, 评价标准={project.standard}")
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        print(f"项目保存成功: ID={project.id}")
        return project
    except Exception as e:
        db.session.rollback()
        print(f"保存项目信息时出错: {str(e)}")
        print(traceback.format_exc())  # 打印详细的错误堆栈
        return None

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
        building_area = request.form.get('building_area')
        standard_selection = request.form.get('standard_selection')
        building_type = request.form.get('building_type')  # 获取建筑类型
        
        # 创建新项目
        project = Project(
            name=project_name,
            code=project_code,
            construction_unit=construction_unit,
            design_unit=design_unit,
            location=project_location,
            standard=standard_selection,
            building_type=building_type  # 设置建筑类型
        )
        
        # 处理建筑面积
        if building_area:
            try:
                project.building_area = float(building_area)
            except ValueError:
                pass
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        # 重定向到项目页面
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
            # 获取评分汇总数据
            score_summary = get_score_summary(project_id)
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
            project = save_project_info(request.form)
            if project:
                print(f"项目信息保存成功: ID={project.id}, 名称={project.name}, 标准={project.standard}")
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
    """生成得分表缓存的键"""
    key = f"scores_{level}_{specialty}"
    if project_id:
        key += f"_{project_id}"
    if standard:
        key += f"_{standard}"
    return key

@app.route('/api/save_score', methods=['POST'])
def save_score():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未接收到数据'}), 400
        
        level = data.get('level')
        specialty = data.get('specialty')
        scores = data.get('scores', [])
        standard = data.get('standard', '成都市标')  # 获取评价标准
        # 从请求中获取项目ID
        project_id_from_request = data.get('project_id')
        
        print(f"接收到保存评分请求: level={level}, specialty={specialty}, standard={standard}, project_id={project_id_from_request}, scores数量={len(scores)}")
        
        if not scores:
            return jsonify({'error': '评分数据为空'}), 400
        
        # 优先使用请求中的项目ID，如果没有再使用查询的项目ID
        if project_id_from_request and str(project_id_from_request).strip():
            project_id = int(project_id_from_request)
        else:
            # 获取当前项目ID
            project = Project.query.first()
            project_id = project.id if project else None
        
        print(f"使用项目ID: {project_id}")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 批量执行插入操作
        success_count = 0
        for score in scores:
            # 处理得分值
            is_achieved = score.get('is_achieved', '否')
            score_value = score.get('score', '0')
            clause_number = score.get('clause_number', '')
            category = score.get('category', '')
            technical_measures = score.get('technical_measures', '')
            project_name = score.get('project_name', '')
            
            # 打印每条记录的详细信息
            print(f"处理评分记录: 条文号={clause_number}, 是否达标={is_achieved}, 技术措施={technical_measures[:20]}...")
            
            # 如果是基本级，得分始终为0
            if level == '基本级':
                score_value = '0'
                print(f"基本级记录: 是否达标={is_achieved}, 技术措施长度={len(technical_measures)}")
                print(f"基本级完整数据: {score}")
            
            try:
                # 首先检查记录是否存在
                check_sql = """
                SELECT COUNT(*) FROM [得分表] 
                WHERE [项目ID] = ? AND [条文号] = ? AND [评价等级] = ? AND [专业] = ?
                """
                cursor.execute(check_sql, (project_id, clause_number, level, specialty))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # 更新现有记录
                    update_sql = """
                    UPDATE [得分表] SET 
                        [项目名称] = ?,
                        [分类] = ?,
                        [是否达标] = ?,
                        [得分] = ?,
                        [技术措施] = ?,
                        [评价标准] = ?
                    WHERE [项目ID] = ? AND [条文号] = ? AND [评价等级] = ? AND [专业] = ?
                    """
                    cursor.execute(
                        update_sql,
                        (
                            project_name,
                            category,
                            is_achieved,
                            score_value,
                            technical_measures,
                            standard,  # 添加评价标准
                            project_id,
                            clause_number,
                            level,
                            specialty
                        )
                    )
                    print(f"更新记录: 条文号={clause_number}, 是否达标={is_achieved}, 技术措施长度={len(technical_measures)}")
                else:
                    # 插入新记录
                    insert_sql = """
                    INSERT INTO [得分表] ([项目ID], [项目名称], [条文号], [分类], [是否达标], [得分], [技术措施], [评价等级], [专业], [评价标准])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(
                        insert_sql,
                        (
                            project_id,
                            project_name,
                            clause_number,
                            category,
                            is_achieved,
                            score_value,
                            technical_measures,
                            level,
                            specialty,
                            standard  # 添加评价标准
                        )
                    )
                    print(f"插入记录: 条文号={clause_number}, 是否达标={is_achieved}, 技术措施长度={len(technical_measures)}")
                
                success_count += 1
            except Exception as e:
                print(f"执行SQL时出错: {str(e)}")
                print(f"SQL参数: project_id={project_id}, clause_number={clause_number}, category={category}, standard={standard}")
                raise
        
        # 提交事务
        conn.commit()
        print(f"事务已提交，成功保存 {success_count} 条记录")
        
        if conn:
            conn.close()
            print("数据库连接已关闭")
        
        # 保存成功后，删除相关缓存
        cache_key = get_scores_cache_key(level, specialty, project_id, standard)
        cache.delete(cache_key)
        
        # 同时删除评分汇总相关的缓存
        summary_cache_key = f"score_summary_{project_id}"
        cache.delete(summary_cache_key)
        
        # 删除专业得分缓存
        specialty_scores_key = f"specialty_scores_{project_id}"
        cache.delete(specialty_scores_key)
        
        print(f"已清除缓存: {cache_key}, {summary_cache_key}, {specialty_scores_key}")
        
        return jsonify({'success': True, 'message': f'成功保存{success_count}条评分记录', 'project_id': project_id}), 200
    
    except Exception as e:
        # 回滚事务
        if conn:
            try:
                conn.rollback()
                print("事务已回滚")
                conn.close()
                print("数据库连接已关闭")
            except Exception as close_error:
                print(f"关闭数据库连接时出错: {str(close_error)}")
        
        # 记录错误信息到日志
        error_msg = f"保存评分失败: {str(e)}"
        stack_trace = traceback.format_exc()
        print(error_msg)
        print(stack_trace)
        app.logger.error(error_msg)
        app.logger.error(stack_trace)
        
        return jsonify({'error': error_msg, 'stack_trace': stack_trace}), 500

@app.route('/api/load_scores', methods=['GET'])
def load_scores():
    try:
        level = request.args.get('level')
        specialty = request.args.get('specialty')
        project_id = request.args.get('project_id')
        standard = request.args.get('standard')  # 获取评价标准参数
        
        if not level or not specialty:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 获取当前项目ID（如果未指定）
        if not project_id:
            project = Project.query.first()
            project_id = project.id if project else None
            
        # 如果未指定评价标准，获取项目的评价标准
        if not standard and project_id:
            project = Project.query.get(project_id)
            if project and project.standard:
                standard = project.standard
        
        # 生成缓存键
        cache_key = get_scores_cache_key(level, specialty, project_id, standard)
        
        # 尝试从缓存获取数据
        cached_scores = cache.get(cache_key)
        if cached_scores is not None:
            print(f"从缓存加载评分数据: {cache_key}, 找到 {len(cached_scores)} 条记录")
            return jsonify({'success': True, 'scores': cached_scores, 'from_cache': True}), 200
        
        # 缓存未命中，从数据库加载
        print(f"缓存未命中，从数据库加载评分数据: {cache_key}")
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询条件 - 使用SQL Server方括号语法
        query_conditions = ["[评价等级]=?", "[专业]=?"]
        query_params = [level, specialty]
        
        # 如果有项目ID，添加到查询条件
        if project_id:
            query_conditions.append("[项目ID]=?")
            query_params.append(project_id)
            
        # 如果有评价标准，添加到查询条件
        if standard:
            query_conditions.append("[评价标准]=?")
            query_params.append(standard)
        
        # 构建查询SQL
        query_sql = f"""SELECT [项目名称], [条文号], [分类], [是否达标], [得分], [技术措施], [评价标准] 
                        FROM [得分表] 
                        WHERE {' AND '.join(query_conditions)}"""
        
        print(f"加载评分数据: level={level}, specialty={specialty}, project_id={project_id}, standard={standard}")
        print(f"执行SQL: {query_sql}, 参数: {query_params}")
        
        # 执行查询
        cursor.execute(query_sql, query_params)
        
        scores = []
        for row in cursor.fetchall():
            scores.append({
                'project_name': row[0],
                'clause_number': row[1],
                'category': row[2],
                'is_achieved': row[3],
                'score': row[4],
                'technical_measures': row[5],
                'standard': row[6] if len(row) > 6 else standard or '成都市标'  # 添加评价标准
            })
        
        conn.close()
        
        # 将结果存入缓存
        cache.set(cache_key, scores)
        
        print(f"找到 {len(scores)} 条评分记录，已存入缓存: {cache_key}")
        return jsonify({'success': True, 'scores': scores, 'from_cache': False}), 200
    
    except Exception as e:
        app.logger.error(f"加载评分失败: {str(e)}")
        traceback.print_exc()  # 打印详细的错误堆栈
        return jsonify({'error': f'加载评分失败: {str(e)}'}), 500

@app.route('/api/project_scores', methods=['GET'])
def get_project_scores():
    try:
        project_id = request.args.get('project_id')
        
        if not project_id:
            return jsonify({'error': '缺少项目ID参数'}), 400
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询该项目的所有得分数据 - 使用SQL Server语法
        cursor.execute(
            """SELECT [评价等级], [专业], [条文号], [分类], [是否达标], [得分], [技术措施]
               FROM [得分表] 
               WHERE [项目ID]=?
               ORDER BY [评价等级], [专业], [条文号]""",
            (project_id,)
        )
        
        scores = []
        for row in cursor.fetchall():
            scores.append({
                'level': row[0],
                'specialty': row[1],
                'clause_number': row[2],
                'category': row[3],
                'is_achieved': row[4],
                'score': row[5],
                'technical_measures': row[6]
            })
        
        # 查询项目信息 - 使用SQL Server语法
        cursor.execute(
            """SELECT [id], [name], [code], [construction_unit], [design_unit], [location], [building_area], [building_type]
               FROM [projects] 
               WHERE [id]=?""",
            (project_id,)
        )
        
        project_row = cursor.fetchone()
        project = None
        if project_row:
            project = {
                'id': project_row[0],
                'name': project_row[1],
                'code': project_row[2],
                'construction_unit': project_row[3],
                'design_unit': project_row[4],
                'location': project_row[5],
                'building_area': project_row[6],
                'building_type': project_row[7]
            }
        
        conn.close()
        
        # 统计数据
        stats = {}
        if scores:
            for level in set(score['level'] for score in scores):
                level_scores = [s for s in scores if s['level'] == level]
                stats[level] = {}
                
                for specialty in set(score['specialty'] for score in level_scores):
                    specialty_scores = [s for s in level_scores if s['specialty'] == specialty]
                    total_items = len(specialty_scores)
                    achieved_items = len([s for s in specialty_scores if s['is_achieved'] == '是'])
                    total_score = sum(float(s['score']) for s in specialty_scores if s['score'].replace('.', '', 1).isdigit())
                    
                    stats[level][specialty] = {
                        'total_items': total_items,
                        'achieved_items': achieved_items,
                        'achievement_rate': round(achieved_items / total_items * 100, 2) if total_items > 0 else 0,
                        'total_score': round(total_score, 2)
                    }
        
        return jsonify({
            'success': True, 
            'project': project, 
            'scores': scores,
            'statistics': stats
        }), 200
    
    except Exception as e:
        app.logger.error(f"获取项目得分数据失败: {str(e)}")
        traceback.print_exc()  # 打印详细的错误堆栈
        return jsonify({'error': f'获取项目得分数据失败: {str(e)}'}), 500

# 添加数据库连接函数 - 支持SQL Server
def get_db_connection():
    try:
        # 直接使用已配置的数据库连接字符串
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        # 从连接字符串中提取参数
        # 格式：mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
        parts = db_url.replace('mssql+pyodbc://', '').split('@')
        auth = parts[0].split(':')
        username = auth[0]
        password = auth[1] if len(auth) > 1 else ''
        
        server_db = parts[1].split('/')
        server = server_db[0]
        db_with_params = server_db[1] if len(server_db) > 1 else ''
        
        # 分离数据库名和驱动程序
        db_parts = db_with_params.split('?')
        database = db_parts[0]
        
        # 使用正确的数据库名称 - 绿色建筑 而不是 缁垫缓鏍囧噯
        # 构建连接字符串 - 使用SQL Server驱动
        conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE=绿色建筑;UID={username};PWD={password}'
        
        print(f"连接数据库: SERVER={server}, DATABASE=绿色建筑, UID={username}")
        print(f"连接字符串: {conn_str.replace(password, '******')}")
        
        # 打印可用的ODBC驱动程序
        print(f"可用的ODBC驱动程序: {pyodbc.drivers()}")
        
        # 连接数据库
        print("尝试连接数据库...")
        conn = pyodbc.connect(conn_str)
        print("数据库连接成功!")
        return conn
    except Exception as e:
        print(f"数据库连接错误: {str(e)}")
        print(f"详细错误信息: {traceback.format_exc()}")
        app.logger.error(f"数据库连接错误: {str(e)}")
        app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise

# 初始化数据库
def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表已创建")
        
        # 创建得分表 - 使用SQL Server语法
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = N'得分表')
            BEGIN
                CREATE TABLE [得分表] (
                    [序号] INT IDENTITY(1,1) PRIMARY KEY,
                    [项目ID] INT,
                    [项目名称] NVARCHAR(255) NOT NULL,
                    [条文号] NVARCHAR(50) NOT NULL,
                    [分类] NVARCHAR(100),
                    [是否达标] NVARCHAR(10) DEFAULT N'否',
                    [得分] NVARCHAR(20) DEFAULT N'0',
                    [技术措施] NVARCHAR(MAX),
                    [评价等级] NVARCHAR(20) NOT NULL,
                    [专业] NVARCHAR(50) NOT NULL,
                    [评价标准] NVARCHAR(50) DEFAULT N'成都市标',
                    [创建时间] DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY([项目ID]) REFERENCES [projects]([id]) ON DELETE CASCADE,
                    CONSTRAINT UC_得分表 UNIQUE([项目ID], [条文号], [评价等级], [专业])
                )
            END
            """)
            
            # 检查评价标准字段是否存在，如果不存在则添加
            cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID(N'[得分表]') AND name = N'评价标准'
            )
            BEGIN
                ALTER TABLE [得分表] ADD [评价标准] NVARCHAR(50) DEFAULT N'成都市标'
            END
            """)
            
            conn.commit()
            conn.close()
            print("得分表创建成功")
        except Exception as e:
            print(f"创建得分表时出错: {str(e)}")
            traceback.print_exc()

# 修改get_score_summary函数，添加缓存
@cache.memoize(timeout=3600)
def get_score_summary(project_id):
    """获取项目评分汇总，使用缓存"""
    try:
        # 生成缓存键
        cache_key = f"score_summary_{project_id}"
        
        # 初始化评分汇总数据结构
        summary = {
            'advanced_level': {
                '建筑': {'total_score': 0},
                '结构': {'total_score': 0},
                '给排水': {'total_score': 0},
                '电气': {'total_score': 0},
                '暖通': {'total_score': 0},
                '景观': {'total_score': 0}
            },
            'by_category': {
                '安全耐久': {'total_score': 0},
                '健康舒适': {'total_score': 0},
                '生活便利': {'total_score': 0},
                '资源节约': {'total_score': 0},
                '环境宜居': {'total_score': 0},
                '提高与创新': {'total_score': 0}
            }
        }
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询提高级各专业得分
        cursor.execute("""
        SELECT 专业, SUM(CAST(得分 AS FLOAT)) AS total_score
        FROM 得分表
        WHERE 项目ID = ? AND 评价等级 = '提高级'
        GROUP BY 专业
        """, project_id)
        
        # 更新各专业得分
        for row in cursor.fetchall():
            specialty, score = row
            if specialty in summary['advanced_level']:
                summary['advanced_level'][specialty]['total_score'] = float(score)
        
        # 查询各分类得分
        cursor.execute("""
        SELECT 分类, SUM(CAST(得分 AS FLOAT)) AS total_score
        FROM 得分表
        WHERE 项目ID = ? AND 评价等级 = '提高级'
        GROUP BY 分类
        """, project_id)
        
        # 更新各分类得分
        for row in cursor.fetchall():
            category, score = row
            if category in summary['by_category']:
                summary['by_category'][category]['total_score'] = float(score)
        
        conn.close()
        
        # 记录日志
        print(f"获取评分汇总数据成功: 项目ID={project_id}")
        
        return summary
    except Exception as e:
        print(f"获取评分汇总数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'advanced_level': {
                '建筑': {'total_score': 0},
                '结构': {'total_score': 0},
                '给排水': {'total_score': 0},
                '电气': {'total_score': 0},
                '暖通': {'total_score': 0},
                '景观': {'total_score': 0}
            },
            'by_category': {
                '安全耐久': {'total_score': 0},
                '健康舒适': {'total_score': 0},
                '生活便利': {'total_score': 0},
                '资源节约': {'total_score': 0},
                '环境宜居': {'total_score': 0},
                '提高与创新': {'total_score': 0}
            }
        }

@cache.memoize(timeout=3600)
def calculate_specialty_scores(project_id=None, by_category=False):
    """
    计算各专业的总得分，使用缓存
    
    参数:
        project_id: 项目ID，如果为None则计算所有项目的得分
        by_category: 是否按分类计算得分
        
    返回值:
        包含各专业总得分的字典，如果by_category为True，则返回按分类细分的得分
    """
    try:
        # 生成缓存键
        cache_key = f"specialty_scores_{project_id}_{by_category}"
        
        # 专业名称映射
        specialties_map = {
            '建筑': '建筑专业',
            '结构': '结构专业',
            '给排水': '给排水专业',
            '电气': '电气专业',
            '暖通': '暖通空调专业',
            '景观': '景观专业'
        }
        
        # 分类列表
        categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
        
        # 初始化结果字典
        if by_category:
            # 按分类初始化
            specialty_scores = {}
            for specialty in specialties_map.values():
                specialty_scores[specialty] = {category: 0 for category in categories}
                specialty_scores[specialty]['总分'] = 0
        else:
            # 只计算总分
            specialty_scores = {specialty: 0 for specialty in specialties_map.values()}
        
        # 连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except Exception as db_error:
            app.logger.error(f"数据库连接失败: {str(db_error)}")
            return specialty_scores
        
        # 构建查询条件
        query_conditions = ["[评价等级] = N'提高级'"]
        query_params = []
        
        # 如果指定了项目ID，添加到查询条件
        if project_id:
            query_conditions.append("[项目ID] = ?")
            query_params.append(project_id)
        
        if by_category:
            # 按专业和分类查询得分
            query = f"""
            SELECT [专业], [分类], SUM(CAST([得分] AS float)) as total_score
            FROM [得分表]
            WHERE {' AND '.join(query_conditions)}
            GROUP BY [专业], [分类]
            """
            
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            # 更新各专业各分类得分
            for row in rows:
                specialty_db = row[0]
                category = row[1]
                score = float(row[2]) if row[2] is not None else 0
                
                # 如果专业在映射中且分类有效，更新对应的得分
                if specialty_db in specialties_map and category in categories:
                    specialty_display = specialties_map[specialty_db]
                    specialty_scores[specialty_display][category] = round(score, 2)
                    specialty_scores[specialty_display]['总分'] += round(score, 2)
        else:
            # 只查询各专业的总得分
            query = f"""
            SELECT [专业], SUM(CAST([得分] AS float)) as total_score
            FROM [得分表]
            WHERE {' AND '.join(query_conditions)}
            GROUP BY [专业]
            """
            
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            # 更新各专业得分
            for row in rows:
                specialty_db = row[0]
                score = float(row[1]) if row[1] is not None else 0
                
                # 如果专业在映射中，更新对应的得分
                if specialty_db in specialties_map:
                    specialty_display = specialties_map[specialty_db]
                    specialty_scores[specialty_display] = round(score, 2)
        
        # 关闭数据库连接
        conn.close()
        
        return specialty_scores
    
    except Exception as e:
        app.logger.error(f"计算专业得分失败: {str(e)}")
        traceback.print_exc()
        if by_category:
            # 返回空的分类结构
            result = {}
            for specialty in specialties_map.values():
                result[specialty] = {category: 0 for category in categories}
                result[specialty]['总分'] = 0
            return result
        else:
            return {specialty: 0 for specialty in specialties_map.values()}

# 添加API端点，用于获取各专业的总得分
@app.route('/api/specialty_scores', methods=['GET'])
def get_specialty_scores():
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
            total_score = sum(specialty_data['总分'] for specialty_data in specialty_scores.values())
            
            # 计算各分类的总分
            categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
            category_totals = {category: 0 for category in categories}
            
            for specialty, scores in specialty_scores.items():
                for category in categories:
                    category_totals[category] += scores[category]
            
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

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 根据环境变量决定是否开启调试模式
    debug_mode = not is_production
    app.logger.info(f"应用启动: 调试模式={debug_mode}")
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 