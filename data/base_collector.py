"""
基础数据采集器
定义数据采集的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """数据采集器基类"""
    
    def __init__(self, exchange: str, symbols: List[str]):
        self.exchange = exchange
        self.symbols = symbols
        self.is_running = False
        self.callbacks = []
        self.collected_data = {}
        
    @abstractmethod
    async def start(self):
        """启动数据采集"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止数据采集"""
        pass
    
    def add_callback(self, callback):
        """添加数据回调函数"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """移除数据回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def notify_callbacks(self, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"数据回调失败: {e}")
    
    def get_collected_data(self) -> Dict[str, Any]:
        """获取采集的数据"""
        return self.collected_data.copy()