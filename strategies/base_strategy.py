"""
策略基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd

class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.is_active = False
        self.performance_data = []
    
    @abstractmethod
    async def initialize(self):
        """初始化策略"""
        pass
    
    @abstractmethod
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        pass
    
    @abstractmethod
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        pass
    
    async def start(self):
        """启动策略"""
        self.is_active = True
        await self.initialize()
    
    async def stop(self):
        """停止策略"""
        self.is_active = False
    
    def update_config(self, new_config: Dict):
        """更新策略配置"""
        self.config.update(new_config)
    
    def record_performance(self, performance: Dict):
        """记录策略表现"""
        self.performance_data.append(performance)
    
    def get_performance_summary(self) -> Dict:
        """获取策略表现摘要"""
        if not self.performance_data:
            return {}
        
        # 计算基本统计信息
        total_trades = len(self.performance_data)
        winning_trades = len([p for p in self.performance_data if p.get('profit', 0) > 0])
        total_profit = sum(p.get('profit', 0) for p in self.performance_data)
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
            "total_profit": total_profit,
            "avg_profit_per_trade": total_profit / total_trades if total_trades > 0 else 0
        }