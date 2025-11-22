#!/usr/bin/env python3
"""
数据库初始化脚本
负责创建数据库表结构和插入初始数据
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager, Base
from core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 创建所有表
        logger.info("创建数据库表...")
        db_manager.create_tables()
        
        # 执行SQL初始化脚本
        logger.info("执行SQL初始化脚本...")
        execute_sql_script()
        
        logger.info("数据库初始化完成!")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def execute_sql_script():
    """执行SQL初始化脚本"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # 读取SQL脚本
        sql_file = Path(__file__).parent / "init_database.sql"
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 连接数据库并执行脚本
        conn = psycopg2.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # 执行SQL脚本
        cursor.execute(sql_script)
        
        # 提交事务
        conn.commit()
        
        logger.info("SQL脚本执行完成")
        
    except Exception as e:
        logger.error(f"执行SQL脚本失败: {e}")
        raise


def drop_database():
    """删除数据库（仅用于测试）"""
    try:
        logger.warning("开始删除数据库...")
        
        db_manager = DatabaseManager()
        db_manager.drop_tables()
        
        logger.warning("数据库删除完成!")
        return True
        
    except Exception as e:
        logger.error(f"删除数据库失败: {e}")
        return False


def check_database_connection():
    """检查数据库连接"""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.name
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        
        logger.info(f"数据库连接成功: {result[0]}")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理脚本')
    parser.add_argument('--action', choices=['init', 'drop', 'check'], default='init', 
                       help='执行的操作: init(初始化), drop(删除), check(检查连接)')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        success = init_database()
        sys.exit(0 if success else 1)
    
    elif args.action == 'drop':
        success = drop_database()
        sys.exit(0 if success else 1)
    
    elif args.action == 'check':
        success = check_database_connection()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()