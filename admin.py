from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from models import User, InvitationCode, db
from functools import wraps

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
    return render_template('admin/dashboard.html', users=users, invite_codes=invite_codes)

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

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=5001, debug=True)