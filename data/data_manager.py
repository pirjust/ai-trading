"""
数据管理器
统一管理数据获取、存储和访问
支持从交易所API、数据库、缓存等多数据源获取数据
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from core.config import settings
from core.database import get_db
from .exchange_client import ExchangeClient
from .websocket_collector import WebSocketCollector
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.exchange_clients = {}
        self.websocket_collectors = {}
        self.cache = {}
        self.cache_ttl = {}  # 缓存过期时间
        self._initialized = False
    
    async def initialize(self):
        """初始化数据管理器"""
        if self._initialized:
            return
        
        logger.info("初始化数据管理器...")
        
        # 初始化交易所客户端
        await self._init_exchange_clients()
        
        # 初始化WebSocket收集器
        await self._init_websocket_collectors()
        
        self._initialized = True
        logger.info("数据管理器初始化完成")
    
    async def _init_exchange_clients(self):
        """初始化交易所客户端"""
        # 币安
        if settings.exchange.binance_api_key:
            self.exchange_clients['binance'] = ExchangeClient('binance')
            await self.exchange_clients['binance'].initialize()
            logger.info("币安客户端初始化完成")
        
        # 欧意
        if settings.exchange.okx_api_key:
            self.exchange_clients['okx'] = ExchangeClient('okx')
            await self.exchange_clients['okx'].initialize()
            logger.info("欧意客户端初始化完成")
        
        # Bybit
        if settings.exchange.bybit_api_key:
            self.exchange_clients['bybit'] = ExchangeClient('bybit')
            await self.exchange_clients['bybit'].initialize()
            logger.info("Bybit客户端初始化完成")
    
    async def _init_websocket_collectors(self):
        """初始化WebSocket收集器"""
        for exchange_name, client in self.exchange_clients.items():
            try:
                collector = WebSocketCollector(exchange_name, client)
                self.websocket_collectors[exchange_name] = collector
                logger.info(f"{exchange_name} WebSocket收集器初始化完成")
            except Exception as e:
                logger.error(f"{exchange_name} WebSocket收集器初始化失败: {e}")
    
    async def get_kline_data(self,
                           symbol: str,
                           interval: str = "1h",
                           limit: int = 100,
                           exchange: str = "binance",
                           use_cache: bool = True) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 数据条数
            exchange: 交易所
            use_cache: 是否使用缓存
            
        Returns:
            K线数据DataFrame
        """
        cache_key = f"kline_{exchange}_{symbol}_{interval}_{limit}"
        
        # 检查缓存
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取K线数据: {cache_key}")
            return self.cache[cache_key]
        
        # 从交易所API获取数据
        try:
            if exchange not in self.exchange_clients:
                raise ValueError(f"不支持的交易所: {exchange}")
            
            client = self.exchange_clients[exchange]
            data = await client.get_kline_data(symbol, interval, limit)
            
            # 转换为DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 数据清理和转换
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 转换数值列
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 只保留需要的列
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            # 存入缓存
            if use_cache:
                self._set_cache(cache_key, df, ttl=300)  # 5分钟缓存
            
            logger.info(f"获取K线数据成功: {symbol} {interval} {len(df)}条")
            return df
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    async def get_ticker_data(self,
                            symbol: str,
                            exchange: str = "binance",
                            use_cache: bool = True) -> Dict[str, Any]:
        """
        获取行情数据
        
        Args:
            symbol: 交易对
            exchange: 交易所
            use_cache: 是否使用缓存
            
        Returns:
            行情数据字典
        """
        cache_key = f"ticker_{exchange}_{symbol}"
        
        # 检查缓存
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取行情数据: {cache_key}")
            return self.cache[cache_key]
        
        try:
            if exchange not in self.exchange_clients:
                raise ValueError(f"不支持的交易所: {exchange}")
            
            client = self.exchange_clients[exchange]
            ticker_data = await client.get_ticker_data(symbol)
            
            # 存入缓存
            if use_cache:
                self._set_cache(cache_key, ticker_data, ttl=30)  # 30秒缓存
            
            logger.info(f"获取行情数据成功: {symbol}")
            return ticker_data
            
        except Exception as e:
            logger.error(f"获取行情数据失败: {e}")
            raise
    
    async def get_orderbook_data(self,
                               symbol: str,
                               depth: int = 20,
                               exchange: str = "binance",
                               use_cache: bool = False) -> Dict[str, Any]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对
            depth: 深度
            exchange: 交易所
            use_cache: 是否使用缓存
            
        Returns:
            订单簿数据字典
        """
        cache_key = f"orderbook_{exchange}_{symbol}_{depth}"
        
        # 检查缓存
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取订单簿数据: {cache_key}")
            return self.cache[cache_key]
        
        try:
            if exchange not in self.exchange_clients:
                raise ValueError(f"不支持的交易所: {exchange}")
            
            client = self.exchange_clients[exchange]
            orderbook_data = await client.get_orderbook_data(symbol, depth)
            
            # 存入缓存
            if use_cache:
                self._set_cache(cache_key, orderbook_data, ttl=5)  # 5秒缓存
            
            logger.debug(f"获取订单簿数据成功: {symbol}")
            return orderbook_data
            
        except Exception as e:
            logger.error(f"获取订单簿数据失败: {e}")
            raise
    
    async def get_historical_data_from_db(self,
                                       symbol: str,
                                       start_time: datetime,
                                       end_time: datetime,
                                       interval: str = "1h") -> pd.DataFrame:
        """
        从数据库获取历史数据
        
        Args:
            symbol: 交易对
            start_time: 开始时间
            end_time: 结束时间
            interval: 时间间隔
            
        Returns:
            历史数据DataFrame
        """
        try:
            # 这里应该从实际的数据库表中查询历史数据
            # 简化实现，实际需要根据数据库结构调整
            
            db_gen = get_db()
            async for db in db_gen:
                # 假设有kline_data表
                query = select(KlineData).where(
                    and_(
                        KlineData.symbol == symbol,
                        KlineData.interval == interval,
                        KlineData.timestamp >= start_time,
                        KlineData.timestamp <= end_time
                    )
                ).order_by(KlineData.timestamp)
                
                result = await db.execute(query)
                records = result.scalars().all()
                
                # 转换为DataFrame
                data = []
                for record in records:
                    data.append({
                        'timestamp': record.timestamp,
                        'open': record.open,
                        'high': record.high,
                        'low': record.low,
                        'close': record.close,
                        'volume': record.volume
                    })
                
                df = pd.DataFrame(data)
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                
                logger.info(f"从数据库获取历史数据成功: {symbol} {len(df)}条")
                return df
            
        except Exception as e:
            logger.error(f"从数据库获取历史数据失败: {e}")
            raise
    
    async def save_kline_data_to_db(self,
                                  data: pd.DataFrame,
                                  symbol: str,
                                  interval: str = "1h"):
        """
        保存K线数据到数据库
        
        Args:
            data: K线数据
            symbol: 交易对
            interval: 时间间隔
        """
        try:
            db_gen = get_db()
            async for db in db_gen:
                # 批量插入数据
                records = []
                for timestamp, row in data.iterrows():
                    record = KlineData(
                        symbol=symbol,
                        interval=interval,
                        timestamp=timestamp,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    records.append(record)
                
                db.add_all(records)
                await db.commit()
                
                logger.info(f"保存K线数据到数据库成功: {symbol} {len(records)}条")
                
        except Exception as e:
            logger.error(f"保存K线数据到数据库失败: {e}")
            raise
    
    async def start_realtime_collection(self,
                                     symbol: str,
                                     exchange: str = "binance"):
        """
        开始实时数据收集
        
        Args:
            symbol: 交易对
            exchange: 交易所
        """
        try:
            if exchange not in self.websocket_collectors:
                raise ValueError(f"{exchange} WebSocket收集器未初始化")
            
            collector = self.websocket_collectors[exchange]
            await collector.start_collecting(symbol)
            
            logger.info(f"开始实时数据收集: {symbol} @ {exchange}")
            
        except Exception as e:
            logger.error(f"开始实时数据收集失败: {e}")
            raise
    
    async def stop_realtime_collection(self,
                                    symbol: str,
                                    exchange: str = "binance"):
        """
        停止实时数据收集
        
        Args:
            symbol: 交易对
            exchange: 交易所
        """
        try:
            if exchange not in self.websocket_collectors:
                return
            
            collector = self.websocket_collectors[exchange]
            await collector.stop_collecting(symbol)
            
            logger.info(f"停止实时数据收集: {symbol} @ {exchange}")
            
        except Exception as e:
            logger.error(f"停止实时数据收集失败: {e}")
            raise
    
    async def get_latest_price(self,
                            symbol: str,
                            exchange: str = "binance") -> float:
        """
        获取最新价格
        
        Args:
            symbol: 交易对
            exchange: 交易所
            
        Returns:
            最新价格
        """
        try:
            # 优先从实时数据获取
            if exchange in self.websocket_collectors:
                collector = self.websocket_collectors[exchange]
                latest_data = collector.get_latest_data(symbol)
                if latest_data and 'price' in latest_data:
                    return float(latest_data['price'])
            
            # 从API获取
            ticker_data = await self.get_ticker_data(symbol, exchange)
            return float(ticker_data.get('price', 0))
            
        except Exception as e:
            logger.error(f"获取最新价格失败: {e}")
            return 0.0
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        if key not in self.cache_ttl:
            return False
        
        return datetime.now() < self.cache_ttl[key]
    
    def _set_cache(self, key: str, value: Any, ttl: int):
        """设置缓存"""
        self.cache[key] = value
        self.cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)
    
    def clear_cache(self, pattern: str = None):
        """清除缓存"""
        if pattern:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.cache_ttl.pop(key, None)
            logger.info(f"清除缓存模式: {pattern}")
        else:
            self.cache.clear()
            self.cache_ttl.clear()
            logger.info("清除所有缓存")
    
    async def get_supported_symbols(self, exchange: str = "binance") -> List[str]:
        """
        获取支持的交易对
        
        Args:
            exchange: 交易所
            
        Returns:
            交易对列表
        """
        try:
            if exchange not in self.exchange_clients:
                raise ValueError(f"不支持的交易所: {exchange}")
            
            client = self.exchange_clients[exchange]
            symbols = await client.get_exchange_info()
            
            logger.info(f"获取支持的交易对: {exchange} {len(symbols)}个")
            return symbols
            
        except Exception as e:
            logger.error(f"获取支持的交易对失败: {e}")
            return []
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'initialized': self._initialized,
            'exchange_clients': list(self.exchange_clients.keys()),
            'websocket_collectors': list(self.websocket_collectors.keys()),
            'cache_size': len(self.cache),
            'collection_status': {}
        }
        
        # WebSocket收集器状态
        for exchange, collector in self.websocket_collectors.items():
            status['collection_status'][exchange] = {
                'is_collecting': collector.is_collecting(),
                'symbols': list(collector.get_collecting_symbols())
            }
        
        return status


# 数据库模型（简化版）
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

class KlineData:
    """K线数据模型（简化版，实际应该使用SQLAlchemy模型）"""
    pass  # 这里应该使用实际的SQLAlchemy模型定义


# 全局数据管理器实例
data_manager = DataManager()


async def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    if not data_manager._initialized:
        await data_manager.initialize()
    return data_manager


# 便捷函数
async def get_klines(symbol: str, **kwargs) -> pd.DataFrame:
    """便捷的K线数据获取函数"""
    dm = await get_data_manager()
    return await dm.get_kline_data(symbol, **kwargs)


async def get_latest_price(symbol: str, exchange: str = "binance") -> float:
    """便捷的获取最新价格函数"""
    dm = await get_data_manager()
    return await dm.get_latest_price(symbol, exchange)


if __name__ == "__main__":
    # 测试数据管理器
    async def test_data_manager():
        dm = DataManager()
        await dm.initialize()
        
        # 测试获取K线数据
        try:
            klines = await dm.get_kline_data("BTCUSDT", "1h", 10)
            print(f"获取K线数据成功: {len(klines)}条")
            print(klines.head())
        except Exception as e:
            print(f"获取K线数据失败: {e}")
        
        # 测试获取行情数据
        try:
            ticker = await dm.get_ticker_data("BTCUSDT")
            print(f"获取行情数据成功: {ticker.get('price')}")
        except Exception as e:
            print(f"获取行情数据失败: {e}")
        
        # 测试系统状态
        status = await dm.get_system_status()
        print(f"系统状态: {status}")
    
    asyncio.run(test_data_manager())