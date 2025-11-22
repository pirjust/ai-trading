"""
技术分析策略
基于经典技术指标的交易策略
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from strategies.base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    """移动平均策略"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.short_period = config.get('short_period', 10)
        self.long_period = config.get('long_period', 30)
        self.signal_threshold = config.get('signal_threshold', 0.02)
    
    async def initialize(self):
        """初始化策略"""
        print(f"移动平均策略初始化: 短期={self.short_period}, 长期={self.long_period}")
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线"""
        result = data.copy()
        
        # 计算短期和长期移动平均
        result[f'ma_{self.short_period}'] = data['close'].rolling(self.short_period).mean()
        result[f'ma_{self.long_period}'] = data['close'].rolling(self.long_period).mean()
        
        # 计算移动平均线的差值和比率
        result['ma_diff'] = result[f'ma_{self.short_period}'] - result[f'ma_{self.long_period}']
        result['ma_ratio'] = result[f'ma_{self.short_period}'] / result[f'ma_{self.long_period}']
        
        return result
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信号"""
        if len(data) < self.long_period:
            return pd.Series(0, index=data.index)
        
        # 计算移动平均
        ma_data = self.calculate_moving_averages(data)
        
        # 计算信号
        signals = pd.Series(0, index=data.index)
        
        # 金叉买入信号
        signals[(ma_data['ma_diff'] > 0) & (ma_data['ma_diff'].shift(1) <= 0)] = 1
        
        # 死叉卖出信号
        signals[(ma_data['ma_diff'] < 0) & (ma_data['ma_diff'].shift(1) >= 0)] = -1
        
        return signals
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.long_period:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 计算移动平均
        ma_data = self.calculate_moving_averages(data)
        
        # 获取最新数据
        latest = ma_data.iloc[-1]
        previous = ma_data.iloc[-2]
        
        # 当前价格与移动平均的关系
        current_price = latest['close']
        short_ma = latest[f'ma_{self.short_period}']
        long_ma = latest[f'ma_{self.long_period}']
        
        # 计算信号强度
        ma_ratio = latest['ma_ratio']
        strength = abs(ma_ratio - 1.0) * 10  # 标准化强度
        
        # 判断交易信号
        if latest['ma_diff'] > 0 and previous['ma_diff'] <= 0:
            # 金叉买入
            signal = "buy"
            confidence = min(strength, 0.9)
        elif latest['ma_diff'] < 0 and previous['ma_diff'] >= 0:
            # 死叉卖出
            signal = "sell"
            confidence = min(strength, 0.9)
        elif ma_ratio > 1 + self.signal_threshold:
            # 短期均线显著高于长期均线，买入
            signal = "buy"
            confidence = min((ma_ratio - 1) * 5, 0.8)
        elif ma_ratio < 1 - self.signal_threshold:
            # 短期均线显著低于长期均线，卖出
            signal = "sell"
            confidence = min((1 - ma_ratio) * 5, 0.8)
        else:
            # 持有观望
            signal = "hold"
            confidence = 0.0
        
        return {
            "signal": signal,
            "strength": strength,
            "confidence": confidence,
            "ma_short": short_ma,
            "ma_long": long_ma,
            "ma_ratio": ma_ratio
        }
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.6:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"],
                "ma_short": signal["ma_short"],
                "ma_long": signal["ma_long"],
                "ma_ratio": signal["ma_ratio"]
            }
        
        return None


class RSIStrategy(BaseStrategy):
    """RSI策略"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.rsi_period = config.get('rsi_period', 14)
        self.oversold = config.get('oversold', 30)
        self.overbought = config.get('overbought', 70)
    
    async def initialize(self):
        """初始化策略"""
        print(f"RSI策略初始化: 周期={self.rsi_period}, 超卖={self.oversold}, 超买={self.overbought}")
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.rsi_period:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 计算RSI
        rsi = self.calculate_rsi(data, self.rsi_period)
        current_rsi = rsi.iloc[-1]
        previous_rsi = rsi.iloc[-2]
        
        # 计算信号强度
        if current_rsi < self.oversold:
            strength = (self.oversold - current_rsi) / self.oversold
            signal = "buy"
        elif current_rsi > self.overbought:
            strength = (current_rsi - self.overbought) / (100 - self.overbought)
            signal = "sell"
        else:
            strength = 0.0
            signal = "hold"
        
        # 基于RSI变化的置信度
        rsi_change = abs(current_rsi - previous_rsi)
        confidence = min(strength + rsi_change / 10, 0.9)
        
        return {
            "signal": signal,
            "strength": strength,
            "confidence": confidence,
            "rsi": current_rsi,
            "rsi_change": rsi_change
        }
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.6:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"],
                "rsi": signal["rsi"],
                "rsi_change": signal["rsi_change"]
            }
        
        return None


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.std_dev = config.get('std_dev', 2)
    
    async def initialize(self):
        """初始化策略"""
        print(f"布林带策略初始化: 周期={self.period}, 标准差={self.std_dev}")
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算布林带"""
        result = data.copy()
        
        # 计算中轨（简单移动平均）
        result['bb_middle'] = data['close'].rolling(self.period).mean()
        
        # 计算标准差
        std = data['close'].rolling(self.period).std()
        
        # 计算上下轨
        result['bb_upper'] = result['bb_middle'] + (std * self.std_dev)
        result['bb_lower'] = result['bb_middle'] - (std * self.std_dev)
        
        # 计算布林带位置
        result['bb_position'] = (data['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
        
        return result
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.period:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 计算布林带
        bb_data = self.calculate_bollinger_bands(data)
        
        # 获取最新数据
        latest = bb_data.iloc[-1]
        
        current_price = latest['close']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_position = latest['bb_position']
        
        # 判断交易信号
        if bb_position < 0.1:  # 价格接近下轨，超卖
            signal = "buy"
            strength = (0.1 - bb_position) * 10
        elif bb_position > 0.9:  # 价格接近上轨，超买
            signal = "sell"
            strength = (bb_position - 0.9) * 10
        else:
            signal = "hold"
            strength = 0.0
        
        # 基于布林带宽度的置信度
        bb_width = (bb_upper - bb_lower) / bb_middle
        confidence = min(strength * bb_width, 0.9)
        
        return {
            "signal": signal,
            "strength": strength,
            "confidence": confidence,
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "bb_position": bb_position,
            "bb_width": bb_width
        }
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.6:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"],
                "bb_upper": signal["bb_upper"],
                "bb_middle": signal["bb_middle"],
                "bb_lower": signal["bb_lower"],
                "bb_position": signal["bb_position"]
            }
        
        return None


class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 26)
        self.signal_period = config.get('signal_period', 9)
    
    async def initialize(self):
        """初始化策略"""
        print(f"MACD策略初始化: 快线={self.fast_period}, 慢线={self.slow_period}, 信号线={self.signal_period}")
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD"""
        result = data.copy()
        
        # 计算快慢线EMA
        fast_ema = data['close'].ewm(span=self.fast_period).mean()
        slow_ema = data['close'].ewm(span=self.slow_period).mean()
        
        # 计算MACD线
        result['macd'] = fast_ema - slow_ema
        
        # 计算信号线
        result['macd_signal'] = result['macd'].ewm(span=self.signal_period).mean()
        
        # 计算MACD柱状图
        result['macd_histogram'] = result['macd'] - result['macd_signal']
        
        return result
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.slow_period:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 计算MACD
        macd_data = self.calculate_macd(data)
        
        # 获取最新数据
        latest = macd_data.iloc[-1]
        previous = macd_data.iloc[-2]
        
        current_macd = latest['macd']
        current_signal = latest['macd_signal']
        current_histogram = latest['macd_histogram']
        
        previous_histogram = previous['macd_histogram']
        
        # 判断交易信号
        if current_histogram > 0 and previous_histogram <= 0:
            # MACD柱状图从负转正，买入信号
            signal = "buy"
            strength = min(abs(current_histogram) * 100, 1.0)
        elif current_histogram < 0 and previous_histogram >= 0:
            # MACD柱状图从正转负，卖出信号
            signal = "sell"
            strength = min(abs(current_histogram) * 100, 1.0)
        elif current_histogram > 0:
            # 柱状图为正，多头趋势
            signal = "buy" if current_macd > current_signal else "hold"
            strength = min(abs(current_histogram) * 50, 0.8)
        else:
            # 柱状图为负，空头趋势
            signal = "sell" if current_macd < current_signal else "hold"
            strength = min(abs(current_histogram) * 50, 0.8)
        
        if signal == "hold":
            strength = 0.0
        
        # 基于MACD线距离的置信度
        macd_distance = abs(current_macd - current_signal)
        confidence = min(strength + macd_distance * 1000, 0.9)
        
        return {
            "signal": signal,
            "strength": strength,
            "confidence": confidence,
            "macd": current_macd,
            "macd_signal": current_signal,
            "macd_histogram": current_histogram,
            "macd_distance": macd_distance
        }
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.6:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"],
                "macd": signal["macd"],
                "macd_signal": signal["macd_signal"],
                "macd_histogram": signal["macd_histogram"]
            }
        
        return None