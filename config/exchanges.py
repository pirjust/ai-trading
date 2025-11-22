"""
交易所配置管理
定义和支持的交易所配置和参数
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel


class ExchangeType(Enum):
    """交易所类型枚举"""
    SPOT = "spot"
    FUTURES = "futures"
    OPTION = "option"
    MARGIN = "margin"


class ExchangeConfig(BaseModel):
    """交易所配置"""
    name: str
    display_name: str
    base_url: str
    sandbox_url: str
    supported_types: List[ExchangeType]
    rate_limit: int  # 每分钟请求限制
    precision: Dict[str, int]  # 精度配置
    
    # API配置
    requires_passphrase: bool = False
    requires_timestamp: bool = True
    
    # 交易配置
    min_order_amount: float = 0.001
    max_leverage: int = 100
    
    class Config:
        use_enum_values = True


class EXCHANGE_CONFIG:
    """交易所配置管理器"""
    
    # 支持的交易所配置
    exchanges: Dict[str, ExchangeConfig] = {
        "binance": ExchangeConfig(
            name="binance",
            display_name="币安",
            base_url="https://api.binance.com",
            sandbox_url="https://testnet.binance.vision",
            supported_types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
            rate_limit=1200,
            precision={"price": 8, "amount": 8},
            min_order_amount=0.001,
            max_leverage=125
        ),
        
        "okx": ExchangeConfig(
            name="okx",
            display_name="欧意",
            base_url="https://www.okx.com",
            sandbox_url="https://www.okx.com",
            supported_types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.OPTION, ExchangeType.MARGIN],
            rate_limit=300,
            precision={"price": 8, "amount": 8},
            requires_passphrase=True,
            min_order_amount=0.001,
            max_leverage=100
        ),
        
        "bybit": ExchangeConfig(
            name="bybit",
            display_name="Bybit",
            base_url="https://api.bybit.com",
            sandbox_url="https://api-testnet.bybit.com",
            supported_types=[ExchangeType.SPOT, ExchangeType.FUTURES],
            rate_limit=600,
            precision={"price": 8, "amount": 8},
            min_order_amount=0.001,
            max_leverage=100
        ),
        
        "coinbase": ExchangeConfig(
            name="coinbase",
            display_name="Coinbase",
            base_url="https://api.coinbase.com",
            sandbox_url="https://api-public.sandbox.coinbase.com",
            supported_types=[ExchangeType.SPOT],
            rate_limit=1000,
            precision={"price": 8, "amount": 8},
            min_order_amount=0.001
        )
    }
    
    @classmethod
    def get_exchange_config(cls, exchange_name: str) -> ExchangeConfig:
        """获取指定交易所配置"""
        if exchange_name not in cls.exchanges:
            raise ValueError(f"不支持的交易所: {exchange_name}")
        return cls.exchanges[exchange_name]
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """获取支持的交易所列表"""
        return list(cls.exchanges.keys())
    
    @classmethod
    def validate_exchange_type(cls, exchange_name: str, exchange_type: ExchangeType) -> bool:
        """验证交易所是否支持指定类型"""
        config = cls.get_exchange_config(exchange_name)
        return exchange_type in config.supported_types
    
    @classmethod
    def get_precision(cls, exchange_name: str, precision_type: str) -> int:
        """获取交易所精度配置"""
        config = cls.get_exchange_config(exchange_name)
        return config.precision.get(precision_type, 8)
    
    @classmethod
    def get_rate_limit(cls, exchange_name: str) -> int:
        """获取交易所请求限制"""
        config = cls.get_exchange_config(exchange_name)
        return config.rate_limit


# 交易对配置
class SymbolConfig(BaseModel):
    """交易对配置"""
    symbol: str
    base_asset: str
    quote_asset: str
    min_order_amount: float
    min_order_value: float
    price_precision: int
    amount_precision: int
    is_active: bool = True


class SYMBOL_CONFIG:
    """交易对配置管理器"""
    
    # 主要交易对配置
    symbols: Dict[str, SymbolConfig] = {
        "BTCUSDT": SymbolConfig(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            min_order_amount=0.0001,
            min_order_value=10.0,
            price_precision=2,
            amount_precision=6
        ),
        
        "ETHUSDT": SymbolConfig(
            symbol="ETHUSDT",
            base_asset="ETH",
            quote_asset="USDT",
            min_order_amount=0.001,
            min_order_value=10.0,
            price_precision=2,
            amount_precision=5
        ),
        
        "BNBUSDT": SymbolConfig(
            symbol="BNBUSDT",
            base_asset="BNB",
            quote_asset="USDT",
            min_order_amount=0.01,
            min_order_value=10.0,
            price_precision=3,
            amount_precision=4
        ),
        
        "ADAUSDT": SymbolConfig(
            symbol="ADAUSDT",
            base_asset="ADA",
            quote_asset="USDT",
            min_order_amount=1.0,
            min_order_value=10.0,
            price_precision=4,
            amount_precision=1
        )
    }
    
    @classmethod
    def get_symbol_config(cls, symbol: str) -> SymbolConfig:
        """获取交易对配置"""
        if symbol not in cls.symbols:
            raise ValueError(f"不支持的交易对: {symbol}")
        return cls.symbols[symbol]
    
    @classmethod
    def validate_order_amount(cls, symbol: str, amount: float) -> bool:
        """验证订单数量"""
        config = cls.get_symbol_config(symbol)
        return amount >= config.min_order_amount
    
    @classmethod
    def validate_order_value(cls, symbol: str, amount: float, price: float) -> bool:
        """验证订单价值"""
        config = cls.get_symbol_config(symbol)
        order_value = amount * price
        return order_value >= config.min_order_value


if __name__ == "__main__":
    # 配置验证测试
    print("=== 交易所配置验证 ===")
    
    for exchange_name in EXCHANGE_CONFIG.get_supported_exchanges():
        config = EXCHANGE_CONFIG.get_exchange_config(exchange_name)
        print(f"{exchange_name}: {config.display_name}")
        print(f"  支持类型: {[t.value for t in config.supported_types]}")
        print(f"  请求限制: {config.rate_limit}/分钟")
        print()
    
    print("=== 交易对配置验证 ===")
    for symbol in SYMBOL_CONFIG.symbols.keys():
        config = SYMBOL_CONFIG.get_symbol_config(symbol)
        print(f"{symbol}: {config.base_asset}/{config.quote_asset}")
        print(f"  最小数量: {config.min_order_amount}")
        print(f"  最小价值: {config.min_order_value}")
        print()