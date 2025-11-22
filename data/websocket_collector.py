"""
WebSocket数据采集器 - 支持币安、欧意等交易所
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

try:
    import websockets
except ImportError:
    websockets = None

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class WebSocketCollector(BaseCollector):
    """WebSocket实时数据采集器"""
    
    def __init__(self, exchange: str, symbols: List[str], websocket_url: str):
        super().__init__(exchange, symbols)
        self.websocket_url = websocket_url
        self.websocket = None
        self.subscription_map = {
            "binance": self._subscribe_binance,
            "okx": self._subscribe_okx
        }
    
    async def _subscribe_binance(self):
        """订阅币安WebSocket"""
        streams = [f"{symbol.lower()}@ticker" for symbol in self.symbols]
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": 1
        }
        await self.websocket.send(json.dumps(subscribe_msg))
    
    async def _subscribe_okx(self):
        """订阅欧意WebSocket"""
        args = []
        for symbol in self.symbols:
            args.append({
                "channel": "tickers",
                "instId": symbol
            })
        
        subscribe_msg = {
            "op": "subscribe",
            "args": args
        }
        await self.websocket.send(json.dumps(subscribe_msg))
    
    async def start(self):
        """启动WebSocket连接"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_running = True
            
            # 订阅数据
            if self.exchange in self.subscription_map:
                await self.subscription_map[self.exchange]()
            
            # 开始接收数据
            asyncio.create_task(self._receive_data())
            
            logger.info(f"WebSocket连接已启动: {self.exchange}")
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            self.is_running = False
    
    async def _receive_data(self):
        """接收WebSocket数据"""
        while self.is_running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # 处理不同交易所的数据格式
                processed_data = self._process_data(data)
                if processed_data:
                    self.notify_callbacks(processed_data)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.error("WebSocket连接已关闭")
                break
            except Exception as e:
                logger.error(f"处理WebSocket数据错误: {e}")
    
    def _process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理不同交易所的数据格式"""
        if self.exchange == "binance":
            return self._process_binance_data(data)
        elif self.exchange == "okx":
            return self._process_okx_data(data)
        return None
    
    def _process_binance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理币安数据"""
        if "e" in data and data["e"] == "24hrTicker":
            return {
                "exchange": "binance",
                "symbol": data["s"],
                "price": float(data["c"]),
                "volume": float(data["v"]),
                "price_change": float(data["p"]),
                "price_change_percent": float(data["P"]),
                "timestamp": data["E"]
            }
        return None
    
    def _process_okx_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理欧意数据"""
        if "data" in data and len(data["data"]) > 0:
            ticker = data["data"][0]
            return {
                "exchange": "okx",
                "symbol": ticker["instId"],
                "price": float(ticker["last"]),
                "volume": float(ticker["vol24h"]),
                "price_change": float(ticker["sodUtc0"]),
                "price_change_percent": float(ticker["sodUtc0"]),
                "timestamp": ticker["ts"]
            }
        return None
    
    async def stop(self):
        """停止WebSocket连接"""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("WebSocket连接已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取采集器状态"""
        return {
            "exchange": self.exchange,
            "symbols": self.symbols,
            "is_running": self.is_running,
            "websocket_url": self.websocket_url
        }