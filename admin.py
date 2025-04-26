from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from models import User, InvitationCode, db
from functools import wraps
import random
import string
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import time

# 创建管理后台蓝图
admin_app = Blueprint('admin', __name__, 
                    template_folder='templates/admin',  # 指定模板目录
                    static_folder='static')            # 指定静态文件目录

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == 'admin':
            flash('只有管理员可以访问此页面')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_app.route('/')
@admin_app.route('/login', methods=['GET'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('.dashboard'))
    return render_template('admin/login.html')

@admin_app.route('/login', methods=['POST'])
def admin_login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password) and user.role == 'admin':
        # 更新最后在线时间
        user.last_seen = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        session['role'] = user.role
        return redirect(url_for('.dashboard'))
    
    flash('邮箱或密码错误，或者您没有管理员权限')
    return redirect(url_for('.admin_login'))

@admin_app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    invite_codes = InvitationCode.query.all()
    
    # 导入Project模型
    from app import Project
    
    # 获取所有项目
    projects = Project.query.all()
    
    # 过滤掉None值，确保计算统计数据时不会出错
    valid_users = [user for user in users if user is not None]
    valid_invite_codes = [code for code in invite_codes if code is not None]
    valid_projects = [project for project in projects if project is not None]
    
    # 计算用户统计数据
    stats = {
        'total_users': len(valid_users),
        'online_users': sum(1 for user in valid_users if user.is_online()),
        'offline_users': sum(1 for user in valid_users if not user.is_online()),
        'admin_users': sum(1 for user in valid_users if user.role == 'admin'),
        # 添加项目统计数据
        'total_projects': len(valid_projects),
        'active_projects': sum(1 for project in valid_projects if project.total_score is None),
        'completed_projects': sum(1 for project in valid_projects if project.total_score is not None),
        'avg_project_score': round(sum(project.total_score for project in valid_projects if project.total_score is not None) / len([p for p in valid_projects if p.total_score is not None]), 2) if any(project.total_score is not None for project in valid_projects) else 0
    }
    
    return render_template('admin/dashboard.html', users=valid_users, invite_codes=valid_invite_codes, projects=valid_projects, stats=stats)

@admin_app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json()
    
    if not all(key in data for key in ['email', 'password', 'role']):
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': '该邮箱已被注册'}), 400
    
    try:
        new_user = User()
        new_user.email = data['email']
        new_user.set_password(data['password'])
        new_user.role = data['role']
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'role': new_user.role
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@admin_app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'message': '该邮箱已被使用'}), 400
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if 'role' in data:
            user.role = data['role']
        
        db.session.commit()
        return jsonify({'success': True, 'message': '用户信息更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == session.get('user_id'):
        return jsonify({'success': False, 'message': '不能删除当前登录的用户'}), 400
    
    try:
        # 先处理邀请码表中的关联
        InvitationCode.query.filter_by(used_by=user.id).update({'used_by': None})
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/logout')
@login_required
def admin_logout():
    logout_user()
    session.clear()
    return redirect(url_for('.admin_login'))

@admin_app.route('/api/invite-codes', methods=['POST'])
@login_required
@admin_required
def generate_invite_code():
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
        return jsonify({'success': False, 'message': '生成邀请码失败'}), 500

@admin_app.route('/api/invite-codes/<int:code_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_invite_code(code_id):
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
        
# 项目管理API路由
@admin_app.route('/api/projects', methods=['GET'])
@login_required
@admin_required
def get_all_projects():
    try:
        # 导入Project模型
        from app import Project, User
        
        # 获取所有项目，并按创建时间降序排序
        projects = Project.query.order_by(Project.created_at.desc()).all()
        
        # 将项目数据转换为JSON格式
        projects_data = []
        for project in projects:
            # 获取项目所属用户
            user = User.query.get(project.user_id)
            user_email = user.email if user else '未知用户'
            
            projects_data.append({
                'id': project.id,
                'name': project.name,
                'user_id': project.user_id,
                'user_email': user_email,
                'code': project.code,
                'construction_unit': project.construction_unit,
                'design_unit': project.design_unit,
                'location': project.location,
                'building_area': project.building_area,
                'building_type': project.building_type,
                'standard': project.standard,
                'score': project.total_score,
                'created_at': project.created_at
            })
        
        return jsonify({
            'success': True,
            'projects': projects_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/projects/<int:project_id>', methods=['GET'])
@login_required
@admin_required
def get_project(project_id):
    try:
        # 导入Project模型
        from app import Project, User
        
        # 获取指定项目
        project = Project.query.get_or_404(project_id)
        
        # 获取项目所属用户
        user = User.query.get(project.user_id)
        user_email = user.email if user else '未知用户'
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'user_id': project.user_id,
            'user_email': user_email,
            'code': project.code,
            'construction_unit': project.construction_unit,
            'design_unit': project.design_unit,
            'location': project.location,
            'building_area': project.building_area,
            'building_type': project.building_type,
            'standard': project.standard,
            'score': project.total_score,
            'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else None
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/projects', methods=['POST'])
@login_required
@admin_required
def create_project():
    try:
        # 导入Project模型
        from app import Project
        
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'user_id']):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 创建新项目
        new_project = Project(
            name=data['name'],
            user_id=data['user_id'],
            standard=data.get('standard'),
            score=data.get('score')
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目创建成功',
            'project': {
                'id': new_project.id,
                'name': new_project.name,
                'user_id': new_project.user_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
@admin_required
def update_project(project_id):
    try:
        # 导入Project模型
        from app import Project
        
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # 更新项目信息
        if 'name' in data:
            project.name = data['name']
        if 'user_id' in data:
            project.user_id = data['user_id']
        if 'score' in data and data['score'] is not None:
            project.total_score = float(data['score'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': '项目更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_project(project_id):
    try:
        # 导入Project模型
        from app import Project
        
        # 这里使用get_or_404直接获取项目，不做用户ID筛选，允许管理员删除任何项目
        project = Project.query.get_or_404(project_id)
        
        # 删除项目
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': '项目删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '删除项目失败: ' + str(e)}), 500

# 评价标准管理API路由
@admin_app.route('/api/standards', methods=['GET'])
@login_required
@admin_required
def get_all_standards():
    try:
        # 导入评价标准模型
        from app import review_standard, db
        import traceback
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 获取筛选参数
        standard_name = request.args.get('standard_name', '')
        specialty = request.args.get('specialty', '')
        attribute = request.args.get('attribute', '')
        query_text = request.args.get('query', '')
        
        # 记录请求信息
        print(f"获取标准数据请求: page={page}, per_page={per_page}, standard_name={standard_name}, specialty={specialty}, attribute={attribute}, query={query_text}")
        
        # 构建查询
        query = review_standard.query
        
        # 应用筛选条件
        if standard_name:
            query = query.filter(review_standard.标准名称 == standard_name)
        if specialty:
            query = query.filter(review_standard.专业.like(f'%{specialty}%'))
        if attribute:
            query = query.filter(review_standard.属性 == attribute)
        if query_text:
            # 在条文号和条文内容中搜索
            query = query.filter(
                db.or_(
                    review_standard.条文号.like(f'%{query_text}%'),
                    review_standard.条文内容.like(f'%{query_text}%')
                )
            )
            
        # 按序号排序
        query = query.order_by(review_standard.序号.asc())
        
        # 获取记录总数
        total_count = query.count()
        print(f"查询到符合条件的标准数: {total_count}")
        
        # 空结果处理
        if total_count == 0:
            return jsonify({
                'success': True,
                'standards': [],
                'pagination': {
                    'total': 0,
                    'pages': 0,
                    'page': page,
                    'per_page': per_page,
                    'has_next': False,
                    'has_prev': False
                }
            })
        
        # 计算总页数
        total_pages = (total_count + per_page - 1) // per_page
        
        # 调整页码范围
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # 获取分页数据
        try:
            standards_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            standards = standards_pagination.items
        except Exception as e:
            print(f"分页错误: {str(e)}")
            print(traceback.format_exc())
            # 兼容旧版SQLAlchemy
            offset = (page - 1) * per_page
            standards = query.limit(per_page).offset(offset).all()
            standards_pagination = type('Pagination', (), {
                'total': total_count,
                'pages': total_pages,
                'page': page,
                'per_page': per_page,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'items': standards
            })
        
        # 将标准数据转换为JSON格式
        standards_data = []
        for standard in standards:
            standards_data.append({
                '序号': standard.序号,
                '条文号': standard.条文号,
                '分类': standard.分类,
                '专业': standard.专业,
                '条文内容': standard.条文内容,
                '分值': standard.分值,
                '审查材料': standard.审查材料,
                '属性': standard.属性,
                '标准名称': standard.标准名称,
                '图片路径': standard.图片路径
            })
        
        print(f"返回标准数据: {len(standards_data)}条")
        
        # 返回数据和分页信息
        return jsonify({
            'success': True,
            'standards': standards_data,
            'pagination': {
                'total': standards_pagination.total,
                'pages': standards_pagination.pages,
                'page': page,
                'per_page': per_page,
                'has_next': standards_pagination.has_next,
                'has_prev': standards_pagination.has_prev
            }
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"获取标准数据错误: {str(e)}")
        print(error_trace)
        return jsonify({'success': False, 'message': f'获取标准数据失败: {str(e)}'}), 500

@admin_app.route('/api/standards/names', methods=['GET'])
@login_required
@admin_required
def get_standard_names():
    try:
        # 导入评价标准模型
        from app import review_standard, db
        
        # 查询所有不同的标准名称
        standard_names = db.session.query(review_standard.标准名称).distinct().all()
        
        # 转换为列表格式并过滤空值
        names_list = [name[0] for name in standard_names if name[0]]
        
        # 确保包含默认标准
        default_standards = ['成都市标', '四川省标', '国标']
        for std in default_standards:
            if std not in names_list:
                names_list.append(std)
        
        # 对标准名称排序
        names_list = sorted(names_list)
        
        print(f"获取到的标准名称: {names_list}")
        
        return jsonify({
            'success': True,
            'standard_names': names_list
        })
    except Exception as e:
        import traceback
        print(f"获取标准名称失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取标准名称失败: {str(e)}'}), 500

@admin_app.route('/api/standards', methods=['POST'])
@login_required
@admin_required
def create_standard():
    try:
        # 导入评价标准模型
        from app import review_standard, db
        
        # 处理表单数据或JSON数据
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 处理表单数据（包含文件上传）
            standard_data = {
                '条文号': request.form.get('条文号', ''),
                '分类': request.form.get('分类', ''),
                '专业': request.form.get('专业', ''),
                '条文内容': request.form.get('条文内容', ''),
                '分值': request.form.get('分值', '0'),
                '审查材料': request.form.get('审查材料', ''),
                '属性': request.form.get('属性', '控制项'),
                '标准名称': request.form.get('标准名称', '成都市标'),
                '图片路径': None
            }
            
            # 处理图片上传
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                
                # 确保文件名安全
                filename = secure_filename(image_file.filename)
                
                # 确保上传目录存在
                upload_folder = os.path.join('static', 'uploads', 'standard_images')
                os.makedirs(upload_folder, exist_ok=True)
                
                # 生成唯一文件名（使用时间戳和原文件名）
                unique_filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                
                # 保存文件
                image_file.save(file_path)
                
                # 更新标准数据的图片路径
                standard_data['图片路径'] = f"/static/uploads/standard_images/{unique_filename}"
        else:
            # 处理JSON数据
            data = request.get_json()
            standard_data = {
                '条文号': data.get('条文号', ''),
                '分类': data.get('分类', ''),
                '专业': data.get('专业', ''),
                '条文内容': data.get('条文内容', ''),
                '分值': data.get('分值', '0'),
                '审查材料': data.get('审查材料', ''),
                '属性': data.get('属性', '控制项'),
                '标准名称': data.get('标准名称', '成都市标'),
                '图片路径': None
            }
        
        # 验证必要字段
        required_fields = ['条文号', '专业', '条文内容', '属性', '标准名称']
        for field in required_fields:
            if not standard_data[field]:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 创建新的标准记录
        new_standard = review_standard(
            条文号=standard_data['条文号'],
            分类=standard_data['分类'],
            专业=standard_data['专业'],
            条文内容=standard_data['条文内容'],
            分值=standard_data['分值'],
            审查材料=standard_data['审查材料'],
            属性=standard_data['属性'],
            标准名称=standard_data['标准名称'],
            图片路径=standard_data['图片路径']
        )
        
        db.session.add(new_standard)
        db.session.commit()
        
        print(f"标准创建成功: 序号={new_standard.序号}, 条文号={new_standard.条文号}")
        
        return jsonify({
            'success': True,
            'message': '标准创建成功',
            'standard': {
                '序号': new_standard.序号,
                '条文号': new_standard.条文号,
                '标准名称': new_standard.标准名称,
                '图片路径': new_standard.图片路径
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"创建标准失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'创建标准失败: {str(e)}'}), 500

@admin_app.route('/api/standards/<int:standard_id>', methods=['PUT'])
@login_required
@admin_required
def update_standard(standard_id):
    try:
        # 导入评价标准模型
        from app import review_standard, db
        import os
        from werkzeug.utils import secure_filename
        
        # 查找要更新的标准
        standard = review_standard.query.get_or_404(standard_id)
        
        # 处理表单数据或JSON数据
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 处理表单数据（包含文件上传）
            standard_data = {
                '条文号': request.form.get('条文号', standard.条文号),
                '分类': request.form.get('分类', standard.分类),
                '专业': request.form.get('专业', standard.专业),
                '条文内容': request.form.get('条文内容', standard.条文内容),
                '分值': request.form.get('分值', standard.分值),
                '审查材料': request.form.get('审查材料', standard.审查材料),
                '属性': request.form.get('属性', standard.属性),
                '标准名称': request.form.get('标准名称', standard.标准名称)
            }
            
            # 检查是否要删除图片
            delete_image = request.form.get('deleteImage') == 'true'
            if delete_image and standard.图片路径:
                # 删除文件系统中的图片文件
                old_image_path = os.path.join('static', standard.图片路径.split('/static/')[-1])
                try:
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                        print(f"删除图片文件成功: {old_image_path}")
                except Exception as e:
                    print(f"删除图片文件失败: {str(e)}")
                
                # 清空图片路径
                standard.图片路径 = None
                print(f"清空标准图片路径: ID={standard_id}")
            
            # 处理图片上传
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                
                # 确保文件名安全
                filename = secure_filename(image_file.filename)
                
                # 确保上传目录存在
                upload_folder = os.path.join('static', 'uploads', 'standard_images')
                os.makedirs(upload_folder, exist_ok=True)
                
                # 生成唯一文件名（使用时间戳和原文件名）
                unique_filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                
                # 保存文件
                image_file.save(file_path)
                
                # 如果有旧图片且不是刚被删除的，尝试删除
                if standard.图片路径:
                    old_image_path = os.path.join('static', standard.图片路径.split('/static/')[-1])
                    try:
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                            print(f"上传新图片时删除旧图片成功: {old_image_path}")
                    except Exception as e:
                        print(f"上传新图片时删除旧图片失败: {str(e)}")
                
                # 更新标准数据的图片路径
                standard.图片路径 = f"/static/uploads/standard_images/{unique_filename}"
        else:
            # 处理JSON数据
            data = request.get_json()
            
            if '条文号' in data:
                standard.条文号 = data['条文号']
            if '分类' in data:
                standard.分类 = data['分类']
            if '专业' in data:
                standard.专业 = data['专业']
            if '条文内容' in data:
                standard.条文内容 = data['条文内容']
            if '分值' in data:
                standard.分值 = data['分值']
            if '审查材料' in data:
                standard.审查材料 = data['审查材料']
            if '属性' in data:
                standard.属性 = data['属性']
            if '标准名称' in data:
                standard.标准名称 = data['标准名称']
        
        # 更新字段
        if request.content_type and 'multipart/form-data' in request.content_type:
            standard.条文号 = standard_data['条文号']
            standard.分类 = standard_data['分类']
            standard.专业 = standard_data['专业']
            standard.条文内容 = standard_data['条文内容']
            standard.分值 = standard_data['分值']
            standard.审查材料 = standard_data['审查材料']
            standard.属性 = standard_data['属性']
            standard.标准名称 = standard_data['标准名称']
        
        db.session.commit()
        
        print(f"标准更新成功: ID={standard_id}")
        
        return jsonify({
            'success': True,
            'message': '标准更新成功'
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"更新标准失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'更新标准失败: {str(e)}'}), 500

@admin_app.route('/api/standards/<int:standard_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_standard(standard_id):
    try:
        # 导入评价标准模型
        from app import review_standard, db
        
        # 查找要删除的标准
        standard = review_standard.query.get_or_404(standard_id)
        print(f"删除标准: ID={standard_id}, 条文号={standard.条文号}, 标准名称={standard.标准名称}")
        
        # 删除标准
        db.session.delete(standard)
        db.session.commit()
        
        print(f"标准删除成功: ID={standard_id}")
        
        return jsonify({
            'success': True,
            'message': '标准删除成功'
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"删除标准失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'删除标准失败: {str(e)}'}), 500

# 添加标准导入API
@admin_app.route('/api/standards/import', methods=['POST'])
@login_required
@admin_required
def import_standards():
    try:
        from app import review_standard, db
        import pandas as pd
        import os
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
            
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
            
        # 检查文件类型
        allowed_extensions = {'csv', 'xlsx', 'xls'}
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'message': '文件类型不支持，请上传.csv、.xlsx或.xls文件'}), 400
        
        # 保存临时文件
        temp_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        # 读取文件内容
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:
                df = pd.read_excel(temp_path)
        except Exception as e:
            os.remove(temp_path)
            return jsonify({'success': False, 'message': f'读取文件失败: {str(e)}'}), 400
        
        # 清理临时文件
        os.remove(temp_path)
        
        # 验证必要列
        required_columns = ['条文号', '专业', '条文内容', '属性', '标准名称']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'success': False, 'message': f'文件缺少必要列: {", ".join(missing_columns)}'}), 400
        
        # 导入数据
        imported_count = 0
        for _, row in df.iterrows():
            try:
                # 创建新的标准记录
                standard = review_standard(
                    条文号=str(row['条文号']),
                    分类=str(row.get('分类', '')),
                    专业=str(row['专业']),
                    条文内容=str(row['条文内容']),
                    分值=str(row.get('分值', '0')),
                    审查材料=str(row.get('审查材料', '')),
                    属性=str(row['属性']),
                    标准名称=str(row['标准名称'])
                )
                
                db.session.add(standard)
                imported_count += 1
                
                # 每100条提交一次，减少内存占用
                if imported_count % 100 == 0:
                    db.session.commit()
            except Exception as e:
                print(f"导入行数据失败: {str(e)}")
                print(f"行数据: {row}")
                continue
        
        # 提交剩余事务
        db.session.commit()
        
        print(f"标准导入成功: 共导入{imported_count}条记录")
        
        return jsonify({
            'success': True,
            'message': f'标准导入成功',
            'imported_count': imported_count
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"导入标准失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'导入标准失败: {str(e)}'}), 500

# 获取单个标准详情
@admin_app.route('/api/standards/<int:standard_id>', methods=['GET'])
@login_required
@admin_required
def get_standard(standard_id):
    try:
        # 导入评价标准模型
        from app import review_standard, db
        
        # 查找指定ID的标准
        standard = review_standard.query.get_or_404(standard_id)
        
        print(f"获取标准详情: ID={standard_id}, 条文号={standard.条文号}, 标准名称={standard.标准名称}")
        
        # 将标准数据转换为JSON格式
        standard_data = {
            '序号': standard.序号,
            '条文号': standard.条文号,
            '分类': standard.分类,
            '专业': standard.专业,
            '条文内容': standard.条文内容,
            '分值': standard.分值,
            '审查材料': standard.审查材料,
            '属性': standard.属性,
            '标准名称': standard.标准名称,
            '图片路径': standard.图片路径
        }
        
        return jsonify({
            'success': True,
            'standard': standard_data
        })
    except Exception as e:
        import traceback
        print(f"获取标准详情失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取标准详情失败: {str(e)}'}), 500

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=5001, debug=True)