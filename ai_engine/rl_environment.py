"""
强化学习环境模拟器
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class TradingEnvironment(gym.Env):
    """加密货币交易强化学习环境"""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000.0, 
                 transaction_fee: float = 0.001, max_position: float = 0.1):
        super(TradingEnvironment, self).__init__()
        
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.max_position = max_position
        
        # 动作空间：[-1, 1] 表示卖/买的比例
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        
        # 状态空间：价格特征 + 账户状态
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, 
                                          shape=(20,), dtype=np.float32)
        
        # 重置环境
        self.reset()
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None):
        """重置环境状态"""
        super().reset(seed=seed)
        
        # 重置交易状态
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0.0
        self.total_value = self.initial_balance
        self.transactions = []
        self.done = False
        
        # 计算初始状态
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """执行一步交易"""
        # 检查是否结束
        if self.done or self.current_step >= len(self.data) - 1:
            self.done = True
            observation = self._get_observation()
            return observation, 0.0, True, False, self._get_info()
        
        # 获取当前价格
        current_price = self.data.iloc[self.current_step]['close']
        
        # 执行交易动作
        reward = self._execute_trade(action[0], current_price)
        
        # 移动到下一步
        self.current_step += 1
        
        # 更新总价值
        self.total_value = self.balance + self.position * current_price
        
        # 检查是否结束
        if self.current_step >= len(self.data) - 1:
            self.done = True
        
        # 获取新的状态和信息
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, self.done, False, info
    
    def _execute_trade(self, action: float, current_price: float) -> float:
        """执行交易"""
        # 计算目标仓位（基于动作）
        target_position = action * self.max_position * self.total_value / current_price
        
        # 计算仓位变化
        position_change = target_position - self.position
        
        # 计算交易成本
        transaction_cost = abs(position_change) * current_price * self.transaction_fee
        
        # 检查资金是否足够
        if position_change > 0:  # 买入
            required_cash = position_change * current_price + transaction_cost
            if required_cash > self.balance:
                # 资金不足，调整交易量
                max_buyable = (self.balance - transaction_cost) / current_price
                position_change = min(position_change, max_buyable)
                transaction_cost = position_change * current_price * self.transaction_fee
        else:  # 卖出
            if abs(position_change) > self.position:
                # 卖出量超过持仓，调整
                position_change = -self.position
                transaction_cost = abs(position_change) * current_price * self.transaction_fee
        
        # 执行交易
        if position_change != 0:
            # 更新仓位
            self.position += position_change
            
            # 更新资金
            self.balance -= position_change * current_price
            self.balance -= transaction_cost
            
            # 记录交易
            self.transactions.append({
                'step': self.current_step,
                'action': 'buy' if position_change > 0 else 'sell',
                'quantity': abs(position_change),
                'price': current_price,
                'fee': transaction_cost
            })
        
        # 计算奖励
        reward = self._calculate_reward(position_change, current_price)
        
        return reward
    
    def _calculate_reward(self, position_change: float, current_price: float) -> float:
        """计算奖励"""
        # 基础奖励：价值变化
        if self.current_step == 0:
            return 0.0
        
        previous_value = self._get_previous_total_value()
        current_value = self.total_value
        
        # 价值变化奖励
        value_change_reward = (current_value - previous_value) / self.initial_balance
        
        # 交易惩罚（鼓励减少交易频率）
        trade_penalty = -0.001 if position_change != 0 else 0.0
        
        # 风险惩罚（鼓励控制风险）
        position_ratio = abs(self.position) * current_price / self.total_value
        risk_penalty = -0.01 * (position_ratio ** 2)
        
        # 总奖励
        total_reward = value_change_reward + trade_penalty + risk_penalty
        
        return total_reward
    
    def _get_previous_total_value(self) -> float:
        """获取上一步的总价值"""
        if self.current_step == 0:
            return self.initial_balance
        
        previous_price = self.data.iloc[self.current_step - 1]['close']
        return self.balance + self.position * previous_price
    
    def _get_observation(self) -> np.ndarray:
        """获取观察状态"""
        if self.current_step >= len(self.data):
            return np.zeros(self.observation_space.shape)
        
        # 价格特征
        current_data = self.data.iloc[self.current_step]
        
        # 技术指标
        price_features = self._calculate_technical_indicators(self.current_step)
        
        # 账户状态
        account_features = np.array([
            self.balance / self.initial_balance,  # 标准化余额
            self.position,  # 当前持仓
            self.total_value / self.initial_balance,  # 标准化总价值
            len(self.transactions) / 100.0  # 交易频率
        ])
        
        # 组合特征
        observation = np.concatenate([price_features, account_features])
        
        # 确保特征数量匹配
        if len(observation) < self.observation_space.shape[0]:
            observation = np.pad(observation, (0, self.observation_space.shape[0] - len(observation)))
        
        return observation[:self.observation_space.shape[0]]
    
    def _calculate_technical_indicators(self, step: int) -> np.ndarray:
        """计算技术指标"""
        if step < 20:  # 需要足够的数据计算指标
            return np.zeros(16)
        
        window_data = self.data.iloc[max(0, step-50):step+1]
        
        features = []
        
        # 价格变动特征
        price_changes = window_data['close'].pct_change().dropna()
        features.extend([
            price_changes.mean(),  # 平均变动
            price_changes.std(),   # 波动率
            price_changes.skew(), # 偏度
            price_changes.kurt()   # 峰度
        ])
        
        # 移动平均特征
        for window in [5, 10, 20]:
            ma = window_data['close'].rolling(window).mean()
            current_ma = ma.iloc[-1] if not pd.isna(ma.iloc[-1]) else window_data['close'].iloc[-1]
            features.append(current_ma / window_data['close'].iloc[-1])
        
        # RSI特征
        rsi = self._calculate_rsi(window_data)
        features.append(rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50)
        
        # MACD特征
        macd_data = self._calculate_macd(window_data)
        features.extend([
            macd_data['macd'].iloc[-1] if not pd.isna(macd_data['macd'].iloc[-1]) else 0,
            macd_data['signal'].iloc[-1] if not pd.isna(macd_data['signal'].iloc[-1]) else 0
        ])
        
        # 布林带特征
        bb_data = self._calculate_bollinger_bands(window_data)
        current_price = window_data['close'].iloc[-1]
        bb_position = (current_price - bb_data['lower'].iloc[-1]) / \
                     (bb_data['upper'].iloc[-1] - bb_data['lower'].iloc[-1])
        features.append(bb_position if not pd.isna(bb_position) else 0.5)
        
        # 成交量特征
        volume_ratio = window_data['volume'].iloc[-1] / window_data['volume'].rolling(10).mean().iloc[-1]
        features.append(volume_ratio if not pd.isna(volume_ratio) else 1.0)
        
        # 时间特征
        if hasattr(window_data.index, 'hour'):
            features.append(window_data.index.hour.iloc[-1] / 24.0)
            features.append(window_data.index.dayofweek.iloc[-1] / 6.0)
        else:
            features.extend([0.5, 0.5])
        
        return np.array(features)
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, data: pd.DataFrame) -> Dict:
        """计算MACD"""
        fast_ema = data['close'].ewm(span=12).mean()
        slow_ema = data['close'].ewm(span=26).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=9).mean()
        
        return {'macd': macd, 'signal': signal}
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20) -> Dict:
        """计算布林带"""
        sma = data['close'].rolling(period).mean()
        std = data['close'].rolling(period).std()
        
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return {'upper': upper_band, 'lower': lower_band}
    
    def _get_info(self) -> Dict:
        """获取环境信息"""
        return {
            'step': self.current_step,
            'balance': self.balance,
            'position': self.position,
            'total_value': self.total_value,
            'transactions_count': len(self.transactions),
            'done': self.done
        }
    
    def render(self, mode: str = 'human'):
        """渲染环境状态"""
        if mode == 'human':
            print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, "
                  f"Position: {self.position:.4f}, Total Value: {self.total_value:.2f}")

class RLAgent:
    """强化学习智能体"""
    
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        
        # 经验回放缓冲区
        self.memory = []
        self.batch_size = 32
        self.memory_size = 10000
        
        # 训练参数
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        
        # 模型初始化
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
    
    def _build_model(self):
        """构建神经网络模型"""
        import torch
        import torch.nn as nn
        
        class DQN(nn.Module):
            def __init__(self, state_size, action_size):
                super(DQN, self).__init__()
                self.fc1 = nn.Linear(state_size, 64)
                self.fc2 = nn.Linear(64, 64)
                self.fc3 = nn.Linear(64, 32)
                self.fc4 = nn.Linear(32, action_size)
                self.relu = nn.ReLU()
                self.dropout = nn.Dropout(0.2)
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.dropout(x)
                x = self.relu(self.fc3(x))
                x = self.fc4(x)
                return x
        
        return DQN(self.state_size, self.action_size)
    
    def update_target_model(self):
        """更新目标网络"""
        self.target_model.load_state_dict(self.model.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append((state, action, reward, next_state, done))
        
        # 限制内存大小
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
    
    def act(self, state):
        """选择动作"""
        import torch
        
        if np.random.random() <= self.epsilon:
            # 探索：随机动作
            return np.random.uniform(-1.0, 1.0, size=(1,))
        
        # 利用：使用模型预测
        self.model.eval()
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.model(state_tensor)
            action = q_values.mean(dim=1).numpy()
        
        return np.clip(action, -1.0, 1.0)
    
    def replay(self):
        """经验回放训练"""
        import torch
        import torch.optim as optim
        
        if len(self.memory) < self.batch_size:
            return
        
        # 随机采样批次
        batch = np.random.choice(len(self.memory), self.batch_size, replace=False)
        
        states = []
        targets = []
        
        for i in batch:
            state, action, reward, next_state, done = self.memory[i]
            
            # 计算目标Q值
            if done:
                target = reward
            else:
                self.target_model.eval()
                with torch.no_grad():
                    next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)
                    next_q_values = self.target_model(next_state_tensor)
                    target = reward + self.gamma * torch.max(next_q_values).item()
            
            # 计算当前Q值
            self.model.eval()
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                current_q_values = self.model(state_tensor)
            
            # 更新Q值
            target_f = current_q_values.clone()
            target_f[0][0] = target  # 简化处理
            
            states.append(state)
            targets.append(target_f)
        
        # 训练模型
        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()
        
        states_tensor = torch.FloatTensor(states)
        targets_tensor = torch.cat(targets)
        
        optimizer.zero_grad()
        outputs = self.model(states_tensor)
        loss = criterion(outputs, targets_tensor)
        loss.backward()
        optimizer.step()
        
        # 衰减探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def load(self, name):
        """加载模型"""
        import torch
        self.model.load_state_dict(torch.load(name))
        self.update_target_model()
    
    def save(self, name):
        """保存模型"""
        import torch
        torch.save(self.model.state_dict(), name)