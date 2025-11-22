"""
初始化数据脚本
"""
import logging
from core.database import db_manager
from core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


def init_default_data():
    """初始化默认数据"""
    try:
        session = db_manager.get_session()
        
        # 检查是否已存在默认管理员用户
        admin_user = session.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@ai-trading.com",
                hashed_password=get_password_hash("Admin123456"),
                is_active=True,
                is_superuser=True
            )
            session.add(admin_user)
            logger.info("创建默认管理员用户")
        
        # 创建默认测试用户
        test_user = session.query(User).filter(User.username == "testuser").first()
        
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@ai-trading.com",
                hashed_password=get_password_hash("Test123456"),
                is_active=True,
                is_superuser=False
            )
            session.add(test_user)
            logger.info("创建默认测试用户")
        
        session.commit()
        logger.info("默认数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化默认数据失败: {e}")
        session.rollback()
        raise


def init_user_settings():
    """初始化用户配置"""
    try:
        session = db_manager.get_session()
        
        # 创建用户配置表（如果不存在）
        session.execute("""
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
        """)
        
        # 为用户创建默认配置
        users = session.query(User).all()
        
        for user in users:
            # 检查是否已存在配置
            existing_setting = session.execute(
                "SELECT id FROM user_settings WHERE user_id = :user_id",
                {"user_id": user.id}
            ).fetchone()
            
            if not existing_setting:
                session.execute(
                    """
                    INSERT INTO user_settings (user_id, language, timezone, theme, notifications_enabled, risk_tolerance)
                    VALUES (:user_id, 'zh', 'Asia/Shanghai', 'dark', true, 'medium')
                    """,
                    {"user_id": user.id}
                )
                logger.info(f"为用户 {user.username} 创建默认配置")
        
        session.commit()
        logger.info("用户配置初始化完成")
        
    except Exception as e:
        logger.error(f"初始化用户配置失败: {e}")
        session.rollback()
        raise


def init_exchange_data():
    """初始化交易所数据"""
    try:
        session = db_manager.get_session()
        
        # 创建默认交易所配置
        exchanges = [
            {
                "name": "binance",
                "api_key": "",
                "api_secret": "",
                "is_active": True
            },
            {
                "name": "okx", 
                "api_key": "",
                "api_secret": "",
                "is_active": True
            },
            {
                "name": "bybit",
                "api_key": "",
                "api_secret": "",
                "is_active": True
            }
        ]
        
        for exchange_data in exchanges:
            existing_exchange = session.execute(
                "SELECT id FROM exchanges WHERE name = :name",
                {"name": exchange_data["name"]}
            ).fetchone()
            
            if not existing_exchange:
                session.execute(
                    """
                    INSERT INTO exchanges (name, api_key, api_secret, is_active)
                    VALUES (:name, :api_key, :api_secret, :is_active)
                    """,
                    exchange_data
                )
                logger.info(f"创建交易所配置: {exchange_data['name']}")
        
        session.commit()
        logger.info("交易所数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化交易所数据失败: {e}")
        session.rollback()
        raise


def init_strategy_data():
    """初始化策略数据"""
    try:
        session = db_manager.get_session()
        
        # 创建默认策略配置
        strategies = [
            {
                "name": "RSI策略",
                "description": "基于RSI指标的简单交易策略",
                "strategy_type": "technical",
                "parameters": {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "stop_loss": 0.05,
                    "take_profit": 0.1
                },
                "is_active": False
            },
            {
                "name": "移动平均线策略",
                "description": "基于移动平均线的趋势跟踪策略",
                "strategy_type": "technical",
                "parameters": {
                    "short_ma": 10,
                    "long_ma": 30,
                    "stop_loss": 0.03,
                    "take_profit": 0.08
                },
                "is_active": False
            },
            {
                "name": "机器学习策略",
                "description": "基于机器学习的预测交易策略",
                "strategy_type": "ml",
                "parameters": {
                    "model_type": "random_forest",
                    "features": ["price", "volume", "rsi", "macd"],
                    "confidence_threshold": 0.7
                },
                "is_active": False
            }
        ]
        
        for strategy_data in strategies:
            existing_strategy = session.execute(
                "SELECT id FROM strategies WHERE name = :name",
                {"name": strategy_data["name"]}
            ).fetchone()
            
            if not existing_strategy:
                session.execute(
                    """
                    INSERT INTO strategies (name, description, strategy_type, parameters, is_active)
                    VALUES (:name, :description, :strategy_type, :parameters, :is_active)
                    """,
                    strategy_data
                )
                logger.info(f"创建策略: {strategy_data['name']}")
        
        session.commit()
        logger.info("策略数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化策略数据失败: {e}")
        session.rollback()
        raise


def init_all_data():
    """初始化所有数据"""
    logger.info("开始初始化所有数据...")
    
    try:
        # 先运行数据库迁移
        from scripts.database_migration import run_all_migrations
        run_all_migrations()
        
        # 然后初始化数据
        init_default_data()
        init_user_settings()
        init_exchange_data()
        init_strategy_data()
        
        logger.info("所有数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化数据失败: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--users":
            init_default_data()
        elif sys.argv[1] == "--settings":
            init_user_settings()
        elif sys.argv[1] == "--exchanges":
            init_exchange_data()
        elif sys.argv[1] == "--strategies":
            init_strategy_data()
        else:
            print("用法: python init_data.py [--users|--settings|--exchanges|--strategies]")
    else:
        init_all_data()