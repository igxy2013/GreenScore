from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for
from auth import authenticate_user, update_last_login

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """登录状态检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录处理"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        update_last_login(user['id'])
        return jsonify({'message': '登录成功', 'redirect': '/project_management'})
    
    return jsonify({'error': '用户名或密码错误'}), 401

@auth_bp.route('/api/logout')
def logout():
    """用户登出"""
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route('/api/check_auth')
def check_auth():
    """检查用户登录状态"""
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')})
    return jsonify({'authenticated': False}), 401