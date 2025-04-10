from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for, send_file
from auth import authenticate_user, update_last_login
import os
from transport_helper import generate_transport_report

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

@auth_bp.route('/api/generate_transport_report', methods=['POST'])
def api_generate_transport_report():
    try:
        # 获取前端发送的数据
        data = request.json
        
        if not data:
            return jsonify({"error": "没有接收到数据"}), 400
        
        # 生成报告
        report_path = generate_transport_report(data)
        
        # 返回生成的报告文件
        return send_file(report_path, as_attachment=True, 
                         download_name=f"公共交通站点分析报告_{data.get('address', '地址未知')}.docx")
    
    except Exception as e:
        print(f"生成报告时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/api/project_info', methods=['GET'])
def api_get_project_info():
    try:
        # 获取项目ID参数
        project_id = request.args.get('project_id')
        
        # 如果没有提供项目ID，返回空信息
        if not project_id:
            return jsonify({})
        
        # 从数据库获取项目信息
        # 这里需要根据实际的数据库模型来实现
        # 例如：
        # from models import Project
        # project = Project.query.get(project_id)
        # if project:
        #     project_info = {
        #         "项目名称": project.name,
        #         "项目地点": project.location,
        #         # 其他字段...
        #     }
        # else:
        #     project_info = {}
        
        # 示例数据
        project_info = {
            "项目名称": "示例项目",
            "项目地点": "示例地址",
            "项目编号": "EXAMPLE-001",
            "建设单位": "示例建设公司",
            "设计单位": "示例设计院",
            "总用地面积": "10000",
            "总建筑面积": "50000",
            "建筑密度": "40",
            "绿地率": "35",
            "容积率": "5.0"
        }
        
        return jsonify(project_info)
    
    except Exception as e:
        print(f"获取项目信息时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500