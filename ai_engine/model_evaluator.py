"""
模型评估和优化模块
用于评估AI模型性能并优化超参数
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
import optuna
from functools import partial


@dataclass
class EvaluationMetrics:
    """模型评估指标"""
    mse: float
    mae: float
    rmse: float
    r2: float
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        metrics = {
            'mse': self.mse,
            'mae': self.mae,
            'rmse': self.rmse,
            'r2': self.r2
        }
        if self.accuracy is not None:
            metrics['accuracy'] = self.accuracy
        if self.precision is not None:
            metrics['precision'] = self.precision
        if self.recall is not None:
            metrics['recall'] = self.recall
        if self.f1 is not None:
            metrics['f1'] = self.f1
        return metrics


class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, task_type: str = "regression"):
        self.task_type = task_type
        self.metrics_history = []
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> EvaluationMetrics:
        """
        计算评估指标
        
        Args:
            y_true: 真实值
            y_pred: 预测值
            
        Returns:
            评估指标对象
        """
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        if self.task_type == "classification":
            # 分类任务指标
            y_pred_class = (y_pred > 0.5).astype(int)
            accuracy = accuracy_score(y_true, y_pred_class)
            precision = precision_score(y_true, y_pred_class, average='weighted')
            recall = recall_score(y_true, y_pred_class, average='weighted')
            f1 = f1_score(y_true, y_pred_class, average='weighted')
            
            return EvaluationMetrics(mse, mae, rmse, r2, accuracy, precision, recall, f1)
        else:
            # 回归任务指标
            return EvaluationMetrics(mse, mae, rmse, r2)
    
    def cross_validate(self, model, X: np.ndarray, y: np.ndarray, 
                      cv_splits: int = 5, scoring: str = "neg_mean_squared_error") -> Dict[str, Any]:
        """
        交叉验证
        
        Args:
            model: 模型对象
            X: 特征数据
            y: 目标数据
            cv_splits: 交叉验证折数
            scoring: 评分指标
            
        Returns:
            交叉验证结果
        """
        # 时间序列交叉验证
        tscv = TimeSeriesSplit(n_splits=cv_splits)
        
        scores = cross_val_score(model, X, y, cv=tscv, scoring=scoring)
        
        return {
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'scores': scores.tolist()
        }
    
    def plot_predictions(self, y_true: np.ndarray, y_pred: np.ndarray, title: str = "预测结果对比"):
        """
        绘制预测结果对比图
        
        Args:
            y_true: 真实值
            y_pred: 预测值
            title: 图表标题
        """
        plt.figure(figsize=(12, 6))
        
        # 预测结果对比
        plt.subplot(1, 2, 1)
        plt.plot(y_true, label='真实值', alpha=0.7)
        plt.plot(y_pred, label='预测值', alpha=0.7)
        plt.title(f'{title} - 预测对比')
        plt.legend()
        
        # 残差图
        plt.subplot(1, 2, 2)
        residuals = y_true - y_pred
        plt.scatter(y_pred, residuals, alpha=0.5)
        plt.axhline(y=0, color='red', linestyle='--')
        plt.title('残差分析')
        plt.xlabel('预测值')
        plt.ylabel('残差')
        
        plt.tight_layout()
        plt.show()
    
    def plot_feature_importance(self, model, feature_names: List[str]):
        """
        绘制特征重要性图
        
        Args:
            model: 模型对象
            feature_names: 特征名称列表
        """
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(10, 8))
            plt.title("特征重要性")
            plt.bar(range(len(importances)), importances[indices])
            plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
            plt.tight_layout()
            plt.show()


class HyperparameterOptimizer:
    """超参数优化器"""
    
    def __init__(self, model_class, task_type: str = "regression"):
        self.model_class = model_class
        self.task_type = task_type
        self.study = None
    
    def objective(self, trial, X_train: np.ndarray, y_train: np.ndarray, 
                 X_val: np.ndarray, y_val: np.ndarray) -> float:
        """
        优化目标函数
        
        Args:
            trial: Optuna trial对象
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            
        Returns:
            优化得分
        """
        # 定义超参数搜索空间
        if self.model_class.__name__ == 'LSTM':
            params = {
                'hidden_size': trial.suggest_int('hidden_size', 32, 256),
                'num_layers': trial.suggest_int('num_layers', 1, 4),
                'dropout': trial.suggest_float('dropout', 0.1, 0.5),
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128])
            }
        elif self.model_class.__name__ == 'XGBRegressor':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
            }
        else:
            # 默认参数搜索空间
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-1, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 50, 500)
            }
        
        # 创建模型并训练
        model = self.model_class(**params)
        model.fit(X_train, y_train)
        
        # 预测并计算得分
        y_pred = model.predict(X_val)
        
        if self.task_type == "regression":
            score = -mean_squared_error(y_val, y_pred)  # 负MSE（最大化）
        else:
            score = accuracy_score(y_val, (y_pred > 0.5).astype(int))
        
        return score
    
    def optimize(self, X_train: np.ndarray, y_train: np.ndarray, 
                X_val: np.ndarray, y_val: np.ndarray, 
                n_trials: int = 100) -> Dict[str, Any]:
        """
        执行超参数优化
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            n_trials: 优化试验次数
            
        Returns:
            优化结果
        """
        objective_func = partial(self.objective, X_train=X_train, y_train=y_train, 
                               X_val=X_val, y_val=y_val)
        
        self.study = optuna.create_study(direction='maximize')
        self.study.optimize(objective_func, n_trials=n_trials)
        
        return {
            'best_params': self.study.best_params,
            'best_value': self.study.best_value,
            'trials': len(self.study.trials)
        }
    
    def plot_optimization_history(self):
        """绘制优化历史"""
        if self.study is not None:
            optuna.visualization.plot_optimization_history(self.study)
            plt.show()
    
    def plot_parallel_coordinate(self):
        """绘制平行坐标图"""
        if self.study is not None:
            optuna.visualization.plot_parallel_coordinate(self.study)
            plt.show()


class ModelEnsemble:
    """模型集成器"""
    
    def __init__(self, models: List[Any], weights: List[float] = None):
        self.models = models
        self.weights = weights if weights else [1.0 / len(models)] * len(models)
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """训练集成模型"""
        for model in self.models:
            model.fit(X, y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """集成预测"""
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(X)
            predictions.append(pred * weight)
        
        return np.sum(predictions, axis=0)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """集成概率预测（分类任务）"""
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            if hasattr(model, 'predict_proba'):
                pred = model.predict_proba(X)[:, 1]  # 正类概率
            else:
                pred = model.predict(X)
            predictions.append(pred * weight)
        
        return np.sum(predictions, axis=0)


class TradingStrategyEvaluator:
    """交易策略评估器"""
    
    def __init__(self, initial_capital: float = 10000.0, transaction_fee: float = 0.001):
        self.initial_capital = initial_capital
        self.transaction_fee = transaction_fee
    
    def evaluate_strategy(self, signals: np.ndarray, prices: np.ndarray, 
                         returns: np.ndarray) -> Dict[str, float]:
        """
        评估交易策略
        
        Args:
            signals: 交易信号（-1, 0, 1）
            prices: 价格序列
            returns: 收益率序列
            
        Returns:
            策略评估指标
        """
        # 计算策略收益
        strategy_returns = signals * returns
        
        # 累计收益
        cumulative_returns = np.cumprod(1 + strategy_returns)
        
        # 计算夏普比率
        sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        
        # 最大回撤
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (running_max - cumulative_returns) / running_max
        max_drawdown = np.max(drawdown)
        
        # 胜率
        winning_trades = np.sum(strategy_returns > 0)
        total_trades = np.sum(signals != 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': cumulative_returns[-1] - 1,
            'annual_return': np.mean(strategy_returns) * 252,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades
        }