from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from models import User, InvitationCode, LogRecord, db
from functools import wraps
import random
import string
from datetime import datetime

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
        'avg_project_score': round(sum(project.total_score or 0 for project in valid_projects) / len(valid_projects), 2) if valid_projects else 0
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
@admin_app.route('/admin/api/projects', methods=['GET'])
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

@admin_app.route('/admin/api/projects/<int:project_id>', methods=['GET'])
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

@admin_app.route('/admin/api/projects', methods=['POST'])
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

@admin_app.route('/admin/api/projects/<int:project_id>', methods=['PUT'])
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

@admin_app.route('/admin/api/projects/<int:project_id>', methods=['DELETE'])
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

# 日志管理API路由
@admin_app.route('/admin/api/logs', methods=['GET'])
@login_required
@admin_required
def get_all_logs():
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 获取筛选参数
        level = request.args.get('level')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        source = request.args.get('source')
        keyword = request.args.get('keyword')
        
        # 构建查询
        query = LogRecord.query
        
        # 应用筛选条件
        if level:
            query = query.filter(LogRecord.level == level)
        if start_date:
            query = query.filter(LogRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(LogRecord.timestamp <= end_date)
        if user_id:
            query = query.filter(LogRecord.user_id == user_id)
        if source:
            query = query.filter(LogRecord.source == source)
        if keyword:
            query = query.filter(LogRecord.message.like(f'%{keyword}%'))
        
        # 按时间倒序排序并分页
        logs_pagination = query.order_by(LogRecord.timestamp.desc()).paginate(page=page, per_page=per_page)
        
        # 获取关联的用户信息
        user_dict = {}
        user_ids = set(log.user_id for log in logs_pagination.items if log.user_id)
        if user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
            user_dict = {user.id: user.email for user in users}
        
        # 准备返回数据
        logs_data = []
        for log in logs_pagination.items:
            log_data = {
                'id': log.id,
                'level': log.level,
                'message': log.message,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'source': log.source,
                'user_id': log.user_id,
                'user_email': user_dict.get(log.user_id, '未知用户') if log.user_id else None,
                'ip_address': log.ip_address,
                'path': log.path,
                'method': log.method,
                'user_agent': log.user_agent
            }
            logs_data.append(log_data)
        
        return jsonify({
            'success': True,
            'logs': logs_data,
            'total': logs_pagination.total,
            'pages': logs_pagination.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/admin/api/logs/levels', methods=['GET'])
@login_required
@admin_required
def get_log_levels():
    try:
        # 获取所有不同的日志级别
        levels = db.session.query(LogRecord.level).distinct().all()
        levels = [level[0] for level in levels]
        
        return jsonify({
            'success': True,
            'levels': levels
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/admin/api/logs/sources', methods=['GET'])
@login_required
@admin_required
def get_log_sources():
    try:
        # 获取所有不同的日志来源
        sources = db.session.query(LogRecord.source).distinct().all()
        sources = [source[0] for source in sources if source[0]]
        
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/admin/api/logs/stats', methods=['GET'])
@login_required
@admin_required
def get_log_stats():
    try:
        # 获取总日志数
        total_logs = LogRecord.query.count()
        
        # 获取各级别日志数量
        level_stats = db.session.query(
            LogRecord.level, 
            db.func.count(LogRecord.id)
        ).group_by(LogRecord.level).all()
        level_stats = {level: count for level, count in level_stats}
        
        # 获取今日日志数量
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_logs = LogRecord.query.filter(LogRecord.timestamp >= today).count()
        
        # 获取最近一周的日志趋势
        from datetime import timedelta
        week_stats = []
        for i in range(7):
            day = today - timedelta(days=i)
            next_day = day + timedelta(days=1)
            count = LogRecord.query.filter(
                LogRecord.timestamp >= day,
                LogRecord.timestamp < next_day
            ).count()
            week_stats.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return jsonify({
            'success': True,
            'total_logs': total_logs,
            'level_stats': level_stats,
            'today_logs': today_logs,
            'week_stats': week_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/admin/api/logs/export', methods=['GET'])
@login_required
@admin_required
def export_logs():
    import csv
    from io import StringIO
    from flask import Response
    
    try:
        # 获取筛选参数
        level = request.args.get('level')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        source = request.args.get('source')
        keyword = request.args.get('keyword')
        
        # 构建查询
        query = LogRecord.query
        
        # 应用筛选条件
        if level:
            query = query.filter(LogRecord.level == level)
        if start_date:
            query = query.filter(LogRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(LogRecord.timestamp <= end_date)
        if user_id:
            query = query.filter(LogRecord.user_id == user_id)
        if source:
            query = query.filter(LogRecord.source == source)
        if keyword:
            query = query.filter(LogRecord.message.like(f'%{keyword}%'))
        
        # 按时间倒序排序
        logs = query.order_by(LogRecord.timestamp.desc()).all()
        
        # 获取关联的用户信息
        user_dict = {}
        user_ids = set(log.user_id for log in logs if log.user_id)
        if user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
            user_dict = {user.id: user.email for user in users}
        
        # 创建CSV文件
        si = StringIO()
        writer = csv.writer(si)
        
        # 写入表头
        writer.writerow(['ID', '级别', '消息', '时间', '来源', '用户ID', '用户邮箱', 'IP地址', '请求路径', '请求方法', '用户代理'])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                log.id,
                log.level,
                log.message,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.source or '',
                log.user_id or '',
                user_dict.get(log.user_id, '') if log.user_id else '',
                log.ip_address or '',
                log.path or '',
                log.method or '',
                log.user_agent or ''
            ])
        
        # 返回CSV文件
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=logs.csv"}
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_app.route('/admin/api/logs/clear', methods=['DELETE'])
@login_required
@admin_required
def clear_logs():
    try:
        # 获取筛选参数
        level = request.args.get('level')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        source = request.args.get('source')
        keyword = request.args.get('keyword')
        
        # 构建查询
        query = LogRecord.query
        
        # 应用筛选条件
        if level:
            query = query.filter(LogRecord.level == level)
        if start_date:
            query = query.filter(LogRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(LogRecord.timestamp <= end_date)
        if user_id:
            query = query.filter(LogRecord.user_id == user_id)
        if source:
            query = query.filter(LogRecord.source == source)
        if keyword:
            query = query.filter(LogRecord.message.like(f'%{keyword}%'))
        
        # 记录删除的日志数量
        count = query.count()
        
        # 执行删除
        query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功清除 {count} 条日志记录',
            'count': count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=5001, debug=True)