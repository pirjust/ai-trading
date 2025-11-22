"""
AI机器学习策略
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from strategies.base_strategy import BaseStrategy
from ..core.strategy_naming import StrategyNameGenerator

class MachineLearningStrategy(BaseStrategy):
    """机器学习策略基类"""
    
    def __init__(self, name: str = None, config: Dict = None):
        # 自动生成策略名称（如果没有提供）
        if name is None:
            name = StrategyNameGenerator.generate_strategy_name(
                algorithm_type="xgboost",
                symbols=config.get('symbols', []) if config else [],
                time_period=config.get('time_period', '1h') if config else '1h',
                include_random=True
            )
        
        super().__init__(name, config or {})
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.target_column = "target"
    
    async def initialize(self):
        """初始化策略"""
        # 这里应该加载训练好的模型
        print(f"机器学习策略初始化: {self.name}")
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """创建特征"""
        features = data.copy()
        
        # 技术指标特征
        features['rsi'] = self.calculate_rsi(data)
        features['macd'] = self.calculate_macd(data)
        features['ma_5'] = data['close'].rolling(5).mean()
        features['ma_20'] = data['close'].rolling(20).mean()
        features['volume_ma'] = data['volume'].rolling(10).mean()
        
        # 价格变动特征
        features['price_change'] = data['close'].pct_change()
        features['volatility'] = data['close'].rolling(20).std()
        
        # 时间特征
        features['hour'] = data.index.hour
        features['day_of_week'] = data.index.dayofweek
        
        return features
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.Series:
        """计算MACD"""
        fast_ema = data['close'].ewm(span=12).mean()
        slow_ema = data['close'].ewm(span=26).mean()
        return fast_ema - slow_ema
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < 50:  # 需要足够的数据
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 创建特征
        features = self.create_features(data)
        latest_features = features.iloc[-1:].dropna()
        
        if len(latest_features) == 0:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 标准化特征
        features_scaled = self.scaler.transform(latest_features[self.feature_columns])
        
        # 预测（这里简化处理，实际应该使用训练好的模型）
        prediction = np.random.choice([-1, 0, 1])  # 随机预测
        confidence = np.random.uniform(0.5, 0.9)  # 随机置信度
        
        signal_map = {-1: "sell", 0: "hold", 1: "buy"}
        
        return {
            "signal": signal_map[prediction],
            "strength": abs(prediction),
            "confidence": confidence
        }
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.7:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"]
            }
        
        return None

class LSTMPredictionStrategy(BaseStrategy):
    """LSTM预测策略"""
    
    def __init__(self, name: str = None, config: Dict = None):
        # 自动生成策略名称（如果没有提供）
        if name is None:
            name = StrategyNameGenerator.generate_strategy_name(
                algorithm_type="lstm",
                symbols=config.get('symbols', []) if config else [],
                time_period=config.get('time_period', '1h') if config else '1h',
                include_random=True
            )
        
        super().__init__(name, config or {})
        self.sequence_length = config.get('sequence_length', 60)
        self.prediction_horizon = config.get('prediction_horizon', 5)
    
    async def initialize(self):
        """初始化策略"""
        print(f"LSTM策略初始化: 序列长度={self.sequence_length}, 预测周期={self.prediction_horizon}")
    
    def prepare_sequences(self, data: pd.DataFrame) -> np.ndarray:
        """准备序列数据"""
        # 这里应该实现LSTM序列准备
        sequences = []
        prices = data['close'].values
        
        for i in range(len(prices) - self.sequence_length):
            sequence = prices[i:i + self.sequence_length]
            sequences.append(sequence)
        
        return np.array(sequences)
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.sequence_length + self.prediction_horizon:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        # 简化的LSTM预测（实际应该使用训练好的模型）
        current_price = data['close'].iloc[-1]
        
        # 模拟预测结果
        predicted_change = np.random.normal(0, 0.02)  # 随机价格变动
        predicted_price = current_price * (1 + predicted_change)
        
        # 生成信号
        if predicted_change > 0.01:  # 预测上涨超过1%
            strength = min(abs(predicted_change) / 0.05, 1.0)  # 标准化强度
            confidence = np.random.uniform(0.6, 0.9)
            return {"signal": "buy", "strength": strength, "confidence": confidence}
        elif predicted_change < -0.01:  # 预测下跌超过1%
            strength = min(abs(predicted_change) / 0.05, 1.0)
            confidence = np.random.uniform(0.6, 0.9)
            return {"signal": "sell", "strength": strength, "confidence": confidence}
        else:
            return {"signal": "hold", "strength": 0, "confidence": 0}
    
    async def execute_strategy(self, data: pd.DataFrame) -> Optional[Dict]:
        """执行策略"""
        signal = await self.generate_signal(data)
        
        if signal["signal"] != "hold" and signal["confidence"] > 0.7:
            return {
                "action": signal["signal"],
                "symbol": self.config.get('symbol', 'BTCUSDT'),
                "quantity": self.config.get('quantity', 0.01),
                "signal_strength": signal["strength"],
                "confidence": signal["confidence"],
                "predicted_change": signal.get('predicted_change', 0)
            }
        
        return None

class ReinforcementLearningStrategy(BaseStrategy):
    """强化学习策略"""
    
    def __init__(self, name: str = None, config: Dict = None):
        # 自动生成策略名称（如果没有提供）
        if name is None:
            name = StrategyNameGenerator.generate_strategy_name(
                algorithm_type="rl",
                symbols=config.get('symbols', []) if config else [],
                market_type=config.get('market_type', 'futures') if config else 'futures',
                include_random=True
            )
        
        super().__init__(name, config or {})
        self.state_size = config.get('state_size', 10)
        self.action_space = ["buy", "sell", "hold"]
        self.epsilon = config.get('epsilon', 0.1)  # 探索率
    
    async def initialize(self):
        """初始化策略"""
        print(f"强化学习策略初始化: 状态大小={self.state_size}, 探索率={self.epsilon}")
    
    def get_state(self, data: pd.DataFrame) -> np.ndarray:
        """获取状态"""
        if len(data) < self.state_size:
            return np.zeros(self.state_size)
        
        recent_data = data.tail(self.state_size)
        
        # 状态特征
        price_features = [
            recent_data['close'].pct_change().mean(),
            recent_data['close'].pct_change().std(),
            recent_data['volume'].pct_change().mean()
        ]
        
        # 技术指标
        rsi = self.calculate_rsi(recent_data).iloc[-1] if len(recent_data) >= 14 else 50
        macd = self.calculate_macd(recent_data).iloc[-1] if len(recent_data) >= 26 else 0
        
        state = np.array(price_features + [rsi, macd])
        
        # 填充到固定长度
        if len(state) < self.state_size:
            state = np.pad(state, (0, self.state_size - len(state)))
        
        return state[:self.state_size]
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """计算RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.Series:
        """计算MACD"""
        fast_ema = data['close'].ewm(span=12).mean()
        slow_ema = data['close'].ewm(span=26).mean()
        return fast_ema - slow_ema
    
    async def generate_signal(self, data: pd.DataFrame) -> Dict:
        """生成交易信号"""
        if len(data) < self.state_size:
            return {"signal": "hold", "strength": 0, "confidence": 0}
        
        state = self.get_state(data)
        
        # 简化版的Q-learning决策（实际应该使用训练好的模型）
        if np.random.random() < self.epsilon:
            # 探索：随机选择动作
            action = np.random.choice(self.action_space)
            confidence = 0.5
        else:
            # 利用：基于状态的决策
            # 这里简化处理，实际应该使用Q值函数
            price_trend = data['close'].pct_change().tail(5).mean()
            
            if price_trend > 0.002:  # 近期上涨趋势
                action = "buy"
            elif price_trend < -0.002:  # 近期下跌趋势
                action = "sell"
            else:
                action = "hold"
            
            confidence = min(abs(price_trend) / 0.01, 0.9)
        
        strength = 0.5 if action == "hold" else 1.0
        
        return {
            "signal": action,
            "strength": strength,
            "confidence": confidence,
            "state": state.tolist()
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
                "rl_state": signal["state"]
            }
        
        return None