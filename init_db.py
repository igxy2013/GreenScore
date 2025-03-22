from app import app, db
from models import User, InvitationCode
from datetime import datetime
from sqlalchemy import text

def init_db():
    with app.app_context():
        try:
            # 创建用户表和邀请码表
            User.__table__.create(db.engine, checkfirst=True)
            InvitationCode.__table__.create(db.engine, checkfirst=True)
            
            # 检查是否已存在管理员用户
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                # 创建管理员用户
                admin = User(
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password('admin123456')
                db.session.add(admin)
                db.session.flush()  # 获取admin的ID
                
                # 创建初始邀请码
                invite = InvitationCode(
                    code='INIT2024',
                    max_usage=100,
                    created_at=datetime.utcnow()
                )
                db.session.add(invite)
                
                db.session.commit()
                print("数据库初始化成功！")
                print("管理员账号：admin@example.com")
                print("管理员密码：admin123456")
                print("初始邀请码：INIT2024")
            else:
                print("管理员账号已存在")
            
        except Exception as e:
            db.session.rollback()
            print(f"数据库初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_db() 