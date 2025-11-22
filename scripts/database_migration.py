"""
数据库迁移脚本
"""
import logging
from sqlalchemy import text
from core.database import db_manager
from core.config import settings

logger = logging.getLogger(__name__)


def create_migration_table():
    """创建迁移记录表"""
    try:
        session = db_manager.get_session()
        
        # 创建迁移记录表
        migration_table_sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        session.execute(text(migration_table_sql))
        session.commit()
        
        logger.info("迁移记录表创建成功")
        
    except Exception as e:
        logger.error(f"创建迁移记录表失败: {e}")
        raise


def check_migration_applied(migration_name: str) -> bool:
    """检查迁移是否已应用"""
    try:
        session = db_manager.get_session()
        
        result = session.execute(
            text("SELECT id FROM migrations WHERE name = :name"),
            {"name": migration_name}
        ).fetchone()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"检查迁移状态失败: {e}")
        return False


def mark_migration_applied(migration_name: str):
    """标记迁移已应用"""
    try:
        session = db_manager.get_session()
        
        session.execute(
            text("INSERT INTO migrations (name) VALUES (:name)"),
            {"name": migration_name}
        )
        session.commit()
        
        logger.info(f"迁移 {migration_name} 已标记为已应用")
        
    except Exception as e:
        logger.error(f"标记迁移失败: {e}")
        raise


def run_migration_001():
    """初始数据库迁移"""
    migration_name = "001_initial_schema"
    
    if check_migration_applied(migration_name):
        logger.info("初始迁移已应用，跳过")
        return
    
    try:
        session = db_manager.get_session()
        
        # 创建用户表
        users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        session.execute(text(users_table_sql))
        
        # 创建交易所表
        exchanges_table_sql = """
        CREATE TABLE IF NOT EXISTS exchanges (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            api_key VARCHAR(255) NOT NULL,
            api_secret VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        session.execute(text(exchanges_table_sql))
        
        # 创建账户表
        accounts_table_sql = """
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            exchange_id INTEGER NOT NULL,
            account_type VARCHAR(20) NOT NULL,
            balance DECIMAL(20, 8) DEFAULT 0.0,
            available_balance DECIMAL(20, 8) DEFAULT 0.0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (exchange_id) REFERENCES exchanges(id)
        )
        """
        session.execute(text(accounts_table_sql))
        
        # 创建策略表
        strategies_table_sql = """
        CREATE TABLE IF NOT EXISTS strategies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            strategy_type VARCHAR(50) NOT NULL,
            parameters JSONB,
            is_active BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        session.execute(text(strategies_table_sql))
        
        # 创建交易记录表
        trades_table_sql = """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL,
            strategy_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            price DECIMAL(20, 8) NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            fee DECIMAL(20, 8) DEFAULT 0.0,
            profit_loss DECIMAL(20, 8) DEFAULT 0.0,
            status VARCHAR(20) DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (strategy_id) REFERENCES strategies(id)
        )
        """
        session.execute(text(trades_table_sql))
        
        # 创建风险警报表
        risk_alerts_table_sql = """
        CREATE TABLE IF NOT EXISTS risk_alerts (
            id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            is_resolved BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        """
        session.execute(text(risk_alerts_table_sql))
        
        # 创建索引
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_exchange_id ON accounts(exchange_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_risk_alerts_account_id ON risk_alerts(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_risk_alerts_created_at ON risk_alerts(created_at)"
        ]
        
        for index_sql in indexes_sql:
            session.execute(text(index_sql))
        
        session.commit()
        mark_migration_applied(migration_name)
        logger.info("初始数据库迁移完成")
        
    except Exception as e:
        logger.error(f"初始迁移失败: {e}")
        session.rollback()
        raise


def run_migration_002():
    """添加用户配置表"""
    migration_name = "002_user_settings"
    
    if check_migration_applied(migration_name):
        logger.info("用户配置迁移已应用，跳过")
        return
    
    try:
        session = db_manager.get_session()
        
        # 创建用户配置表
        user_settings_sql = """
        CREATE TABLE IF NOT EXISTS user_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            language VARCHAR(10) DEFAULT 'zh',
            timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
            theme VARCHAR(20) DEFAULT 'dark',
            notifications_enabled BOOLEAN DEFAULT true,
            risk_tolerance VARCHAR(20) DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        session.execute(text(user_settings_sql))
        
        # 创建索引
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)"))
        
        session.commit()
        mark_migration_applied(migration_name)
        logger.info("用户配置迁移完成")
        
    except Exception as e:
        logger.error(f"用户配置迁移失败: {e}")
        session.rollback()
        raise


def run_migration_003():
    """添加API请求日志表"""
    migration_name = "003_api_logs"
    
    if check_migration_applied(migration_name):
        logger.info("API日志迁移已应用，跳过")
        return
    
    try:
        session = db_manager.get_session()
        
        # 创建API请求日志表
        api_logs_sql = """
        CREATE TABLE IF NOT EXISTS api_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            endpoint VARCHAR(255) NOT NULL,
            method VARCHAR(10) NOT NULL,
            status_code INTEGER,
            response_time INTEGER,
            user_agent TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        session.execute(text(api_logs_sql))
        
        # 创建索引
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint)"
        ]
        
        for index_sql in indexes_sql:
            session.execute(text(index_sql))
        
        session.commit()
        mark_migration_applied(migration_name)
        logger.info("API日志迁移完成")
        
    except Exception as e:
        logger.error(f"API日志迁移失败: {e}")
        session.rollback()
        raise


def run_all_migrations():
    """运行所有迁移"""
    logger.info("开始数据库迁移...")
    
    # 创建迁移记录表
    create_migration_table()
    
    # 按顺序运行迁移
    migrations = [
        run_migration_001,
        run_migration_002,
        run_migration_003
    ]
    
    for migration in migrations:
        try:
            migration()
        except Exception as e:
            logger.error(f"迁移执行失败: {e}")
            raise
    
    logger.info("所有数据库迁移完成")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--init":
            run_migration_001()
        elif sys.argv[1] == "--all":
            run_all_migrations()
        else:
            print("用法: python database_migration.py [--init|--all]")
    else:
        run_all_migrations()