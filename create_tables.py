from app import db, app
import sqlalchemy as sa
from sqlalchemy import text

def create_tables():
    """创建所有数据库表"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")
        
        # 检查并添加standard列
        try:
            # 检查projects表是否存在standard列
            with db.engine.connect() as conn:
                # 检查列是否存在
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'standard'
                """))
                
                # 如果列不存在，添加它
                if result.scalar() == 0:
                    print("添加standard列到projects表...")
                    conn.execute(text("""
                        ALTER TABLE projects 
                        ADD standard NVARCHAR(20)
                    """))
                    # 在SQLAlchemy 1.4中，需要使用事务来提交更改
                    # conn.commit() 不再可用
                    print("standard列添加成功！")
                else:
                    print("standard列已存在，无需添加。")
                    
                # 检查projects表是否存在public_building_type列
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'public_building_type'
                """))
                
                # 如果列不存在，添加它
                if result.scalar() == 0:
                    print("添加public_building_type列到projects表...")
                    conn.execute(text("""
                        ALTER TABLE projects 
                        ADD public_building_type NVARCHAR(50)
                    """))
                    print("public_building_type列添加成功！")
                else:
                    print("public_building_type列已存在，无需添加。")
        except Exception as e:
            print(f"检查或添加列时出错: {str(e)}")

if __name__ == "__main__":
    create_tables() 