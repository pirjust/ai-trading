"""
数据库模型定义
使用SQLAlchemy ORM定义所有数据库表结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    accounts = relationship("Account", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")


class Exchange(Base):
    """交易所表"""
    __tablename__ = "exchanges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    passphrase = Column(String(255))  # 某些交易所需要
    sandbox = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=1200)  # 每分钟请求限制
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    accounts = relationship("Account", back_populates="exchange")
    
    __table_args__ = (
        Index('idx_exchange_name_active', 'name', 'is_active'),
    )


class Account(Base):
    """账户表"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    account_type = Column(String(20), nullable=False, index=True)  # spot, futures, option, margin
    account_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="accounts")
    exchange = relationship("Exchange", back_populates="accounts")
    balances = relationship("Balance", back_populates="account")
    positions = relationship("Position", back_populates="account")
    trades = relationship("Trade", back_populates="account")
    
    __table_args__ = (
        Index('idx_account_user_exchange', 'user_id', 'exchange_id'),
        Index('idx_account_type_active', 'account_type', 'is_active'),
    )


class Balance(Base):
    """余额表"""
    __tablename__ = "balances"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    asset = Column(String(20), nullable=False, index=True)
    free = Column(Float, nullable=False, default=0.0)
    locked = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    account = relationship("Account", back_populates="balances")
    
    __table_args__ = (
        Index('idx_balance_account_asset', 'account_id', 'asset'),
    )


class Symbol(Base):
    """交易对表"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    base_asset = Column(String(20), nullable=False)
    quote_asset = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    min_quantity = Column(Float, nullable=False, default=0.001)
    max_quantity = Column(Float, nullable=False)
    step_size = Column(Float, nullable=False, default=0.001)
    min_price = Column(Float, nullable=False, default=0.01)
    max_price = Column(Float, nullable=False)
    tick_size = Column(Float, nullable=False, default=0.01)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    exchange = relationship("Exchange")
    klines = relationship("KlineData", back_populates="symbol")
    positions = relationship("Position", back_populates="symbol_trading")
    trades = relationship("Trade", back_populates="symbol_trading")
    
    __table_args__ = (
        Index('idx_symbol_exchange_symbol', 'exchange_id', 'symbol'),
    )


class KlineData(Base):
    """K线数据表"""
    __tablename__ = "kline_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    interval = Column(String(10), nullable=False, index=True)  # 1m, 5m, 15m, 30m, 1h, 4h, 1d
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=False, default=0.0)
    trades_count = Column(Integer, default=0)
    taker_buy_volume = Column(Float, nullable=False, default=0.0)
    taker_buy_quote_volume = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    symbol = relationship("Symbol", back_populates="klines")
    
    __table_args__ = (
        Index('idx_kline_symbol_interval_time', 'symbol_id', 'interval', 'timestamp'),
        Index('idx_kline_timestamp', 'timestamp'),
    )


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False, index=True)  # technical, ml, rl
    strategy_class = Column(String(100), nullable=False)  # 具体的策略类名
    parameters = Column(JSON)  # 策略参数
    symbols = Column(JSON)  # 交易对列表
    timeframes = Column(JSON)  # 时间周期列表
    risk_settings = Column(JSON)  # 风险设置
    is_active = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy")
    trade_signals = relationship("TradeSignal", back_populates="strategy")
    
    __table_args__ = (
        Index('idx_strategy_user_active', 'user_id', 'is_active'),
        Index('idx_strategy_type', 'strategy_type'),
    )


class Backtest(Base):
    """回测表"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    initial_balance = Column(Float, nullable=False)
    final_balance = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    avg_win = Column(Float, nullable=False)
    avg_loss = Column(Float, nullable=False)
    parameters = Column(JSON)  # 回测参数
    status = Column(String(20), default="running", index=True)  # running, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")
    backtest_trades = relationship("BacktestTrade", back_populates="backtest")
    
    __table_args__ = (
        Index('idx_backtest_strategy_symbol', 'strategy_id', 'symbol'),
        Index('idx_backtest_status', 'status'),
    )


class BacktestTrade(Base):
    """回测交易记录表"""
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), nullable=False)  # market, limit
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False, default=0.0)
    profit_loss = Column(Float, nullable=False, default=0.0)
    balance = Column(Float, nullable=False)  # 交易后余额
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    strategy = Column(String(100), nullable=False)
    
    # 关系
    backtest = relationship("Backtest", back_populates="backtest_trades")
    
    __table_args__ = (
        Index('idx_backtest_trade_backtest', 'backtest_id'),
        Index('idx_backtest_trade_time', 'entry_time'),
    )


class Position(Base):
    """持仓表"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    side = Column(String(10), nullable=False, index=True)  # long, short
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    margin = Column(Float, nullable=False, default=0.0)
    leverage = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, default=True, index=True)
    opened_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    account = relationship("Account", back_populates="positions")
    symbol_trading = relationship("Symbol", back_populates="positions")
    
    __table_args__ = (
        Index('idx_position_account_symbol', 'account_id', 'symbol_id'),
        Index('idx_position_active', 'is_active'),
    )


class Trade(Base):
    """实际交易记录表"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    exchange_order_id = Column(String(100), nullable=False, index=True)
    client_order_id = Column(String(100), nullable=False)
    side = Column(String(10), nullable=False, index=True)
    order_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    executed_quantity = Column(Float, nullable=False)
    executed_price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False, default=0.0)
    fee_asset = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # pending, filled, cancelled, failed
    executed_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    account = relationship("Account", back_populates="trades")
    symbol_trading = relationship("Symbol", back_populates="trades")
    strategy = relationship("Strategy")
    
    __table_args__ = (
        Index('idx_trade_account_symbol', 'account_id', 'symbol_id'),
        Index('idx_trade_status_time', 'status', 'executed_at'),
        Index('idx_trade_exchange_order', 'exchange_order_id'),
    )


class TradeSignal(Base):
    """交易信号表"""
    __tablename__ = "trade_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False, index=True)  # buy, sell, close
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    strength = Column(Float, nullable=False)
    parameters = Column(JSON)  # 信号参数
    is_executed = Column(Boolean, default=False, index=True)
    executed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    strategy = relationship("Strategy", back_populates="trade_signals")
    
    __table_args__ = (
        Index('idx_signal_strategy_symbol', 'strategy_id', 'symbol'),
        Index('idx_signal_type_executed', 'signal_type', 'is_executed'),
    )


class RiskAlert(Base):
    """风险警报表"""
    __tablename__ = "risk_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)  # 警报详细信息
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User")
    account = relationship("Account")
    
    __table_args__ = (
        Index('idx_alert_user_severity', 'user_id', 'severity'),
        Index('idx_alert_resolved', 'is_resolved', 'created_at'),
    )


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger_name = Column(String(100), nullable=False)
    module = Column(String(100), nullable=False)
    function = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_log_level_time', 'level', 'created_at'),
        Index('idx_log_module_time', 'module', 'created_at'),
    )


class PerformanceMetric(Base):
    """性能指标表"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # gauge, counter, histogram
    value = Column(Float, nullable=False)
    labels = Column(JSON)  # 标签
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_metric_name_time', 'metric_name', 'timestamp'),
        Index('idx_metric_time', 'timestamp'),
    )


# 数据库初始化函数
def create_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")


def drop_tables(engine):
    """删除所有表（仅用于测试）"""
    Base.metadata.drop_all(bind=engine)
    print("数据库表删除完成")


# 数据库模型验证
def validate_models():
    """验证数据库模型"""
    model_info = []
    
    for name, cls in Base.registry._class_registry.items():
        if hasattr(cls, '__tablename__'):
            columns = []
            for column in cls.__table__.columns:
                columns.append(f"{column.name}: {column.type}")
            
            model_info.append({
                'table': cls.__tablename__,
                'class': name,
                'columns': columns
            })
    
    return model_info


if __name__ == "__main__":
    # 模型验证
    models_info = validate_models()
    print("=== 数据库模型信息 ===")
    for model in models_info:
        print(f"\n表: {model['table']} (类: {model['class']})")
        for column in model['columns']:
            print(f"  {column}")