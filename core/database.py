"""
数据库管理模块
负责数据库连接、会话管理和数据库操作
"""

import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import settings

logger = logging.getLogger(__name__)

# 数据库基础配置
Base = declarative_base()
metadata = MetaData()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.session_local = None
        self._setup_database()
    
    def _setup_database(self):
        """设置数据库连接"""
        try:
            # 创建数据库引擎
            self.engine = create_engine(
                settings.database.url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,
                echo=settings.debug
            )
            
            # 创建会话工厂
            self.session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("数据库连接配置完成")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if not self.session_local:
            self._setup_database()
        
        session = self.session_local()
        try:
            return session
        except Exception as e:
            session.close()
            raise e
    
    def get_session_generator(self):
        """获取数据库会话生成器（用于依赖注入）"""
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()
    
    def create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除数据库表（仅用于测试）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除完成")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db():
    """依赖注入：获取数据库会话生成器"""
    return db_manager.get_session_generator()


def init_database():
    """初始化数据库"""
    db_manager.create_tables()
    
    # 插入初始数据
    from scripts.init_data import init_default_data
    init_default_data()


# 导入完整的数据库模型
from app.models.database_models import (
    User, Exchange, Account, Balance, Symbol, KlineData, 
    Strategy, Backtest, BacktestTrade, Position, Trade, 
    TradeSignal, RiskAlert, SystemLog, PerformanceMetric
)


if __name__ == "__main__":
    # 数据库测试
    db_manager = DatabaseManager()
    db_manager.create_tables()
    print("数据库初始化完成")