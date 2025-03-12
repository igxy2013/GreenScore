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

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# 配置缓存
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",  # 使用简单的内存缓存
    "CACHE_DEFAULT_TIMEOUT": 3600  # 缓存过期时间，单位秒（1小时）
}
cache = Cache(app, config=cache_config)

# 配置数据库连接
# 使用SQL Server数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
print(f"使用SQL Server数据库: {os.getenv('DATABASE_URL').replace(':' + os.getenv('DATABASE_URL').split(':')[2].split('@')[0] + '@', ':***@')}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # 打印SQL语句

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
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

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
    
    # 尝试多种筛选方法
    standards = []
    
    # 方法1: 使用属性字段精确匹配
    if attribute and specialty:
        query1 = Standard.query.filter(Standard.属性 == attribute).filter(Standard.专业.like(f'%{specialty}%'))
        standards1 = query1.all()
        print(f"方法1 (属性精确匹配): 找到 {len(standards1)} 条记录")
        if standards1:
            standards = standards1
    
    # 方法2: 使用属性字段模糊匹配
    if not standards and attribute:
        query2 = Standard.query
        query2 = query2.filter(Standard.属性.like(f'%{attribute}%'))
        if specialty:
            query2 = query2.filter(Standard.专业.like(f'%{specialty}%'))
        standards2 = query2.all()
        print(f"方法2 (属性模糊匹配): 找到 {len(standards2)} 条记录")
        if standards2:
            standards = standards2
    
    # 方法3: 只按专业筛选
    if not standards and specialty:
        query3 = Standard.query.filter(Standard.专业.like(f'%{specialty}%'))
        standards3 = query3.all()
        print(f"方法3 (仅按专业): 找到 {len(standards3)} 条记录")
        if standards3:
            standards = standards3
    
    # 如果所有方法都失败，返回所有记录
    if not standards:
        standards = Standard.query.all()
        print(f"所有筛选方法都失败，返回所有 {len(standards)} 条记录")
    
    end_time = time.time()
    print(f"筛选查询耗时: {end_time - start_time:.2f}秒")
    
    return standards

# 获取项目信息
def get_project():
    try:
        # 这里简单处理，获取第一个项目
        # 实际应用中可能需要根据用户会话或其他方式获取特定项目
        project = Project.query.first()
        return project
    except Exception as e:
        print(f"获取项目信息时出错: {str(e)}")
        return None

# 保存项目信息
def save_project_info(form_data):
    try:
        # 获取现有项目或创建新项目
        project = Project.query.first()
        if not project:
            project = Project()
        
        # 更新项目信息
        project.name = form_data.get('project_name', '')
        project.code = form_data.get('project_code', '')
        project.construction_unit = form_data.get('construction_unit', '')
        project.design_unit = form_data.get('design_unit', '')
        project.location = form_data.get('project_location', '')
        
        # 处理建筑面积，确保是数字
        building_area = form_data.get('building_area', '')
        if building_area and building_area.strip():
            try:
                project.building_area = float(building_area)
            except ValueError:
                project.building_area = 0
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        return project
    except Exception as e:
        db.session.rollback()
        print(f"保存项目信息时出错: {str(e)}")
        return None

@app.route('/')
def index():
    try:
        # 获取页面参数
        current_page = request.args.get('page', '')
        
        # 检查数据库连接
        db.session.execute(text("SELECT 1"))
        print("数据库连接成功!")
        
        # 使用缓存获取数据
        standards = get_all_standards()
        
        # 获取项目信息
        project = get_project()
        
        # 如果是绿色建材页面，直接使用静态HTML文件的内容
        if current_page == 'green_materials':
            # 通过iframe嵌入的方式来显示绿色建材计算器内容
            return render_template('index.html',
                                  standards=standards,
                                  current_page=current_page,
                                  project=project)
        
        # 如果是评分汇总页面，需要获取评分统计数据
        if current_page == 'score_summary':
            score_summary = get_score_summary(project.id if project else None)
            return render_template('index.html', 
                              standards=standards, 
                              current_page=current_page,
                              project=project,
                              score_summary=score_summary)
        
        return render_template('index.html', 
                              standards=standards, 
                              current_page=current_page,
                              project=project)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

@app.route('/', methods=['POST'])
def handle_form():
    try:
        form_type = request.form.get('form_type', '')
        
        if form_type == 'project_info':
            # 处理项目信息表单提交
            project = save_project_info(request.form)
            if project:
                print(f"项目信息保存成功: {project.name}")
            else:
                print("项目信息保存失败")
            
            # 重定向回项目信息页面
            return redirect(url_for('index', page='project_info'))
        
        # 如果不是已知的表单类型，返回首页
        return redirect(url_for('index'))
    except Exception as e:
        print(f"处理表单时发生错误: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', error=str(e))

@app.route('/filter')
def filter_standards():
    try:
        level = request.args.get('level', '')  # 基本级或提高级
        specialty = request.args.get('specialty', '')  # 专业
        
        print(f"请求筛选: 级别={level}, 专业={specialty}")
        
        # 使用缓存获取筛选后的数据
        standards = get_filtered_standards(level, specialty)
        
        # 获取项目信息
        project = get_project()
        
        return render_template('index.html', 
                            standards=standards, 
                            current_level=level, 
                            current_specialty=specialty,
                            current_page='specialty',
                            project=project)
    except Exception as e:
        print(f"筛选时发生错误: {str(e)}")
        print(traceback.format_exc())
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

@app.route('/api/save_score', methods=['POST'])
def save_score():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未接收到数据'}), 400
        
        level = data.get('level')
        specialty = data.get('specialty')
        scores = data.get('scores', [])
        # 从请求中获取项目ID
        project_id_from_request = data.get('project_id')
        
        if not scores:
            return jsonify({'error': '评分数据为空'}), 400
        
        # 优先使用请求中的项目ID，如果没有再使用查询的项目ID
        if project_id_from_request and str(project_id_from_request).strip():
            project_id = int(project_id_from_request)
        else:
            # 获取当前项目ID
            project = Project.query.first()
            project_id = project.id if project else None
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 批量执行插入操作
        for score in scores:
            # 处理得分值
            is_achieved = score.get('is_achieved', '否')
            score_value = score.get('score', '0')
            
            # 如果是基本级，得分始终为0
            if level == '基本级':
                score_value = '0'
            
            # SQL Server不支持REPLACE INTO，使用MERGE代替
            sql = """
            MERGE [得分表] AS target
            USING (SELECT ? AS [项目ID], ? AS [项目名称], ? AS [条文号], ? AS [分类], ? AS [是否达标], 
                         ? AS [得分], ? AS [技术措施], ? AS [评价等级], ? AS [专业]) AS source
            ON (target.[项目ID] = source.[项目ID] AND 
                target.[条文号] = source.[条文号] AND 
                target.[评价等级] = source.[评价等级] AND 
                target.[专业] = source.[专业])
            WHEN MATCHED THEN
                UPDATE SET 
                    target.[项目名称] = source.[项目名称],
                    target.[分类] = source.[分类],
                    target.[是否达标] = source.[是否达标],
                    target.[得分] = source.[得分],
                    target.[技术措施] = source.[技术措施]
            WHEN NOT MATCHED THEN
                INSERT ([项目ID], [项目名称], [条文号], [分类], [是否达标], [得分], [技术措施], [评价等级], [专业])
                VALUES (source.[项目ID], source.[项目名称], source.[条文号], source.[分类], 
                        source.[是否达标], source.[得分], source.[技术措施], source.[评价等级], source.[专业]);
            """
            
            cursor.execute(
                sql,
                (
                    project_id,
                    score.get('project_name', ''),
                    score.get('clause_number', ''),
                    score.get('category', ''),
                    is_achieved,
                    score_value,
                    score.get('technical_measures', ''),
                    level,
                    specialty
                )
            )
        
        # 提交事务
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'成功保存{len(scores)}条评分记录', 'project_id': project_id}), 200
    
    except Exception as e:
        # 记录错误信息到日志
        app.logger.error(f"保存评分失败: {str(e)}")
        traceback.print_exc()  # 打印详细的错误堆栈
        return jsonify({'error': f'保存评分失败: {str(e)}'}), 500

@app.route('/api/load_scores', methods=['GET'])
def load_scores():
    try:
        level = request.args.get('level')
        specialty = request.args.get('specialty')
        project_id = request.args.get('project_id')
        
        if not level or not specialty:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 获取当前项目ID（如果未指定）
        if not project_id:
            project = Project.query.first()
            project_id = project.id if project else None
        
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
        
        # 构建查询SQL
        query_sql = f"""SELECT [项目名称], [条文号], [分类], [是否达标], [得分], [技术措施] 
                        FROM [得分表] 
                        WHERE {' AND '.join(query_conditions)}"""
        
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
                'technical_measures': row[5]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'scores': scores}), 200
    
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
            """SELECT [id], [name], [code], [construction_unit], [design_unit], [location], [building_area]
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
                'building_area': project_row[6]
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
    # 使用与SQLAlchemy相同的连接字符串
    db_url = os.getenv('DATABASE_URL', '')
    
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
    
    # 构建连接字符串
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    # 连接数据库
    conn = pyodbc.connect(conn_str)
    return conn

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
                    [创建时间] DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY([项目ID]) REFERENCES [projects]([id]) ON DELETE CASCADE,
                    CONSTRAINT UC_得分表 UNIQUE([项目ID], [条文号], [评价等级], [专业])
                )
            END
            """)
            
            conn.commit()
            conn.close()
            print("得分表创建成功")
        except Exception as e:
            print(f"创建得分表时出错: {str(e)}")
            traceback.print_exc()

# 添加评分汇总函数
def get_score_summary(project_id):
    """
    获取项目的评分汇总数据
    
    参数:
        project_id: 项目ID
    
    返回值:
        包含评分汇总信息的字典
    """
    try:
        # 初始化默认返回结构，确保即使在失败时也返回有效结构
        default_result = {
            'basic_level': {},
            'advanced_level': {},
            'by_category': {},
            'matrix': {
                '建筑专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '结构专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '给排水专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '电气专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '暖通空调专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '景观专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                }
            }
        }
        
        if not project_id:
            app.logger.warning("获取评分汇总时项目ID为空")
            return default_result
        
        # 尝试连接数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
        except Exception as db_error:
            app.logger.error(f"数据库连接失败: {str(db_error)}")
            return default_result
        
        # 基本级专业评分汇总
        basic_level = {}
        specialties = ['建筑', '结构', '给排水', '电气', '暖通', '景观']
        
        for specialty in specialties:
            # 查询基本级该专业的评分数据
            try:
                query = """
                SELECT COUNT(*) as total_items,
                       SUM(CASE WHEN [是否达标] = N'是' THEN 1 ELSE 0 END) as achieved_items
                FROM [得分表]
                WHERE [项目ID] = ? AND [评价等级] = N'基本级' AND [专业] = ?
                """
                cursor.execute(query, (project_id, specialty))
                row = cursor.fetchone()
                
                if row and row[0] > 0:
                    total_items = row[0]
                    achieved_items = row[1] if row[1] is not None else 0
                    achievement_rate = round((achieved_items / total_items) * 100, 2) if total_items > 0 else 0
                    
                    basic_level[specialty] = {
                        'total_items': total_items,
                        'achieved_items': achieved_items,
                        'achievement_rate': achievement_rate
                    }
            except Exception as query_error:
                app.logger.error(f"查询基本级{specialty}专业评分数据失败: {str(query_error)}")
                # 继续下一个专业的查询
        
        # 提高级专业评分汇总
        advanced_level = {}
        
        for specialty in specialties:
            # 查询提高级该专业的评分数据
            try:
                query = """
                SELECT COUNT(*) as total_items,
                       SUM(CAST([得分] AS float)) as total_score
                FROM [得分表]
                WHERE [项目ID] = ? AND [评价等级] = N'提高级' AND [专业] = ?
                """
                cursor.execute(query, (project_id, specialty))
                row = cursor.fetchone()
                
                if row and row[0] > 0:
                    total_items = row[0]
                    total_score = float(row[1]) if row[1] is not None else 0
                    
                    # 计算该专业的最大可能分值
                    max_query = """
                    SELECT SUM(CAST([分值] AS float)) as max_score
                    FROM [成都市标]
                    WHERE [属性] = N'评分项' AND [专业] LIKE ?
                    """
                    try:
                        cursor.execute(max_query, (f'%{specialty}%',))
                        max_row = cursor.fetchone()
                        max_score = float(max_row[0]) if max_row and max_row[0] is not None else 100
                    except Exception:
                        max_score = 100  # 如果查询失败，使用默认值
                    
                    score_rate = round((total_score / max_score) * 100, 2) if max_score > 0 else 0
                    
                    advanced_level[specialty] = {
                        'total_items': total_items,
                        'total_score': total_score,
                        'max_score': max_score,
                        'score_rate': score_rate
                    }
            except Exception as query_error:
                app.logger.error(f"查询提高级{specialty}专业评分数据失败: {str(query_error)}")
                # 继续下一个专业的查询
        
        # 按分类汇总（提高级）
        by_category = {}
        categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
        
        for category in categories:
            # 查询该分类的评分数据
            try:
                query = """
                SELECT COUNT(*) as total_items,
                       SUM(CAST([得分] AS float)) as total_score
                FROM [得分表]
                WHERE [项目ID] = ? AND [评价等级] = N'提高级' AND [分类] = ?
                """
                cursor.execute(query, (project_id, category))
                row = cursor.fetchone()
                
                if row and row[0] > 0:
                    total_items = row[0]
                    total_score = float(row[1]) if row[1] is not None else 0
                    
                    # 计算该分类的最大可能分值
                    max_query = """
                    SELECT SUM(CAST([分值] AS float)) as max_score
                    FROM [成都市标]
                    WHERE [属性] = N'评分项' AND [分类] = ?
                    """
                    try:
                        cursor.execute(max_query, (category,))
                        max_row = cursor.fetchone()
                        max_score = float(max_row[0]) if max_row and max_row[0] is not None else 100
                    except Exception:
                        max_score = 100  # 如果查询失败，使用默认值
                    
                    score_rate = round((total_score / max_score) * 100, 2) if max_score > 0 else 0
                    
                    by_category[category] = {
                        'total_items': total_items,
                        'total_score': total_score,
                        'max_score': max_score,
                        'score_rate': score_rate
                    }
            except Exception as query_error:
                app.logger.error(f"查询{category}分类评分数据失败: {str(query_error)}")
                # 继续下一个分类的查询
        
        # 初始化矩阵数据结构（使用默认结构）
        matrix = default_result['matrix'].copy()
        
        # 查询专业和分类的得分数据
        try:
            specialties_map = {
                '建筑': '建筑专业',
                '结构': '结构专业',
                '给排水': '给排水专业',
                '电气': '电气专业',
                '暖通': '暖通空调专业',
                '景观': '景观专业'
            }
            
            categories = ['安全耐久', '健康舒适', '生活便利', '资源节约', '环境宜居', '提高与创新']
            
            query = """
            SELECT [专业], [分类], SUM(CAST([得分] AS float)) as total_score
            FROM [得分表]
            WHERE [项目ID] = ? AND [评价等级] = N'提高级'
            GROUP BY [专业], [分类]
            """
            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()
            
            # 更新矩阵数据
            for row in rows:
                specialty_db = row[0]
                category = row[1]
                score = float(row[2]) if row[2] is not None else 0
                
                # 跳过未知的专业或分类
                if specialty_db not in specialties_map or category not in categories:
                    continue
                    
                specialty_display = specialties_map[specialty_db]
                matrix[specialty_display][category] = int(score)
        except Exception as matrix_error:
            app.logger.error(f"查询矩阵数据失败: {str(matrix_error)}")
            # 使用默认矩阵数据
        
        # 无论成功与否，确保关闭数据库连接
        try:
            conn.close()
        except Exception:
            pass
        
        # 返回结果，确保所有键都存在
        return {
            'basic_level': basic_level,
            'advanced_level': advanced_level,
            'by_category': by_category,
            'matrix': matrix
        }
    
    except Exception as e:
        app.logger.error(f"获取评分汇总数据失败: {str(e)}")
        traceback.print_exc()
        
        # 出现任何错误时，返回带有默认矩阵的结构，而不是None
        return {
            'basic_level': {},
            'advanced_level': {},
            'by_category': {},
            'matrix': {
                '建筑专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '结构专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '给排水专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '电气专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '暖通空调专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                },
                '景观专业': {
                    '安全耐久': 0,
                    '健康舒适': 0,
                    '生活便利': 0,
                    '资源节约': 0,
                    '环境宜居': 0,
                    '提高与创新': 0
                }
            }
        }

def calculate_specialty_scores(project_id=None, by_category=False):
    """
    计算各专业的总得分
    
    参数:
        project_id: 项目ID，如果为None则计算所有项目的得分
        by_category: 是否按分类计算得分
        
    返回值:
        包含各专业总得分的字典，如果by_category为True，则返回按分类细分的得分
    """
    try:
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
    
    app.run(debug=True) 