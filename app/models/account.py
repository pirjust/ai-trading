"""
交易账户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from core.database import Base

class TradingAccount(Base):
    __tablename__ = "trading_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)  # 账户类型：spot, futures, options
    exchange = Column(String(50), nullable=False)  # 交易所：binance, okx等
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    status = Column(String(20), default="active")  # 状态：active, inactive, suspended
    total_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())