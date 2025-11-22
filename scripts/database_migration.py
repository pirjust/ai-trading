#!/usr/bin/env python3
"""
AI量化交易系统数据库迁移脚本
支持数据库版本管理和迁移
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """数据库迁移管理类"""
    
    def __init__(self, db_url: str = None):
        """初始化数据库连接"""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("数据库连接URL未配置")
        
        self.conn = None
        self.migrations_table = "schema_migrations"
        
    def connect(self):
        """连接到数据库"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def ensure_migrations_table(self):
        """确保迁移表存在"""
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    version VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logger.info("迁移表检查完成")
    
    def get_applied_migrations(self) -> List[str]:
        """获取已应用的迁移版本"""
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT version FROM {self.migrations_table} ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]
    
    def apply_migration(self, version: str, name: str, sql: str):
        """应用单个迁移"""
        try:
            with self.conn.cursor() as cursor:
                # 执行迁移SQL
                cursor.execute(sql)
                
                # 记录迁移历史
                cursor.execute(f"""
                    INSERT INTO {self.migrations_table} (version, name)
                    VALUES (%s, %s)
                """, (version, name))
                
                self.conn.commit()
                logger.info(f"✅ 迁移 {version} - {name} 应用成功")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 迁移 {version} - {name} 应用失败: {e}")
            raise
    
    def get_pending_migrations(self) -> Dict[str, str]:
        """获取待处理的迁移文件"""
        migrations_dir = "scripts/migrations"
        if not os.path.exists(migrations_dir):
            return {}
        
        migrations = {}
        for filename in sorted(os.listdir(migrations_dir)):
            if filename.endswith('.sql') and '_' in filename:
                # 版本格式: YYYYMMDDHHMMSS_name.sql
                version = filename.split('_')[0]
                name = '_'.join(filename.split('_')[1:]).replace('.sql', '')
                
                with open(os.path.join(migrations_dir, filename), 'r', encoding='utf-8') as f:
                    migrations[version] = {
                        'name': name,
                        'sql': f.read()
                    }
        
        return migrations
    
    def migrate(self, target_version: str = None):
        """执行数据库迁移"""
        logger.info("开始数据库迁移...")
        
        # 确保迁移表存在
        self.ensure_migrations_table()
        
        # 获取已应用的迁移
        applied_migrations = set(self.get_applied_migrations())
        
        # 获取所有迁移文件
        all_migrations = self.get_pending_migrations()
        
        # 确定需要应用的迁移
        pending_migrations = {}
        for version, migration in all_migrations.items():
            if version not in applied_migrations:
                if target_version and version > target_version:
                    continue
                pending_migrations[version] = migration
        
        if not pending_migrations:
            logger.info("没有需要应用的迁移")
            return
        
        logger.info(f"发现 {len(pending_migrations)} 个待应用的迁移")
        
        # 按版本顺序应用迁移
        for version in sorted(pending_migrations.keys()):
            migration = pending_migrations[version]
            self.apply_migration(version, migration['name'], migration['sql'])
        
        logger.info("✅ 数据库迁移完成")
    
    def rollback(self, target_version: str):
        """回滚到指定版本"""
        logger.info(f"开始回滚到版本 {target_version}...")
        
        # 获取已应用的迁移
        applied_migrations = self.get_applied_migrations()
        
        # 需要回滚的迁移（按逆序）
        migrations_to_rollback = [v for v in applied_migrations if v > target_version]
        
        if not migrations_to_rollback:
            logger.info("没有需要回滚的迁移")
            return
        
        logger.info(f"发现 {len(migrations_to_rollback)} 个需要回滚的迁移")
        
        # 按逆序回滚（最新先回滚）
        for version in reversed(migrations_to_rollback):
            # 这里需要实现具体的回滚逻辑
            # 通常需要为每个迁移创建对应的回滚SQL文件
            logger.warning(f"回滚迁移 {version} - 回滚功能待实现")
        
        logger.info("⚠️ 回滚完成（部分功能可能需要手动处理）")
    
    def status(self):
        """显示迁移状态"""
        logger.info("检查迁移状态...")
        
        # 获取已应用的迁移
        applied_migrations = self.get_applied_migrations()
        
        # 获取所有迁移文件
        all_migrations = self.get_pending_migrations()
        
        logger.info("迁移状态报告:")
        logger.info(f"已应用的迁移: {len(applied_migrations)}")
        logger.info(f"待处理的迁移: {len(all_migrations) - len(applied_migrations)}")
        
        for version in sorted(all_migrations.keys()):
            status = "✅ 已应用" if version in applied_migrations else "⏳ 待处理"
            name = all_migrations[version]['name']
            logger.info(f"  {version} - {name} - {status}")
    
    def create_migration(self, name: str):
        """创建新的迁移文件"""
        # 生成时间戳版本号
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version = f"{timestamp}"
        
        # 创建迁移文件
        filename = f"{version}_{name}.sql"
        filepath = os.path.join("scripts/migrations", filename)
        
        # 确保目录存在
        os.makedirs("scripts/migrations", exist_ok=True)
        
        # 创建迁移模板
        template = f"""-- 迁移: {name}
-- 版本: {version}
-- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- 迁移SQL语句
-- 请在此处编写数据库变更语句

-- 示例:
-- CREATE TABLE new_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 请确保SQL语句是幂等的（可以重复执行）
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        logger.info(f"✅ 迁移文件已创建: {filepath}")
        return filepath

# 命令行接口
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI量化交易系统数据库迁移工具')
    parser.add_argument('command', choices=['migrate', 'rollback', 'status', 'create'], 
                        help='迁移命令')
    parser.add_argument('--target', help='目标版本（用于rollback）')
    parser.add_argument('--name', help='迁移名称（用于create）')
    parser.add_argument('--db-url', help='数据库连接URL')
    
    args = parser.parse_args()
    
    try:
        migration = DatabaseMigration(args.db_url)
        
        with migration:
            if args.command == 'migrate':
                migration.migrate(args.target)
            elif args.command == 'rollback':
                if not args.target:
                    logger.error("回滚操作需要指定目标版本")
                    sys.exit(1)
                migration.rollback(args.target)
            elif args.command == 'status':
                migration.status()
            elif args.command == 'create':
                if not args.name:
                    logger.error("创建迁移需要指定名称")
                    sys.exit(1)
                migration.create_migration(args.name)
    
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()