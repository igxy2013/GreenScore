from app import app as application
from models import db
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    with application.app_context():
        try:
            # 初始化数据库
            db.create_all()
            logger.info("数据库表已创建")
            
            # 检查是否需要创建管理员用户
            from models import User
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = User()
                admin.email = 'admin@example.com'
                admin.set_password('admin123')
                admin.role = 'admin'
                db.session.add(admin)
                db.session.commit()
                logger.info("已创建默认管理员用户")
        except Exception as e:
            logger.error(f"初始化数据库时出错: {str(e)}")
            raise
    
    application.run(host='0.0.0.0', port=5000, debug=True)