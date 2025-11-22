"""
数据格式转换器
提供统一的数据格式转换功能，将不同交易所的数据格式转换为统一格式
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UnifiedDataFormat:
    """统一数据格式定义"""
    
    @staticmethod
    def format_ticker(exchange: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """统一行情数据格式"""
        if exchange == "binance":
            return UnifiedDataFormat._format_binance_ticker(raw_data)
        elif exchange == "okx":
            return UnifiedDataFormat._format_okx_ticker(raw_data)
        elif exchange == "bybit":
            return UnifiedDataFormat._format_bybit_ticker(raw_data)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
    
    @staticmethod
    def format_depth(exchange: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """统一深度数据格式"""
        if exchange == "binance":
            return UnifiedDataFormat._format_binance_depth(raw_data)
        elif exchange == "okx":
            return UnifiedDataFormat._format_okx_depth(raw_data)
        elif exchange == "bybit":
            return UnifiedDataFormat._format_bybit_depth(raw_data)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
    
    @staticmethod
    def format_klines(exchange: str, raw_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """统一K线数据格式"""
        if exchange == "binance":
            return UnifiedDataFormat._format_binance_klines(raw_data)
        elif exchange == "okx":
            return UnifiedDataFormat._format_okx_klines(raw_data)
        elif exchange == "bybit":
            return UnifiedDataFormat._format_bybit_klines(raw_data)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
    
    @staticmethod
    def format_order(exchange: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """统一订单数据格式"""
        if exchange == "binance":
            return UnifiedDataFormat._format_binance_order(raw_data)
        elif exchange == "okx":
            return UnifiedDataFormat._format_okx_order(raw_data)
        elif exchange == "bybit":
            return UnifiedDataFormat._format_bybit_order(raw_data)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
    
    @staticmethod
    def format_balance(exchange: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """统一余额数据格式"""
        if exchange == "binance":
            return UnifiedDataFormat._format_binance_balance(raw_data)
        elif exchange == "okx":
            return UnifiedDataFormat._format_okx_balance(raw_data)
        elif exchange == "bybit":
            return UnifiedDataFormat._format_bybit_balance(raw_data)
        else:
            raise ValueError(f"不支持的交易所: {exchange}")
    
    # 币安数据格式转换
    @staticmethod
    def _format_binance_ticker(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换币安行情数据"""
        return {
            "symbol": raw_data["symbol"],
            "price": float(raw_data["lastPrice"]),
            "volume": float(raw_data["volume"]),
            "price_change": float(raw_data["priceChange"]),
            "price_change_percent": float(raw_data["priceChangePercent"]),
            "high": float(raw_data["highPrice"]),
            "low": float(raw_data["lowPrice"]),
            "open": float(raw_data["openPrice"]),
            "timestamp": raw_data["closeTime"],
            "exchange": "binance"
        }
    
    @staticmethod
    def _format_binance_depth(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换币安深度数据"""
        return {
            "symbol": raw_data["symbol"],
            "bids": [[float(price), float(amount)] for price, amount in raw_data["bids"]],
            "asks": [[float(price), float(amount)] for price, amount in raw_data["asks"]],
            "timestamp": raw_data["lastUpdateId"],
            "exchange": "binance"
        }
    
    @staticmethod
    def _format_binance_klines(raw_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """转换币安K线数据"""
        klines = []
        for kline in raw_data:
            klines.append({
                "timestamp": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": kline[6],
                "quote_volume": float(kline[7]),
                "trades": kline[8],
                "taker_buy_base": float(kline[9]),
                "taker_buy_quote": float(kline[10])
            })
        return klines
    
    @staticmethod
    def _format_binance_order(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换币安订单数据"""
        return {
            "order_id": str(raw_data["orderId"]),
            "symbol": raw_data["symbol"],
            "side": raw_data["side"].lower(),
            "order_type": raw_data["type"].lower(),
            "quantity": float(raw_data["origQty"]),
            "price": float(raw_data.get("price", 0)),
            "status": raw_data["status"],
            "filled_quantity": float(raw_data["executedQty"]),
            "avg_price": float(raw_data.get("avgPrice", 0)),
            "create_time": raw_data["time"],
            "update_time": raw_data["updateTime"],
            "exchange": "binance"
        }
    
    @staticmethod
    def _format_binance_balance(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换币安余额数据"""
        balances = {}
        for balance in raw_data.get("balances", []):
            asset = balance["asset"]
            balances[asset] = {
                "free": float(balance["free"]),
                "locked": float(balance["locked"])
            }
        return {
            "balances": balances,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "exchange": "binance"
        }
    
    # 欧意数据格式转换
    @staticmethod
    def _format_okx_ticker(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换欧意行情数据"""
        data = raw_data["data"][0] if "data" in raw_data else raw_data
        return {
            "symbol": data["instId"],
            "price": float(data["last"]),
            "volume": float(data["vol24h"]),
            "price_change": float(data["sodUtc0"]),
            "price_change_percent": float(data["sodUtc0"]),
            "high": float(data["high24h"]),
            "low": float(data["low24h"]),
            "open": float(data["open24h"]),
            "timestamp": data["ts"],
            "exchange": "okx"
        }
    
    @staticmethod
    def _format_okx_depth(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换欧意深度数据"""
        data = raw_data["data"][0] if "data" in raw_data else raw_data
        return {
            "symbol": data["instId"],
            "bids": [[float(price), float(amount)] for price, amount in data["bids"]],
            "asks": [[float(price), float(amount)] for price, amount in data["asks"]],
            "timestamp": data["ts"],
            "exchange": "okx"
        }
    
    @staticmethod
    def _format_okx_klines(raw_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """转换欧意K线数据"""
        klines = []
        for kline in raw_data:
            klines.append({
                "timestamp": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": kline[0],
                "quote_volume": float(kline[5]) * float(kline[4]),
                "trades": 0,
                "taker_buy_base": 0,
                "taker_buy_quote": 0
            })
        return klines
    
    @staticmethod
    def _format_okx_order(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换欧意订单数据"""
        data = raw_data["data"][0] if "data" in raw_data else raw_data
        return {
            "order_id": data["ordId"],
            "symbol": data["instId"],
            "side": data["side"],
            "order_type": data["ordType"],
            "quantity": float(data["sz"]),
            "price": float(data.get("px", 0)),
            "status": data["state"],
            "filled_quantity": float(data.get("accFillSz", 0)),
            "avg_price": float(data.get("avgPx", 0)),
            "create_time": int(data["cTime"]),
            "update_time": int(data["uTime"]),
            "exchange": "okx"
        }
    
    @staticmethod
    def _format_okx_balance(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换欧意余额数据"""
        data = raw_data["data"][0] if "data" in raw_data else raw_data
        balances = {}
        for detail in data.get("details", []):
            asset = detail["ccy"]
            balances[asset] = {
                "free": float(detail["availBal"]),
                "locked": float(detail["frozenBal"])
            }
        return {
            "balances": balances,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "exchange": "okx"
        }
    
    # Bybit数据格式转换（占位符）
    @staticmethod
    def _format_bybit_ticker(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换Bybit行情数据"""
        return {
            "symbol": raw_data.get("symbol", ""),
            "price": float(raw_data.get("lastPrice", 0)),
            "volume": float(raw_data.get("volume24h", 0)),
            "price_change": float(raw_data.get("price24hPcnt", 0)),
            "price_change_percent": float(raw_data.get("price24hPcnt", 0)) * 100,
            "high": float(raw_data.get("highPrice24h", 0)),
            "low": float(raw_data.get("lowPrice24h", 0)),
            "open": float(raw_data.get("openPrice", 0)),
            "timestamp": raw_data.get("time", 0),
            "exchange": "bybit"
        }
    
    @staticmethod
    def _format_bybit_depth(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换Bybit深度数据"""
        return {
            "symbol": raw_data.get("symbol", ""),
            "bids": [[float(price), float(amount)] for price, amount in raw_data.get("b", [])],
            "asks": [[float(price), float(amount)] for price, amount in raw_data.get("a", [])],
            "timestamp": raw_data.get("ts", 0),
            "exchange": "bybit"
        }
    
    @staticmethod
    def _format_bybit_klines(raw_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """转换Bybit K线数据"""
        klines = []
        for kline in raw_data:
            klines.append({
                "timestamp": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": kline[6],
                "quote_volume": float(kline[7]),
                "trades": kline[8]
            })
        return klines
    
    @staticmethod
    def _format_bybit_order(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换Bybit订单数据"""
        return {
            "order_id": raw_data.get("orderId", ""),
            "symbol": raw_data.get("symbol", ""),
            "side": raw_data.get("side", "").lower(),
            "order_type": raw_data.get("orderType", "").lower(),
            "quantity": float(raw_data.get("qty", 0)),
            "price": float(raw_data.get("price", 0)),
            "status": raw_data.get("orderStatus", ""),
            "filled_quantity": float(raw_data.get("cumExecQty", 0)),
            "avg_price": float(raw_data.get("avgPrice", 0)),
            "create_time": raw_data.get("createdTime", 0),
            "update_time": raw_data.get("updatedTime", 0),
            "exchange": "bybit"
        }
    
    @staticmethod
    def _format_bybit_balance(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换Bybit余额数据"""
        balances = {}
        for wallet in raw_data.get("list", []):
            for coin in wallet.get("coin", []):
                asset = coin["coin"]
                balances[asset] = {
                    "free": float(coin.get("free", 0)),
                    "locked": float(coin.get("locked", 0))
                }
        return {
            "balances": balances,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "exchange": "bybit"
        }


class DataFormatter:
    """数据格式化器"""
    
    @staticmethod
    def normalize_symbol(symbol: str, exchange: str) -> str:
        """标准化交易对符号"""
        if exchange == "binance":
            return symbol.upper()
        elif exchange == "okx":
            return symbol.upper()
        elif exchange == "bybit":
            return symbol.upper()
        else:
            return symbol
    
    @staticmethod
    def normalize_price(price: float, exchange: str, symbol: str) -> float:
        """标准化价格"""
        # 这里可以根据交易所和交易对的精度要求进行标准化
        return round(price, 8)
    
    @staticmethod
    def normalize_amount(amount: float, exchange: str, symbol: str) -> float:
        """标准化数量"""
        # 这里可以根据交易所和交易对的精度要求进行标准化
        return round(amount, 8)
    
    @staticmethod
    def convert_timestamp(timestamp: Any, exchange: str) -> int:
        """转换时间戳为毫秒"""
        if isinstance(timestamp, int):
            # 如果已经是毫秒级时间戳
            if timestamp > 1e12:  # 大于1万亿，可能是微秒级
                return timestamp // 1000
            elif timestamp > 1e9:  # 大于10亿，可能是秒级
                return timestamp * 1000
            else:
                return timestamp
        elif isinstance(timestamp, str):
            # 如果是字符串时间戳
            try:
                return int(timestamp)
            except ValueError:
                # 如果是ISO格式时间
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return int(dt.timestamp() * 1000)
        else:
            return int(datetime.now().timestamp() * 1000)
    
    @staticmethod
    def validate_data_format(data: Dict[str, Any], data_type: str) -> bool:
        """验证数据格式"""
        required_fields = {
            "ticker": ["symbol", "price", "timestamp"],
            "depth": ["symbol", "bids", "asks", "timestamp"],
            "order": ["order_id", "symbol", "side", "order_type", "quantity", "status"],
            "balance": ["balances", "timestamp"]
        }
        
        if data_type not in required_fields:
            return False
        
        for field in required_fields[data_type]:
            if field not in data:
                logger.warning(f"数据格式验证失败: 缺少字段 {field}")
                return False
        
        return True


# 使用示例
if __name__ == "__main__":
    # 测试数据格式转换
    binance_ticker = {
        "symbol": "BTCUSDT",
        "lastPrice": "50000.00",
        "volume": "1000.5",
        "priceChange": "100.00",
        "priceChangePercent": "0.2",
        "highPrice": "51000.00",
        "lowPrice": "49000.00",
        "openPrice": "49900.00",
        "closeTime": 1640995200000
    }
    
    formatted = UnifiedDataFormat.format_ticker("binance", binance_ticker)
    print("币安行情数据转换结果:")
    print(formatted)
    
    # 验证数据格式
    is_valid = DataFormatter.validate_data_format(formatted, "ticker")
    print(f"数据格式验证: {is_valid}")