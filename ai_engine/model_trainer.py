"""
AI模型训练和预测模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import warnings
warnings.filterwarnings('ignore')

class TradingDataset(Dataset):
    """交易数据集类"""
    
    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.targets = torch.LongTensor(targets)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

class LSTMPredictor(nn.Module):
    """LSTM价格预测模型"""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int):
        super(LSTMPredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        # LSTM前向传播
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.dropout(out[:, -1, :])  # 取最后一个时间步
        out = self.fc(out)
        return out

class MLModelTrainer:
    """机器学习模型训练器"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.model_configs = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1
            }
        }
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """创建技术指标特征"""
        features = data.copy()
        
        # 价格相关特征
        features['price_change'] = data['close'].pct_change()
        features['high_low_ratio'] = data['high'] / data['low']
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(10).mean()
        
        # 移动平均特征
        for window in [5, 10, 20, 50]:
            features[f'ma_{window}'] = data['close'].rolling(window).mean()
            features[f'ma_ratio_{window}'] = data['close'] / features[f'ma_{window}']
        
        # 波动率特征
        features['volatility_5'] = data['close'].rolling(5).std()
        features['volatility_20'] = data['close'].rolling(20).std()
        features['volatility_ratio'] = features['volatility_5'] / features['volatility_20']
        
        # RSI指标
        features['rsi'] = self._calculate_rsi(data)
        
        # MACD指标
        macd_data = self._calculate_macd(data)
        features['macd'] = macd_data['macd']
        features['macd_signal'] = macd_data['signal']
        features['macd_histogram'] = macd_data['histogram']
        
        # 布林带
        bb_data = self._calculate_bollinger_bands(data)
        features['bb_upper'] = bb_data['upper']
        features['bb_lower'] = bb_data['lower']
        features['bb_position'] = (data['close'] - bb_data['lower']) / (bb_data['upper'] - bb_data['lower'])
        
        # 时间特征
        if hasattr(data.index, 'hour'):
            features['hour'] = data.index.hour
            features['day_of_week'] = data.index.dayofweek
            features['is_weekend'] = data.index.dayofweek.isin([5, 6]).astype(int)
        
        return features.dropna()
    
    def prepare_training_data(self, data: pd.DataFrame, target_col: str = 'target', 
                             sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        # 创建特征
        features_df = self.create_features(data)
        
        # 选择特征列
        feature_columns = [col for col in features_df.columns if col != target_col]
        self.feature_names = feature_columns
        
        # 提取特征和目标
        X = features_df[feature_columns].values
        y = features_df[target_col].values if target_col in features_df.columns else None
        
        # 标准化特征
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['standard'] = scaler
        
        # 准备序列数据（用于LSTM）
        if sequence_length > 1:
            X_sequences, y_sequences = self._create_sequences(X_scaled, y, sequence_length)
            return X_sequences, y_sequences
        
        return X_scaled, y
    
    def train_classification_model(self, model_type: str, X: np.ndarray, y: np.ndarray) -> Dict:
        """训练分类模型"""
        # 分割数据集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 选择模型
        if model_type == 'random_forest':
            model = RandomForestClassifier(**self.model_configs['random_forest'])
        elif model_type == 'gradient_boosting':
            model = GradientBoostingClassifier(**self.model_configs['gradient_boosting'])
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 训练模型
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # 保存模型
        self.models[model_type] = model
        
        return {
            'model_type': model_type,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'feature_importance': dict(zip(self.feature_names, model.feature_importances_))
        }
    
    def train_lstm_model(self, X_sequences: np.ndarray, y: np.ndarray, 
                        input_size: int, hidden_size: int = 64, num_layers: int = 2,
                        epochs: int = 100, batch_size: int = 32) -> Dict:
        """训练LSTM模型"""
        # 创建数据集
        dataset = TradingDataset(X_sequences, y)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 创建模型
        model = LSTMPredictor(input_size, hidden_size, num_layers, output_size=3)  # 3类：涨、跌、平
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # 训练循环
        model.train()
        train_losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            for batch_features, batch_targets in dataloader:
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_targets)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            train_losses.append(epoch_loss / len(dataloader))
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {epoch_loss / len(dataloader):.4f}")
        
        # 保存模型
        self.models['lstm'] = model
        
        return {
            'model_type': 'lstm',
            'final_loss': train_losses[-1],
            'training_losses': train_losses,
            'model_architecture': str(model)
        }
    
    def predict(self, model_type: str, features: np.ndarray) -> np.ndarray:
        """使用模型进行预测"""
        if model_type not in self.models:
            raise ValueError(f"模型未训练: {model_type}")
        
        model = self.models[model_type]
        
        if model_type == 'lstm':
            model.eval()
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features)
                predictions = model(features_tensor)
                return torch.argmax(predictions, dim=1).numpy()
        else:
            return model.predict(features)
    
    def save_model(self, model_type: str, filepath: str):
        """保存模型"""
        if model_type not in self.models:
            raise ValueError(f"模型未训练: {model_type}")
        
        if model_type == 'lstm':
            torch.save({
                'model_state_dict': self.models[model_type].state_dict(),
                'feature_names': self.feature_names,
                'scaler': self.scalers.get('standard')
            }, filepath)
        else:
            joblib.dump({
                'model': self.models[model_type],
                'feature_names': self.feature_names,
                'scaler': self.scalers.get('standard')
            }, filepath)
    
    def load_model(self, model_type: str, filepath: str):
        """加载模型"""
        if model_type == 'lstm':
            checkpoint = torch.load(filepath)
            input_size = len(checkpoint['feature_names'])
            model = LSTMPredictor(input_size, 64, 2, 3)
            model.load_state_dict(checkpoint['model_state_dict'])
            self.models[model_type] = model
        else:
            checkpoint = joblib.load(filepath)
            self.models[model_type] = checkpoint['model']
        
        self.feature_names = checkpoint['feature_names']
        if 'scaler' in checkpoint:
            self.scalers['standard'] = checkpoint['scaler']
    
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
        histogram = macd - signal
        
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20) -> Dict:
        """计算布林带"""
        sma = data['close'].rolling(period).mean()
        std = data['close'].rolling(period).std()
        
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return {'upper': upper_band, 'lower': lower_band, 'sma': sma}
    
    def _create_sequences(self, data: np.ndarray, targets: np.ndarray, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """创建序列数据"""
        sequences = []
        target_sequences = []
        
        for i in range(len(data) - sequence_length):
            sequences.append(data[i:i + sequence_length])
            target_sequences.append(targets[i + sequence_length])
        
        return np.array(sequences), np.array(target_sequences)