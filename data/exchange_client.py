"""
交易所客户端统一接口
提供统一的交易所API调用接口，支持币安、欧意等主流交易所
"""

from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
import asyncio
import logging
from enum import Enum

from .binance_api import BinanceAPI
from .okx_api import OKXAPI
from config.exchanges import EXCHANGE_CONFIG

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """交易所类型"""
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"
    COINBASE = "coinbase"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"


class UnifiedTicker:
    """统一行情数据结构"""
    
    def __init__(self, data: Dict[str, Any]):
        self.symbol = data.get('symbol', '')
        self.price = float(data.get('price', 0))
        self.volume = float(data.get('volume', 0))
        self.price_change = float(data.get('price_change', 0))
        self.price_change_percent = float(data.get('price_change_percent', 0))
        self.high = float(data.get('high', 0))
        self.low = float(data.get('low', 0))
        self.open = float(data.get('open', 0))
        self.timestamp = data.get('timestamp', 0)


class UnifiedOrder:
    """统一订单数据结构"""
    
    def __init__(self, data: Dict[str, Any]):
        self.order_id = data.get('order_id', '')
        self.symbol = data.get('symbol', '')
        self.side = data.get('side', '')
        self.order_type = data.get('order_type', '')
        self.quantity = float(data.get('quantity', 0))
        self.price = float(data.get('price', 0))
        self.status = data.get('status', '')
        self.filled_quantity = float(data.get('filled_quantity', 0))
        self.avg_price = float(data.get('avg_price', 0))
        self.create_time = data.get('create_time', 0)
        self.update_time = data.get('update_time', 0)


class UnifiedPosition:
    """统一持仓数据结构"""
    
    def __init__(self, data: Dict[str, Any]):
        self.symbol = data.get('symbol', '')
        self.side = data.get('side', '')
        self.quantity = float(data.get('quantity', 0))
        self.avg_price = float(data.get('avg_price', 0))
        self.mark_price = float(data.get('mark_price', 0))
        self.unrealized_pnl = float(data.get('unrealized_pnl', 0))
        self.leverage = int(data.get('leverage', 1))


class UnifiedBalance:
    """统一余额数据结构"""
    
    def __init__(self, data: Dict[str, Any]):
        self.asset = data.get('asset', '')
        self.free = float(data.get('free', 0))
        self.locked = float(data.get('locked', 0))
        self.total = self.free + self.locked


class BaseExchangeClient(ABC):
    """交易所客户端基类"""
    
    def __init__(self, exchange_type: ExchangeType, sandbox: bool = False):
        self.exchange_type = exchange_type
        self.sandbox = sandbox
        self.is_connected = False
    
    @abstractmethod
    async def connect(self):
        """连接交易所"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> UnifiedTicker:
        """获取行情"""
        pass
    
    @abstractmethod
    async def get_tickers(self) -> List[UnifiedTicker]:
        """获取所有行情"""
        pass
    
    @abstractmethod
    async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取深度数据"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, 
                        limit: int = 1000) -> List[List[Any]]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> List[UnifiedBalance]:
        """获取余额"""
        pass
    
    @abstractmethod
    async def create_order(self, symbol: str, side: OrderSide, 
                          order_type: OrderType, quantity: float,
                          price: float = None) -> UnifiedOrder:
        """创建订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str) -> UnifiedOrder:
        """获取订单信息"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> List[UnifiedOrder]:
        """获取当前挂单"""
        pass
    
    @abstractmethod
    async def get_positions(self, symbol: str = None) -> List[UnifiedPosition]:
        """获取持仓"""
        pass
    
    @abstractmethod
    async def test_connectivity(self) -> bool:
        """测试连接性"""
        pass


class BinanceClient(BaseExchangeClient):
    """币安客户端"""
    
    def __init__(self, sandbox: bool = False):
        super().__init__(ExchangeType.BINANCE, sandbox)
        self.api = None
    
    async def connect(self):
        """连接币安"""
        try:
            self.api = BinanceAPI(sandbox=self.sandbox)
            await self.api.__aenter__()
            
            if await self.test_connectivity():
                self.is_connected = True
                logger.info("币安客户端连接成功")
            else:
                raise Exception("币安连接测试失败")
                
        except Exception as e:
            logger.error(f"币安客户端连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self.api:
            await self.api.__aexit__(None, None, None)
            self.is_connected = False
            logger.info("币安客户端已断开连接")
    
    async def get_ticker(self, symbol: str) -> UnifiedTicker:
        """获取币安行情"""
        data = await self.api.get_ticker(symbol)
        return UnifiedTicker({
            'symbol': symbol,
            'price': float(data['lastPrice']),
            'volume': float(data['volume']),
            'price_change': float(data['priceChange']),
            'price_change_percent': float(data['priceChangePercent']),
            'high': float(data['highPrice']),
            'low': float(data['lowPrice']),
            'open': float(data['openPrice']),
            'timestamp': data['closeTime']
        })
    
    async def get_tickers(self) -> List[UnifiedTicker]:
        """获取所有币安行情"""
        data = await self.api.get_tickers()
        tickers = []
        
        for item in data:
            ticker = UnifiedTicker({
                'symbol': item['symbol'],
                'price': float(item['lastPrice']),
                'volume': float(item['volume']),
                'price_change': float(item['priceChange']),
                'price_change_percent': float(item['priceChangePercent']),
                'high': float(item['highPrice']),
                'low': float(item['lowPrice']),
                'open': float(item['openPrice']),
                'timestamp': item['closeTime']
            })
            tickers.append(ticker)
        
        return tickers
    
    async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取币安深度数据"""
        return await self.api.get_depth(symbol, limit)
    
    async def get_klines(self, symbol: str, interval: str, 
                        limit: int = 1000) -> List[List[Any]]:
        """获取币安K线数据"""
        return await self.api.get_klines(symbol, interval, limit=limit)
    
    async def get_balance(self) -> List[UnifiedBalance]:
        """获取币安余额"""
        balances_data = await self.api.get_balance()
        balances = []
        
        for asset, balance_info in balances_data.items():
            balance = UnifiedBalance({
                'asset': asset,
                'free': balance_info['free'],
                'locked': balance_info['locked']
            })
            balances.append(balance)
        
        return balances
    
    async def create_order(self, symbol: str, side: OrderSide, 
                          order_type: OrderType, quantity: float,
                          price: float = None) -> UnifiedOrder:
        """创建币安订单"""
        # 转换订单类型
        if order_type == OrderType.MARKET:
            order_type_str = 'MARKET'
        elif order_type == OrderType.LIMIT:
            order_type_str = 'LIMIT'
        else:
            raise ValueError(f"不支持的订单类型: {order_type}")
        
        result = await self.api.create_order(
            symbol=symbol,
            side=side.value.upper(),
            order_type=order_type_str,
            quantity=quantity,
            price=price
        )
        
        return UnifiedOrder({
            'order_id': result['orderId'],
            'symbol': symbol,
            'side': side.value,
            'order_type': order_type.value,
            'quantity': quantity,
            'price': result.get('price', 0),
            'status': result['status'],
            'create_time': result['transactTime']
        })
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """取消币安订单"""
        try:
            await self.api.cancel_order(symbol, int(order_id))
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    async def get_order(self, symbol: str, order_id: str) -> UnifiedOrder:
        """获取币安订单信息"""
        result = await self.api.get_order(symbol, int(order_id))
        
        return UnifiedOrder({
            'order_id': order_id,
            'symbol': symbol,
            'side': result['side'].lower(),
            'order_type': result['type'].lower(),
            'quantity': float(result['origQty']),
            'price': float(result.get('price', 0)),
            'status': result['status'],
            'filled_quantity': float(result['executedQty']),
            'avg_price': float(result.get('avgPrice', 0)),
            'create_time': result['time'],
            'update_time': result['updateTime']
        })
    
    async def get_open_orders(self, symbol: str = None) -> List[UnifiedOrder]:
        """获取币安当前挂单"""
        orders_data = await self.api.get_open_orders(symbol)
        orders = []
        
        for order_data in orders_data:
            order = UnifiedOrder({
                'order_id': order_data['orderId'],
                'symbol': order_data['symbol'],
                'side': order_data['side'].lower(),
                'order_type': order_data['type'].lower(),
                'quantity': float(order_data['origQty']),
                'price': float(order_data.get('price', 0)),
                'status': order_data['status'],
                'filled_quantity': float(order_data['executedQty']),
                'create_time': order_data['time']
            })
            orders.append(order)
        
        return orders
    
    async def get_positions(self, symbol: str = None) -> List[UnifiedPosition]:
        """获取币安持仓（主要针对合约）"""
        # 币安现货没有持仓概念，返回空列表
        return []
    
    async def test_connectivity(self) -> bool:
        """测试币安连接性"""
        return await self.api.test_connectivity()


class OKXClient(BaseExchangeClient):
    """欧意客户端"""
    
    def __init__(self, sandbox: bool = False):
        super().__init__(ExchangeType.OKX, sandbox)
        self.api = None
    
    async def connect(self):
        """连接欧意"""
        try:
            self.api = OKXAPI(sandbox=self.sandbox)
            await self.api.__aenter__()
            
            if await self.test_connectivity():
                self.is_connected = True
                logger.info("欧意客户端连接成功")
            else:
                raise Exception("欧意连接测试失败")
                
        except Exception as e:
            logger.error(f"欧意客户端连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self.api:
            await self.api.__aexit__(None, None, None)
            self.is_connected = False
            logger.info("欧意客户端已断开连接")
    
    async def get_ticker(self, symbol: str) -> UnifiedTicker:
        """获取欧意行情"""
        data = await self.api.get_ticker(symbol)
        ticker_data = data['data'][0]
        
        return UnifiedTicker({
            'symbol': symbol,
            'price': float(ticker_data['last']),
            'volume': float(ticker_data['vol24h']),
            'price_change': float(ticker_data['sodUtc0']),
            'price_change_percent': float(ticker_data['sodUtc0']),
            'high': float(ticker_data['high24h']),
            'low': float(ticker_data['low24h']),
            'open': float(ticker_data['open24h']),
            'timestamp': ticker_data['ts']
        })
    
    async def get_tickers(self) -> List[UnifiedTicker]:
        """获取所有欧意行情"""
        data = await self.api.get_tickers()
        tickers = []
        
        for ticker_data in data:
            ticker = UnifiedTicker({
                'symbol': ticker_data['instId'],
                'price': float(ticker_data['last']),
                'volume': float(ticker_data['vol24h']),
                'price_change': float(ticker_data['sodUtc0']),
                'price_change_percent': float(ticker_data['sodUtc0']),
                'high': float(ticker_data['high24h']),
                'low': float(ticker_data['low24h']),
                'open': float(ticker_data['open24h']),
                'timestamp': ticker_data['ts']
            })
            tickers.append(ticker)
        
        return tickers
    
    async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取欧意深度数据"""
        return await self.api.get_depth(symbol, limit)
    
    async def get_klines(self, symbol: str, interval: str, 
                        limit: int = 1000) -> List[List[Any]]:
        """获取欧意K线数据"""
        return await self.api.get_klines(symbol, interval, limit=limit)
    
    async def get_balance(self) -> List[UnifiedBalance]:
        """获取欧意余额"""
        balances_data = await self.api.get_account_balance()
        balances = []
        
        for balance_data in balances_data['data'][0]['details']:
            balance = UnifiedBalance({
                'asset': balance_data['ccy'],
                'free': float(balance_data['availBal']),
                'locked': float(balance_data['frozenBal'])
            })
            balances.append(balance)
        
        return balances
    
    async def create_order(self, symbol: str, side: OrderSide, 
                          order_type: OrderType, quantity: float,
                          price: float = None) -> UnifiedOrder:
        """创建欧意订单"""
        # 转换订单类型
        if order_type == OrderType.MARKET:
            ord_type = 'market'
        elif order_type == OrderType.LIMIT:
            ord_type = 'limit'
        else:
            raise ValueError(f"不支持的订单类型: {order_type}")
        
        result = await self.api.place_order(
            inst_id=symbol,
            td_mode='cash',  # 现货交易
            side=side.value,
            ord_type=ord_type,
            sz=str(quantity),
            px=str(price) if price else None
        )
        
        return UnifiedOrder({
            'order_id': result['data'][0]['ordId'],
            'symbol': symbol,
            'side': side.value,
            'order_type': order_type.value,
            'quantity': quantity,
            'price': price or 0,
            'status': 'pending',
            'create_time': int(time.time() * 1000)
        })
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """取消欧意订单"""
        try:
            await self.api.cancel_order(symbol, ord_id=order_id)
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    async def get_order(self, symbol: str, order_id: str) -> UnifiedOrder:
        """获取欧意订单信息"""
        result = await self.api.get_order_info(symbol, ord_id=order_id)
        order_data = result['data'][0]
        
        return UnifiedOrder({
            'order_id': order_id,
            'symbol': symbol,
            'side': order_data['side'],
            'order_type': order_data['ordType'],
            'quantity': float(order_data['sz']),
            'price': float(order_data.get('px', 0)),
            'status': order_data['state'],
            'filled_quantity': float(order_data.get('accFillSz', 0)),
            'avg_price': float(order_data.get('avgPx', 0)),
            'create_time': int(order_data['cTime'])
        })
    
    async def get_open_orders(self, symbol: str = None) -> List[UnifiedOrder]:
        """获取欧意当前挂单"""
        # 欧意没有专门的挂单接口，使用订单历史接口过滤
        orders_data = await self.api.get_order_history(inst_type='SPOT')
        orders = []
        
        for order_data in orders_data:
            if order_data['state'] in ['live', 'partially_filled']:
                order = UnifiedOrder({
                    'order_id': order_data['ordId'],
                    'symbol': order_data['instId'],
                    'side': order_data['side'],
                    'order_type': order_data['ordType'],
                    'quantity': float(order_data['sz']),
                    'price': float(order_data.get('px', 0)),
                    'status': order_data['state'],
                    'filled_quantity': float(order_data.get('accFillSz', 0)),
                    'create_time': int(order_data['cTime'])
                })
                orders.append(order)
        
        return orders
    
    async def get_positions(self, symbol: str = None) -> List[UnifiedPosition]:
        """获取欧意持仓（主要针对合约）"""
        # 欧意现货没有持仓概念，返回空列表
        return []
    
    async def test_connectivity(self) -> bool:
        """测试欧意连接性"""
        return await self.api.test_connectivity()


class ExchangeClientFactory:
    """交易所客户端工厂"""
    
    @staticmethod
    def create_client(exchange_type: ExchangeType, sandbox: bool = False) -> BaseExchangeClient:
        """创建交易所客户端"""
        if exchange_type == ExchangeType.BINANCE:
            return BinanceClient(sandbox)
        elif exchange_type == ExchangeType.OKX:
            return OKXClient(sandbox)
        else:
            raise ValueError(f"不支持的交易所类型: {exchange_type}")
    
    @staticmethod
    def get_supported_exchanges() -> List[ExchangeType]:
        """获取支持的交易所列表"""
        return [ExchangeType.BINANCE, ExchangeType.OKX]


# 使用示例
async def example_usage():
    """使用示例"""
    try:
        # 创建币安客户端
        binance_client = ExchangeClientFactory.create_client(
            ExchangeType.BINANCE, sandbox=True
        )
        
        await binance_client.connect()
        
        # 获取行情
        ticker = await binance_client.get_ticker("BTCUSDT")
        print(f"BTCUSDT价格: {ticker.price}")
        
        # 获取余额
        balances = await binance_client.get_balance()
        for balance in balances:
            if balance.total > 0:
                print(f"{balance.asset}: {balance.total}")
        
        await binance_client.disconnect()
        
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())