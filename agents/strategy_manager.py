"""
策略管理器 - 统一管理所有AI交易策略
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import logging

from strategies.base_strategy import BaseStrategy
from strategies.ai_strategies import MachineLearningStrategy, LSTMPredictionStrategy, ReinforcementLearningStrategy
from strategies.technical_strategies import MovingAverageStrategy, RSIStrategy
from data.exchange_client import ExchangeClientFactory, ExchangeType

logger = logging.getLogger(__name__)


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.exchange_clients: Dict[str, Any] = {}
        self.is_running = False
        self.data_buffer = {}
        self.performance_tracker = {}
        
    async def add_strategy(self, strategy_name: str, strategy_type: str, 
                         config: Dict[str, Any], exchange_type: ExchangeType = ExchangeType.BINANCE):
        """添加策略"""
        try:
            # 创建策略实例
            if strategy_type == "machine_learning":
                strategy = MachineLearningStrategy(strategy_name, config)
            elif strategy_type == "lstm_prediction":
                strategy = LSTMPredictionStrategy(strategy_name, config)
            elif strategy_type == "reinforcement_learning":
                strategy = ReinforcementLearningStrategy(strategy_name, config)
            elif strategy_type == "moving_average":
                strategy = MovingAverageStrategy(strategy_name, config)
            elif strategy_type == "rsi":
                strategy = RSIStrategy(strategy_name, config)
            else:
                raise ValueError(f"不支持的策略类型: {strategy_type}")
            
            # 初始化策略
            await strategy.initialize()
            
            # 连接交易所
            if exchange_type.value not in self.exchange_clients:
                client = ExchangeClientFactory.create_client(exchange_type, sandbox=True)
                await client.connect()
                self.exchange_clients[exchange_type.value] = client
            
            # 添加策略到管理器
            self.strategies[strategy_name] = {
                'strategy': strategy,
                'exchange_type': exchange_type,
                'config': config,
                'is_active': False,
                'last_signal_time': 0,
                'total_signals': 0,
                'successful_trades': 0
            }
            
            logger.info(f"策略 {strategy_name} 添加成功")
            return True
            
        except Exception as e:
            logger.error(f"添加策略失败: {e}")
            return False
    
    async def start_strategy(self, strategy_name: str):
        """启动策略"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        try:
            strategy_info = self.strategies[strategy_name]
            strategy = strategy_info['strategy']
            
            await strategy.start()
            strategy_info['is_active'] = True
            
            logger.info(f"策略 {strategy_name} 已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动策略失败: {e}")
            return False
    
    async def stop_strategy(self, strategy_name: str):
        """停止策略"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        try:
            strategy_info = self.strategies[strategy_name]
            strategy = strategy_info['strategy']
            
            await strategy.stop()
            strategy_info['is_active'] = False
            
            logger.info(f"策略 {strategy_name} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止策略失败: {e}")
            return False
    
    async def update_data(self, symbol: str, data: pd.DataFrame):
        """更新市场数据"""
        self.data_buffer[symbol] = data
        
        # 检查所有相关策略
        for strategy_name, strategy_info in self.strategies.items():
            if strategy_info['is_active']:
                strategy = strategy_info['strategy']
                config = strategy_info['config']
                
                # 检查策略是否关注此交易对
                if config.get('symbol') == symbol or symbol in config.get('symbols', [symbol]):
                    await self._execute_strategy(strategy_name, strategy, data)
    
    async def _execute_strategy(self, strategy_name: str, strategy: BaseStrategy, data: pd.DataFrame):
        """执行策略"""
        try:
            # 生成交易信号
            signal = await strategy.generate_signal(data)
            
            if signal.get('confidence', 0) > 0.7:  # 置信度阈值
                # 执行策略
                action = await strategy.execute_strategy(data)
                
                if action:
                    strategy_info = self.strategies[strategy_name]
                    strategy_info['last_signal_time'] = time.time()
                    strategy_info['total_signals'] += 1
                    
                    # 执行交易
                    await self._execute_trade(strategy_name, action)
                    
                    logger.info(f"策略 {strategy_name} 执行交易: {action}")
        
        except Exception as e:
            logger.error(f"执行策略 {strategy_name} 失败: {e}")
    
    async def _execute_trade(self, strategy_name: str, action: Dict[str, Any]):
        """执行交易"""
        try:
            strategy_info = self.strategies[strategy_name]
            exchange_type = strategy_info['exchange_type']
            
            if exchange_type.value in self.exchange_clients:
                client = self.exchange_clients[exchange_type.value]
                
                # 创建订单
                from data.exchange_client import OrderSide, OrderType
                
                order = await client.create_order(
                    symbol=action['symbol'],
                    side=OrderSide.BUY if action['action'] == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=action['quantity']
                )
                
                # 记录交易结果
                self._record_trade_result(strategy_name, order, action)
                
                logger.info(f"策略 {strategy_name} 订单创建成功: {order.order_id}")
        
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
    
    def _record_trade_result(self, strategy_name: str, order: Any, action: Dict[str, Any]):
        """记录交易结果"""
        if strategy_name not in self.performance_tracker:
            self.performance_tracker[strategy_name] = {
                'trades': [],
                'total_pnl': 0.0,
                'win_rate': 0.0
            }
        
        tracker = self.performance_tracker[strategy_name]
        
        trade_record = {
            'timestamp': datetime.now(),
            'order_id': order.order_id,
            'action': action['action'],
            'symbol': action['symbol'],
            'quantity': action['quantity'],
            'signal_strength': action.get('signal_strength', 0),
            'confidence': action.get('confidence', 0)
        }
        
        tracker['trades'].append(trade_record)
    
    def get_strategy_status(self, strategy_name: str = None) -> Dict[str, Any]:
        """获取策略状态"""
        if strategy_name:
            if strategy_name not in self.strategies:
                return {}
            return self._get_single_strategy_status(strategy_name)
        else:
            return {
                name: self._get_single_strategy_status(name)
                for name in self.strategies.keys()
            }
    
    def _get_single_strategy_status(self, strategy_name: str) -> Dict[str, Any]:
        """获取单个策略状态"""
        strategy_info = self.strategies[strategy_name]
        
        status = {
            'strategy_name': strategy_name,
            'is_active': strategy_info['is_active'],
            'last_signal_time': strategy_info['last_signal_time'],
            'total_signals': strategy_info['total_signals'],
            'successful_trades': strategy_info['successful_trades'],
            'config': strategy_info['config']
        }
        
        # 添加性能数据
        if strategy_name in self.performance_tracker:
            performance = self.performance_tracker[strategy_name]
            status.update({
                'total_trades': len(performance['trades']),
                'total_pnl': performance['total_pnl'],
                'win_rate': performance['win_rate']
            })
        
        return status
    
    async def get_active_strategies(self) -> List[str]:
        """获取活跃策略列表"""
        return [
            name for name, info in self.strategies.items() 
            if info['is_active']
        ]
    
    async def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        try:
            # 停止策略
            strategy_info = self.strategies[strategy_name]
            if strategy_info['is_active']:
                await self.stop_strategy(strategy_name)
            
            # 从管理器中移除
            del self.strategies[strategy_name]
            
            # 清理性能数据
            if strategy_name in self.performance_tracker:
                del self.performance_tracker[strategy_name]
            
            logger.info(f"策略 {strategy_name} 已移除")
            return True
            
        except Exception as e:
            logger.error(f"移除策略失败: {e}")
            return False
    
    async def shutdown(self):
        """关闭策略管理器"""
        # 停止所有策略
        for strategy_name in list(self.strategies.keys()):
            await self.stop_strategy(strategy_name)
        
        # 断开所有交易所连接
        for client in self.exchange_clients.values():
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"断开交易所连接失败: {e}")
        
        self.exchange_clients.clear()
        self.is_running = False
        logger.info("策略管理器已关闭")


# 策略工厂
class StrategyFactory:
    """策略工厂类"""
    
    @staticmethod
    def create_strategy_config(strategy_type: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建策略配置"""
        # 基础配置
        config = base_config.copy()
        
        # 根据策略类型生成策略名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config['strategy_name'] = f"{strategy_type}_{timestamp}"
        
        # 策略特定配置
        if strategy_type == "machine_learning":
            config.update({
                'model_type': 'random_forest',
                'retrain_interval': 3600,  # 1小时重训练
                'confidence_threshold': 0.7
            })
        elif strategy_type == "lstm_prediction":
            config.update({
                'sequence_length': 60,
                'prediction_horizon': 5,
                'model_path': f"models/lstm_{timestamp}.pkl"
            })
        elif strategy_type == "reinforcement_learning":
            config.update({
                'state_size': 20,
                'epsilon': 0.1,
                'learning_rate': 0.001
            })
        elif strategy_type == "moving_average":
            config.update({
                'short_period': 10,
                'long_period': 30,
                'signal_threshold': 0.02
            })
        elif strategy_type == "rsi":
            config.update({
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70
            })
        
        return config
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """获取可用策略列表"""
        return [
            "machine_learning",
            "lstm_prediction", 
            "reinforcement_learning",
            "moving_average",
            "rsi"
        ]


# 使用示例
async def example_usage():
    """使用示例"""
    manager = StrategyManager()
    
    try:
        # 创建策略配置
        config = StrategyFactory.create_strategy_config("machine_learning", {
            'symbol': 'BTCUSDT',
            'quantity': 0.001,
            'confidence_threshold': 0.8
        })
        
        # 添加策略
        await manager.add_strategy("ml_strategy", "machine_learning", config)
        
        # 启动策略
        await manager.start_strategy("ml_strategy")
        
        # 模拟市场数据更新
        import numpy as np
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'open': np.random.uniform(45000, 50000, 100),
            'high': np.random.uniform(50000, 52000, 100),
            'low': np.random.uniform(43000, 45000, 100),
            'close': np.random.uniform(45000, 50000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        # 更新数据
        await manager.update_data('BTCUSDT', data)
        
        # 获取策略状态
        status = manager.get_strategy_status("ml_strategy")
        print(f"策略状态: {status}")
        
        # 关闭管理器
        await manager.shutdown()
        
    except Exception as e:
        print(f"示例执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())