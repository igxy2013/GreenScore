from functools import wraps
from flask import Blueprint, request, jsonify, session
from models import db, Project, User
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """管理员权限检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/api/projects/<int:project_id>', methods=['PUT'])
@admin_required
def update_project(project_id):
    """管理员更新项目"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404

        data = request.get_json()
        project.name = data.get('name', project.name)
        project.user_id = data.get('user_id', project.user_id)
        project.status = data.get('status', project.status)
        
        if 'total_score' in data:
            project.total_score = data['total_score']

        db.session.commit()
        return jsonify({'success': True, 'message': '项目更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/api/projects/<int:project_id>', methods=['DELETE'])
@admin_required
def delete_project(project_id):
    """管理员删除项目"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404

        # 删除项目相关的得分记录
        db.session.execute(
            text("DELETE FROM `得分表` WHERE `项目ID` = :project_id"),
            {"project_id": project_id}
        )

        # 删除项目
        db.session.delete(project)
        db.session.commit()
        return jsonify({'success': True, 'message': '项目删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/api/projects', methods=['POST'])
@admin_required
def create_project():
    """管理员创建项目"""
    try:
        data = request.get_json()
        project = Project(
            name=data['name'],
            user_id=data['user_id'],
            status=data.get('status', 'pending')
        )
        if 'total_score' in data:
            project.total_score = data['total_score']

        db.session.add(project)
        db.session.commit()
        return jsonify({'success': True, 'message': '项目创建成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 