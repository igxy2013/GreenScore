from app import db, User
import logging
import traceback
from sqlalchemy import text

def create_users_table():
    """创建用户表"""
    try:
        print("开始创建用户表...")
        
        # 检查表是否已存在
        inspector = db.inspect(db.engine)
        if 'users' in inspector.get_table_names():
            print("用户表已存在，跳过创建")
            return True
            
        # 创建用户表
        db.create_all()
        
        # 检查并添加password_hash字段
        with db.engine.begin() as conn:
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM sys.columns 
                    WHERE object_id = OBJECT_ID('users') 
                    AND name = 'password_hash'
                )
                BEGIN
                    ALTER TABLE users
                    ADD password_hash VARCHAR(256) NOT NULL
                END
            """))
        print("用户表创建成功！")
        return True
        
    except Exception as e:
        print(f"创建用户表时出错: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建用户表
    success = create_users_table()
    if success:
        print("用户表创建/检查完成")
    else:
        print("用户表创建失败")