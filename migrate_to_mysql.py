#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQL Server到MySQL数据迁移脚本
此脚本用于将SQL Server数据库中的数据迁移到MySQL数据库
"""

import os
import sys
import logging
import urllib.parse
from sqlalchemy import create_engine, text
import pandas as pd
import pyodbc
import pymysql

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

def get_sqlserver_connection():
    """获取SQL Server数据库连接"""
    try:
        # SQL Server连接配置
        server = os.environ.get('SQLSERVER_SERVER', 'aibim.xyz')
        database = os.environ.get('SQLSERVER_DATABASE', '绿色建筑')
        username = os.environ.get('SQLSERVER_USERNAME', 'test')
        password = os.environ.get('SQLSERVER_PASSWORD', '123456')
        driver = os.environ.get('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        
        # 使用pyodbc直接创建连接，而不是SQLAlchemy
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        conn = pyodbc.connect(conn_str)
        logger.info("SQL Server连接成功")
        return conn
    except Exception as e:
        logger.error(f"SQL Server连接失败: {str(e)}")
        raise

def get_mysql_connection():
    """获取MySQL数据库连接"""
    try:
        # 从配置文件获取MySQL数据库连接参数
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
        mysql_database = os.environ.get('MYSQL_DATABASE', '绿色建筑')
        mysql_username = os.environ.get('MYSQL_USERNAME', 'mysql')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '12345678')
        
        # 使用pymysql直接创建连接
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_username,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4'
        )
        
        # 测试连接
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            logger.info("MySQL连接测试成功")
        
        return conn
    except Exception as e:
        logger.error(f"MySQL连接失败: {str(e)}")
        raise

def get_tables(conn):
    """获取数据库中的所有表"""
    try:
        cursor = conn.cursor()
        # SQL Server查询
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
                
        logger.info(f"获取到{len(tables)}个表")
        return tables
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        raise

def migrate_table(source_conn, target_conn, table_name):
    """迁移单个表的数据"""
    try:
        logger.info(f"开始迁移表: {table_name}")
        
        # 构建查询语句，使用方括号包围表名以支持特殊字符（SQL Server语法）
        query = f"SELECT * FROM [{table_name}]"
        
        # 使用pandas从pyodbc连接读取数据
        df = pd.read_sql(query, source_conn)
        row_count = len(df)
        logger.info(f"表 {table_name} 读取了 {row_count} 条记录")
        
        if row_count > 0:
            # 处理中文列名，防止在MySQL中出现问题
            df.columns = [col if isinstance(col, str) else str(col) for col in df.columns]
            
            # 创建MySQL游标
            mysql_cursor = target_conn.cursor()
            
            try:
                # 删除现有表（如果存在），使用MySQL语法
                mysql_cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                
                # 根据DataFrame构建创建表SQL
                create_table_sql = get_create_table_sql(df, table_name)
                mysql_cursor.execute(create_table_sql)
                
                # 批量插入数据
                insert_data_sql_list = get_insert_data_sql(df, table_name)
                for sql in insert_data_sql_list:
                    mysql_cursor.execute(sql)
                
                # 提交事务
                target_conn.commit()
                logger.info(f"表 {table_name} 迁移完成")
            except Exception as e:
                # 回滚事务
                target_conn.rollback()
                logger.error(f"写入MySQL失败: {str(e)}")
                raise
            finally:
                # 关闭游标
                mysql_cursor.close()
        else:
            logger.warning(f"表 {table_name} 没有数据，跳过")
        
        return row_count
    except Exception as e:
        logger.error(f"迁移表 {table_name} 时出错: {str(e)}")
        raise

def get_create_table_sql(df, table_name):
    """根据DataFrame生成创建表的SQL语句"""
    columns = []
    for col in df.columns:
        # 根据DataFrame的数据类型确定SQL列类型
        dtype = df[col].dtype
        if 'int' in str(dtype):
            col_type = 'INT'
        elif 'float' in str(dtype):
            col_type = 'FLOAT'
        elif 'datetime' in str(dtype):
            col_type = 'DATETIME'
        else:
            # 默认使用TEXT，确保能存储各种类型的数据
            col_type = 'TEXT'
        
        # 转义列名
        escaped_col = f"`{col}`"
        columns.append(f"{escaped_col} {col_type}")
    
    # 生成创建表的SQL（MySQL语法）
    create_sql = f"CREATE TABLE `{table_name}` ({', '.join(columns)})"
    return create_sql

def get_insert_data_sql(df, table_name, batch_size=100):
    """根据DataFrame生成插入数据的SQL语句，分批处理"""
    if len(df) == 0:
        return []
    
    result = []
    # 分批处理，避免生成过大的SQL语句
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        # 为每一批次生成INSERT语句
        columns = [f"`{col}`" for col in batch.columns]
        values_list = []
        
        for _, row in batch.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append('NULL')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    # 转义字符串值
                    val_str = str(val).replace("'", "''")
                    values.append(f"'{val_str}'")
            
            values_list.append(f"({', '.join(values)})")
        
        # 生成完整的INSERT语句（MySQL语法）
        insert_sql = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES {', '.join(values_list)}"
        result.append(insert_sql)
    
    return result

def main():
    """主函数"""
    try:
        logger.info("开始数据迁移")
        
        # 获取数据库连接
        source_conn = get_sqlserver_connection()
        target_conn = get_mysql_connection()
        
        # 获取所有表
        tables = get_tables(source_conn)
        
        # 总表数和迁移成功的表数
        total_tables = len(tables)
        successful_tables = 0
        total_rows = 0
        
        # 迁移每个表
        for table in tables:
            try:
                rows = migrate_table(source_conn, target_conn, table)
                total_rows += rows
                successful_tables += 1
            except Exception as e:
                logger.error(f"表 {table} 迁移失败: {str(e)}")
        
        # 关闭连接
        source_conn.close()
        target_conn.close()
        
        # 迁移统计
        logger.info(f"数据迁移完成，总计 {total_tables} 个表，成功 {successful_tables} 个，共迁移 {total_rows} 条记录")
        
        if successful_tables < total_tables:
            logger.warning(f"有 {total_tables - successful_tables} 个表迁移失败")
        
        return 0
    except Exception as e:
        logger.error(f"数据迁移过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())