"""
特征工程和数据预处理模块
用于提取、转换和选择交易数据的特征
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression
import talib


@dataclass
class FeatureConfig:
    """特征工程配置"""
    # 技术指标配置
    indicators: List[str] = None
    # 时间窗口配置
    windows: List[int] = None
    # 特征选择配置
    feature_selection_method: str = "kbest"
    n_features: int = 50
    # 标准化配置
    scaler: str = "standard"
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = ["SMA", "EMA", "RSI", "MACD", "BBANDS", "ATR", "STOCH"]
        if self.windows is None:
            self.windows = [5, 10, 20, 30, 60]


class FeatureEngineer:
    """特征工程器"""
    
    def __init__(self, config: FeatureConfig = None):
        self.config = config or FeatureConfig()
        self.scaler = None
        self.feature_selector = None
        self.feature_names = []
    
    def extract_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取技术指标特征
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            包含技术指标的DataFrame
        """
        features_df = df.copy()
        
        # 基础价格特征
        features_df['price_change'] = df['close'].pct_change()
        features_df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        features_df['volume_change'] = df['volume'].pct_change()
        
        # 移动平均线
        for window in self.config.windows:
            features_df[f'SMA_{window}'] = talib.SMA(df['close'], timeperiod=window)
            features_df[f'EMA_{window}'] = talib.EMA(df['close'], timeperiod=window)
            features_df[f'SMA_ratio_{window}'] = df['close'] / features_df[f'SMA_{window}']
        
        # RSI指标
        for window in [6, 14, 24]:
            features_df[f'RSI_{window}'] = talib.RSI(df['close'], timeperiod=window)
        
        # MACD指标
        macd, macd_signal, macd_hist = talib.MACD(df['close'])
        features_df['MACD'] = macd
        features_df['MACD_signal'] = macd_signal
        features_df['MACD_hist'] = macd_hist
        
        # 布林带
        for window in [20, 50]:
            upper, middle, lower = talib.BBANDS(df['close'], timeperiod=window)
            features_df[f'BB_upper_{window}'] = upper
            features_df[f'BB_middle_{window}'] = middle
            features_df[f'BB_lower_{window}'] = lower
            features_df[f'BB_position_{window}'] = (df['close'] - lower) / (upper - lower)
        
        # 随机指标
        slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'])
        features_df['STOCH_k'] = slowk
        features_df['STOCH_d'] = slowd
        
        # ATR指标
        features_df['ATR'] = talib.ATR(df['high'], df['low'], df['close'])
        
        # 成交量指标
        features_df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
        features_df['volume_ratio'] = df['volume'] / features_df['volume_sma']
        
        # 价格波动率
        for window in [5, 10, 20]:
            features_df[f'volatility_{window}'] = df['close'].pct_change().rolling(window).std()
        
        return features_df
    
    def create_lag_features(self, df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
        """
        创建滞后特征
        
        Args:
            df: 原始DataFrame
            columns: 需要创建滞后特征的列
            lags: 滞后阶数列表
            
        Returns:
            包含滞后特征的DataFrame
        """
        features_df = df.copy()
        
        for col in columns:
            for lag in lags:
                features_df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        return features_df
    
    def create_rolling_features(self, df: pd.DataFrame, columns: List[str], windows: List[int]) -> pd.DataFrame:
        """
        创建滚动统计特征
        
        Args:
            df: 原始DataFrame
            columns: 需要创建滚动特征的列
            windows: 滚动窗口列表
            
        Returns:
            包含滚动特征的DataFrame
        """
        features_df = df.copy()
        
        for col in columns:
            for window in windows:
                # 滚动均值
                features_df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window).mean()
                # 滚动标准差
                features_df[f'{col}_rolling_std_{window}'] = df[col].rolling(window).std()
                # 滚动最小值
                features_df[f'{col}_rolling_min_{window}'] = df[col].rolling(window).min()
                # 滚动最大值
                features_df[f'{col}_rolling_max_{window}'] = df[col].rolling(window).max()
                # 滚动分位数
                features_df[f'{col}_rolling_quantile_25_{window}'] = df[col].rolling(window).quantile(0.25)
                features_df[f'{col}_rolling_quantile_75_{window}'] = df[col].rolling(window).quantile(0.75)
        
        return features_df
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建时间相关特征
        
        Args:
            df: 原始DataFrame
            
        Returns:
            包含时间特征的DataFrame
        """
        features_df = df.copy()
        
        if 'timestamp' in df.columns:
            # 转换为时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 时间特征
            features_df['hour'] = df['timestamp'].dt.hour
            features_df['day_of_week'] = df['timestamp'].dt.dayofweek
            features_df['day_of_month'] = df['timestamp'].dt.day
            features_df['month'] = df['timestamp'].dt.month
            
            # 周期性特征
            features_df['hour_sin'] = np.sin(2 * np.pi * features_df['hour'] / 24)
            features_df['hour_cos'] = np.cos(2 * np.pi * features_df['hour'] / 24)
            features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_week'] / 7)
            features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_week'] / 7)
        
        return features_df
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series = None) -> pd.DataFrame:
        """
        拟合特征工程器并转换数据
        
        Args:
            X: 特征DataFrame
            y: 目标变量
            
        Returns:
            转换后的特征DataFrame
        """
        # 提取技术指标
        X_processed = self.extract_technical_indicators(X)
        
        # 创建滞后特征
        price_columns = ['open', 'high', 'low', 'close', 'volume']
        X_processed = self.create_lag_features(X_processed, price_columns, [1, 2, 3, 5, 10])
        
        # 创建滚动特征
        X_processed = self.create_rolling_features(X_processed, ['close', 'volume'], [5, 10, 20])
        
        # 创建时间特征
        X_processed = self.create_time_features(X_processed)
        
        # 记录特征名称
        self.feature_names = [col for col in X_processed.columns if col not in X.columns]
        
        # 标准化
        if self.config.scaler == "standard":
            self.scaler = StandardScaler()
        else:
            self.scaler = MinMaxScaler()
        
        # 选择数值型列进行标准化
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        X_processed[numeric_cols] = self.scaler.fit_transform(X_processed[numeric_cols])
        
        # 特征选择
        if y is not None and self.config.feature_selection_method == "kbest":
            self.feature_selector = SelectKBest(score_func=f_regression, k=self.config.n_features)
            X_selected = self.feature_selector.fit_transform(X_processed[numeric_cols], y)
            
            # 获取选中的特征名称
            selected_indices = self.feature_selector.get_support(indices=True)
            self.selected_features = [numeric_cols[i] for i in selected_indices]
            
            # 创建包含选中特征的DataFrame
            X_processed = X_processed[self.selected_features]
        
        return X_processed
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        转换新数据
        
        Args:
            X: 新特征DataFrame
            
        Returns:
            转换后的特征DataFrame
        """
        if self.scaler is None:
            raise ValueError("FeatureEngineer must be fitted before transformation")
        
        # 应用相同的特征工程流程
        X_processed = self.extract_technical_indicators(X)
        X_processed = self.create_lag_features(X_processed, ['open', 'high', 'low', 'close', 'volume'], [1, 2, 3, 5, 10])
        X_processed = self.create_rolling_features(X_processed, ['close', 'volume'], [5, 10, 20])
        X_processed = self.create_time_features(X_processed)
        
        # 标准化
        numeric_cols = X_processed.select_dtypes(include=[np.number]).columns
        X_processed[numeric_cols] = self.scaler.transform(X_processed[numeric_cols])
        
        # 特征选择
        if self.feature_selector is not None:
            X_selected = self.feature_selector.transform(X_processed[numeric_cols])
            X_processed = pd.DataFrame(X_selected, columns=self.selected_features)
        
        return X_processed
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性
        
        Returns:
            特征重要性字典
        """
        if self.feature_selector is None:
            return {}
        
        feature_scores = dict(zip(self.selected_features, self.feature_selector.scores_))
        return dict(sorted(feature_scores.items(), key=lambda x: x[1], reverse=True))
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称"""
        if self.feature_selector is not None:
            return self.selected_features
        return self.feature_names


class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            df: 原始数据
            
        Returns:
            清洗后的数据
        """
        # 移除重复行
        df_cleaned = df.drop_duplicates()
        
        # 处理缺失值
        df_cleaned = df_cleaned.fillna(method='ffill').fillna(method='bfill')
        
        # 移除异常值（使用IQR方法）
        numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df_cleaned[col].quantile(0.25)
            Q3 = df_cleaned[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 使用边界值替换异常值
            df_cleaned[col] = np.where(df_cleaned[col] < lower_bound, lower_bound, df_cleaned[col])
            df_cleaned[col] = np.where(df_cleaned[col] > upper_bound, upper_bound, df_cleaned[col])
        
        return df_cleaned
    
    def prepare_training_data(self, df: pd.DataFrame, target_col: str = 'price_change', 
                            lookback_window: int = 60, forecast_horizon: int = 1) -> tuple:
        """
        准备训练数据
        
        Args:
            df: 原始数据
            target_col: 目标变量列
            lookback_window: 回看窗口大小
            forecast_horizon: 预测时间步长
            
        Returns:
            特征矩阵和目标向量
        """
        # 数据清洗
        df_cleaned = self.clean_data(df)
        
        # 特征工程
        X = df_cleaned.drop(columns=[target_col], errors='ignore')
        y = df_cleaned[target_col].shift(-forecast_horizon)  # 未来预测
        
        # 移除最后forecast_horizon行（没有对应的目标值）
        X = X.iloc[:-forecast_horizon]
        y = y.iloc[:-forecast_horizon]
        
        # 应用特征工程
        X_features = self.feature_engineer.fit_transform(X, y)
        
        # 创建序列数据
        X_sequences, y_sequences = [], []
        
        for i in range(len(X_features) - lookback_window):
            X_sequences.append(X_features.iloc[i:i+lookback_window].values)
            y_sequences.append(y.iloc[i+lookback_window])
        
        return np.array(X_sequences), np.array(y_sequences)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        return self.feature_engineer.get_feature_importance()