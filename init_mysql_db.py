#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL数据库初始化脚本
此脚本用于创建MySQL数据库表结构
"""

import os
import logging
from sqlalchemy import create_engine
from app import app
from models import db

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('init_db.log')
    ]
)
logger = logging.getLogger(__name__)

def init_mysql_database():
    """初始化MySQL数据库结构"""
    try:
        logger.info("开始初始化MySQL数据库")
        
        # 获取应用上下文
        with app.app_context():
            # 创建所有表
            db.create_all()
            logger.info("数据库表创建成功")
            
            # 检查是否需要创建管理员用户
            from models import User
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = User()
                admin.username = 'admin'
                admin.email = 'admin@example.com'
                admin.set_password('admin123')
                admin.role = 'admin'
                db.session.add(admin)
                db.session.commit()
                logger.info("已创建默认管理员用户")
            
            logger.info("MySQL数据库初始化完成")
            return True
    except Exception as e:
        logger.error(f"初始化MySQL数据库时出错: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_mysql_database()
    if success:
        print("MySQL数据库初始化成功！")
    else:
        print("MySQL数据库初始化失败，请查看日志获取详细信息。")
        exit(1) 