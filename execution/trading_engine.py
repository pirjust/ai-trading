"""
交易引擎核心模块
"""
import asyncio
from typing import Dict, List, Optional
import ccxt
from sqlalchemy.orm import Session

from core.database import get_db
from config.exchanges import ExchangeConfig
from config.trading_config import TradingConfig
from risk_management.risk_engine import RiskEngine

class TradingEngine:
    """交易引擎"""
    
    def __init__(self):
        self.exchange_config = ExchangeConfig()
        self.trading_config = TradingConfig()
        self.risk_engine = RiskEngine()
        self.active_exchanges: Dict[str, ccxt.Exchange] = {}
        
    async def initialize(self):
        """初始化交易引擎"""
        # 初始化交易所连接
        for exchange_name, config in self.exchange_config.exchanges.items():
            if config['enabled']:
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'apiKey': config['api_key'],
                    'secret': config['api_secret'],
                    'sandbox': config['sandbox'],
                    'enableRateLimit': True
                })
                self.active_exchanges[exchange_name] = exchange
        
        # 初始化风险引擎
        await self.risk_engine.initialize()
    
    async def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        exchange: str = "binance",
        account_id: int = None
    ) -> Dict:
        """执行交易"""
        
        # 风险检查
        risk_check = await self.risk_engine.check_trade_risk(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            account_id=account_id
        )
        
        if not risk_check["allowed"]:
            raise Exception(f"交易被风险控制阻止: {risk_check['reason']}")
        
        # 获取交易所实例
        exchange_instance = self.active_exchanges.get(exchange)
        if not exchange_instance:
            raise Exception(f"交易所 {exchange} 未配置或未启用")
        
        try:
            # 执行交易
            if order_type == "market":
                order = await exchange_instance.create_market_order(
                    symbol, side, quantity
                )
            elif order_type == "limit":
                if not price:
                    raise Exception("限价单需要指定价格")
                order = await exchange_instance.create_limit_order(
                    symbol, side, quantity, price
                )
            else:
                raise Exception(f"不支持的订单类型: {order_type}")
            
            # 记录交易
            await self._record_trade(order, account_id, exchange)
            
            return {
                "success": True,
                "order_id": order['id'],
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": order.get('price'),
                "status": order['status']
            }
            
        except Exception as e:
            # 记录交易失败
            await self._record_failed_trade(
                symbol, side, quantity, order_type, price, str(e), account_id, exchange
            )
            raise Exception(f"交易执行失败: {str(e)}")
    
    async def get_positions(self, exchange: str = "binance") -> List[Dict]:
        """获取持仓信息"""
        exchange_instance = self.active_exchanges.get(exchange)
        if not exchange_instance:
            raise Exception(f"交易所 {exchange} 未配置")
        
        try:
            # 获取持仓
            positions = await exchange_instance.fetch_positions()
            return positions
        except Exception as e:
            raise Exception(f"获取持仓失败: {str(e)}")
    
    async def get_account_balance(self, exchange: str = "binance") -> Dict:
        """获取账户余额"""
        exchange_instance = self.active_exchanges.get(exchange)
        if not exchange_instance:
            raise Exception(f"交易所 {exchange} 未配置")
        
        try:
            balance = await exchange_instance.fetch_balance()
            return {
                "total": balance['total'],
                "free": balance['free'],
                "used": balance['used']
            }
        except Exception as e:
            raise Exception(f"获取余额失败: {str(e)}")
    
    async def _record_trade(self, order: Dict, account_id: int, exchange: str):
        """记录交易到数据库"""
        # 这里应该将交易记录保存到数据库
        pass
    
    async def _record_failed_trade(
        self, symbol: str, side: str, quantity: float, 
        order_type: str, price: Optional[float], 
        error: str, account_id: int, exchange: str
    ):
        """记录失败交易"""
        # 记录失败交易到数据库
        pass