from flask import Blueprint, request, jsonify
from auth import get_db_connection, hash_password
from sqlalchemy import text
from loguru import logger

register_bp = Blueprint('register', __name__)

@register_bp.route('/api/validate-invite-code', methods=['POST'])
def validate_invite_code():
    """验证邀请码"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'valid': False, 'message': '请输入邀请码'}), 400
            
        # 检查邀请码是否有效
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id FROM invitation_codes WHERE code = :code AND is_used = 0"),
                {"code": code}
            ).fetchone()
            
            if not result:
                return jsonify({'valid': False, 'message': '无效的邀请码'}), 400
                
            return jsonify({'valid': True, 'message': '邀请码验证成功'}), 200
            
    except Exception as e:
        logger.error(f"邀请码验证失败: {str(e)}")
        return jsonify({'valid': False, 'message': '验证失败，请稍后重试'}), 500

@register_bp.route('/api/register', methods=['POST'])
def register():
    """用户注册处理"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        invitation_code = data.get('invitation_code')
        
        if not email or not password or not invitation_code:
            return jsonify({'success': False, 'message': '邮箱、密码和邀请码不能为空'}), 400
            
        # 检查邀请码是否有效
        engine = get_db_connection()
        with engine.connect() as conn:
            # 验证邀请码
            invite_result = conn.execute(
                text("SELECT id FROM invitation_codes WHERE code = :code AND is_used = 0"),
                {"code": invitation_code}
            ).fetchone()
            
            if not invite_result:
                return jsonify({'success': False, 'message': '无效的邀请码'}), 400
                
            # 检查邮箱是否已存在
            email_result = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if email_result:
                return jsonify({'success': False, 'message': '邮箱已被注册'}), 400
            
            # 创建新用户
            hashed_password = hash_password(password)
            conn.execute(
                text("""
                INSERT INTO users (email, password, created_at, updated_at)
                VALUES (:email, :password, GETDATE(), GETDATE())
                """),
                {
                    "email": email,
                    "password": hashed_password
                }
            )
            
            # 标记邀请码已使用
            conn.execute(
                text("UPDATE invitation_codes SET is_used = 1, used_at = GETDATE() WHERE code = :code"),
                {"code": invitation_code}
            )
            
            return jsonify({'success': True, 'message': '注册成功'}), 201
            
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'}), 500