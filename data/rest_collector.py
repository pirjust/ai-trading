"""
REST API数据采集器
通过REST API定期获取市场数据
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from .base_collector import BaseCollector
from data.exchange_client import ExchangeClientFactory, ExchangeType

logger = logging.getLogger(__name__)


class RESTCollector(BaseCollector):
    """REST API数据采集器"""
    
    def __init__(self, exchange: str, symbols: List[str], exchange_type: ExchangeType = ExchangeType.BINANCE):
        super().__init__(exchange, symbols)
        self.exchange_type = exchange_type
        self.client = None
        self.collection_interval = 60  # 默认60秒采集一次
        self.last_collection_time = 0
        
    async def start(self):
        """启动数据采集"""
        try:
            # 创建交易所客户端
            self.client = ExchangeClientFactory.create_client(self.exchange_type, sandbox=True)
            await self.client.connect()
            
            self.is_running = True
            logger.info(f"REST数据采集器已启动: {self.exchange} - {self.symbols}")
            
            # 开始采集循环
            asyncio.create_task(self._collection_loop())
            
        except Exception as e:
            logger.error(f"启动REST采集器失败: {e}")
            self.is_running = False
    
    async def stop(self):
        """停止数据采集"""
        self.is_running = False
        
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.error(f"断开交易所连接失败: {e}")
        
        logger.info(f"REST数据采集器已停止: {self.exchange}")
    
    async def _collection_loop(self):
        """数据采集循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查是否到了采集时间
                if current_time - self.last_collection_time >= self.collection_interval:
                    await self._collect_data()
                    self.last_collection_time = current_time
                
                # 等待下一次检查
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"数据采集循环错误: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒
    
    async def _collect_data(self):
        """采集数据"""
        try:
            for symbol in self.symbols:
                try:
                    # 获取ticker数据
                    ticker = await self.client.get_ticker(symbol)
                    
                    # 获取K线数据
                    klines = await self.client.get_klines(symbol, "1m", limit=100)
                    
                    # 转换K线数据
                    kline_df = self._convert_klines_to_dataframe(klines)
                    
                    # 组合数据
                    market_data = {
                        "exchange": self.exchange,
                        "symbol": symbol,
                        "timestamp": ticker.timestamp,
                        "price": ticker.price,
                        "volume": ticker.volume,
                        "price_change": ticker.price_change,
                        "price_change_percent": ticker.price_change_percent,
                        "high": ticker.high,
                        "low": ticker.low,
                        "open": ticker.open,
                        "klines": kline_df.to_dict('records') if not kline_df.empty else []
                    }
                    
                    # 存储数据
                    self.collected_data[symbol] = market_data
                    
                    # 通知回调
                    self.notify_callbacks(market_data)
                    
                    logger.debug(f"采集到数据: {symbol} - {ticker.price}")
                    
                except Exception as e:
                    logger.error(f"采集 {symbol} 数据失败: {e}")
                    
        except Exception as e:
            logger.error(f"数据采集失败: {e}")
    
    def _convert_klines_to_dataframe(self, klines: List[List[Any]]) -> pd.DataFrame:
        """转换K线数据为DataFrame"""
        if not klines:
            return pd.DataFrame()
        
        # K线数据格式: [timestamp, open, high, low, close, volume, ...]
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # 转换数据类型
        numeric_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                         'quote_asset_volume', 'number_of_trades']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 转换时间戳为datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        
        return df
    
    async def get_historical_data(self, symbol: str, interval: str = "1h", 
                                limit: int = 1000) -> pd.DataFrame:
        """获取历史数据"""
        try:
            if not self.client:
                raise Exception("客户端未初始化")
            
            klines = await self.client.get_klines(symbol, interval, limit=limit)
            return self._convert_klines_to_dataframe(klines)
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿数据"""
        try:
            if not self.client:
                raise Exception("客户端未初始化")
            
            depth = await self.client.get_depth(symbol, limit)
            
            return {
                "exchange": self.exchange,
                "symbol": symbol,
                "timestamp": time.time(),
                "bids": depth.get("bids", [])[:limit],
                "asks": depth.get("asks", [])[:limit],
                "bid_price": depth.get("bids", [])[0][0] if depth.get("bids") else None,
                "ask_price": depth.get("asks", [])[0][0] if depth.get("asks") else None,
                "spread": None  # 将在下面计算
            }
            
        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return {}
    
    def set_collection_interval(self, interval: int):
        """设置采集间隔"""
        self.collection_interval = max(interval, 5)  # 最小5秒间隔
        logger.info(f"数据采集间隔已设置为: {self.collection_interval}秒")
    
    def get_collected_data(self, symbol: str = None) -> Dict[str, Any]:
        """获取采集的数据"""
        if symbol:
            return self.collected_data.get(symbol, {})
        return self.collected_data.copy()
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """获取市场摘要"""
        summary = {
            "exchange": self.exchange,
            "timestamp": time.time(),
            "symbols": {}
        }
        
        for symbol, data in self.collected_data.items():
            summary["symbols"][symbol] = {
                "price": data.get("price", 0),
                "volume": data.get("volume", 0),
                "price_change_percent": data.get("price_change_percent", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0)
            }
        
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """获取采集器状态"""
        return {
            "exchange": self.exchange,
            "symbols": self.symbols,
            "is_running": self.is_running,
            "collection_interval": self.collection_interval,
            "last_collection_time": self.last_collection_time,
            "collected_symbols": list(self.collected_data.keys()),
            "total_collected": len(self.collected_data)
        }


# 使用示例
async def example_usage():
    """使用示例"""
    collector = RESTCollector("binance", ["BTCUSDT", "ETHUSDT"])
    
    try:
        # 启动采集器
        await collector.start()
        
        # 运行一段时间
        await asyncio.sleep(60)
        
        # 获取采集的数据
        data = collector.get_collected_data()
        for symbol, market_data in data.items():
            print(f"{symbol}: 价格={market_data.get('price')}, "
                  f"变动={market_data.get('price_change_percent')}%")
        
        # 获取市场摘要
        summary = await collector.get_market_summary()
        print(f"市场摘要: {summary}")
        
        # 停止采集器
        await collector.stop()
        
    except Exception as e:
        print(f"示例执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())