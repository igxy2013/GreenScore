from flask import Blueprint, request, jsonify
from auth import get_db_connection, hash_password
from sqlalchemy import text
from loguru import logger

register_bp = Blueprint('register', __name__)

@register_bp.route('/api/register', methods=['POST'])
def register():
    """用户注册处理"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
            
        # 检查用户名是否已存在
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            
            if result:
                return jsonify({'error': '用户名已存在'}), 400
                
            # 检查邮箱是否已存在
            if email:
                result = conn.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": email}
                ).fetchone()
                
                if result:
                    return jsonify({'error': '邮箱已被注册'}), 400
            
            # 创建新用户
            hashed_password = hash_password(password)
            conn.execute(
                text("""
                INSERT INTO users (username, password, email, created_at, updated_at)
                VALUES (:username, :password, :email, GETDATE(), GETDATE())
                """),
                {
                    "username": username,
                    "password": hashed_password,
                    "email": email
                }
            )
            
            return jsonify({'message': '注册成功'}), 201
            
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        return jsonify({'error': '注册失败，请稍后重试'}), 500