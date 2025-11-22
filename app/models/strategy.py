"""
策略模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from core.database import Base

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # 策略类型：ma_crossover, rsi, lstm等
    config = Column(JSON)  # 策略配置参数
    status = Column(String(20), default="inactive")  # 状态：active, inactive, paused
    performance = Column(JSON)  # 策略表现数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())