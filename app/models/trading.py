"""
交易订单模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.sql import func
from core.database import Base

class TradeOrder(Base):
    __tablename__ = "trade_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)  # 交易对：BTCUSDT, ETHUSDT等
    side = Column(String(10), nullable=False)  # 方向：buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    order_type = Column(String(20), default="market")  # 订单类型：market, limit, stop
    status = Column(String(20), default="pending")  # 状态：pending, executed, canceled, failed
    exchange_order_id = Column(String(100))  # 交易所订单ID
    account_id = Column(Integer, nullable=False)  # 关联的交易账户
    strategy_id = Column(Integer)  # 关联的策略ID
    metadata = Column(JSON)  # 订单元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())