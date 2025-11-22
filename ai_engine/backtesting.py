"""
策略回测和验证系统
用于评估AI交易策略的历史表现
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from enum import Enum


class PositionType(Enum):
    """仓位类型"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Trade:
    """交易记录"""
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_type: PositionType
    quantity: float
    pnl: Optional[float] = None
    
    def calculate_pnl(self, current_price: float = None) -> float:
        """计算盈亏"""
        if self.pnl is not None:
            return self.pnl
        
        if current_price is not None and self.exit_price is None:
            # 未平仓交易
            if self.position_type == PositionType.LONG:
                return (current_price - self.entry_price) * self.quantity
            else:
                return (self.entry_price - current_price) * self.quantity
        elif self.exit_price is not None:
            # 已平仓交易
            if self.position_type == PositionType.LONG:
                return (self.exit_price - self.entry_price) * self.quantity
            else:
                return (self.entry_price - self.exit_price) * self.quantity
        
        return 0.0


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    avg_trade_return: float
    trades: List[Trade]
    equity_curve: pd.Series
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'profit_factor': self.profit_factor,
            'avg_trade_return': self.avg_trade_return
        }


class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000.0, transaction_fee: float = 0.001,
                 slippage: float = 0.0005, position_limit: float = 0.1):
        self.initial_capital = initial_capital
        self.transaction_fee = transaction_fee
        self.slippage = slippage
        self.position_limit = position_limit  # 单笔交易最大仓位比例
        self.trades = []
        self.current_position = None
    
    def calculate_position_size(self, price: float, signal_strength: float) -> float:
        """
        计算仓位大小
        
        Args:
            price: 当前价格
            signal_strength: 信号强度
            
        Returns:
            仓位数量
        """
        max_position_value = self.initial_capital * self.position_limit
        position_size = (max_position_value * abs(signal_strength)) / price
        return position_size
    
    def execute_trade(self, timestamp: datetime, price: float, signal: float, 
                     signal_strength: float = 1.0) -> Optional[Trade]:
        """
        执行交易
        
        Args:
            timestamp: 交易时间
            price: 交易价格
            signal: 交易信号（-1, 0, 1）
            signal_strength: 信号强度
            
        Returns:
            交易记录
        """
        # 应用滑点
        execution_price = price * (1 + self.slippage) if signal > 0 else price * (1 - self.slippage)
        
        # 平仓逻辑
        if self.current_position is not None:
            # 检查是否需要平仓
            if (signal == 0 and self.current_position.position_type != PositionType.FLAT) or \
               (signal > 0 and self.current_position.position_type == PositionType.SHORT) or \
               (signal < 0 and self.current_position.position_type == PositionType.LONG):
                
                # 平仓
                self.current_position.exit_time = timestamp
                self.current_position.exit_price = execution_price
                self.current_position.pnl = self.current_position.calculate_pnl()
                
                # 记录交易
                self.trades.append(self.current_position)
                
                # 重置当前仓位
                closed_trade = self.current_position
                self.current_position = None
                
                # 如果新信号要求开仓，继续执行开仓
                if signal != 0:
                    return self.execute_trade(timestamp, price, signal, signal_strength)
                
                return closed_trade
        
        # 开仓逻辑
        if signal != 0 and self.current_position is None:
            position_type = PositionType.LONG if signal > 0 else PositionType.SHORT
            quantity = self.calculate_position_size(execution_price, signal_strength)
            
            # 创建新交易
            self.current_position = Trade(
                entry_time=timestamp,
                exit_time=None,
                entry_price=execution_price,
                exit_price=None,
                position_type=position_type,
                quantity=quantity
            )
        
        return None
    
    def run_backtest(self, data: pd.DataFrame, signals: pd.Series, 
                    signal_strengths: pd.Series = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: 包含价格数据的DataFrame
            signals: 交易信号序列
            signal_strengths: 信号强度序列
            
        Returns:
            回测结果
        """
        if signal_strengths is None:
            signal_strengths = pd.Series(1.0, index=signals.index)
        
        # 重置状态
        self.trades = []
        self.current_position = None
        
        # 执行回测
        equity = [self.initial_capital]
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            price = row['close']
            signal = signals.loc[timestamp] if timestamp in signals.index else 0
            strength = signal_strengths.loc[timestamp] if timestamp in signal_strengths.index else 1.0
            
            # 执行交易
            trade = self.execute_trade(timestamp, price, signal, strength)
            
            # 计算当前权益
            current_equity = equity[-1]
            
            if self.current_position is not None:
                # 计算未平仓交易的浮动盈亏
                unrealized_pnl = self.current_position.calculate_pnl(price)
                current_equity = self.initial_capital + sum(trade.pnl for trade in self.trades if trade.pnl is not None) + unrealized_pnl
            else:
                current_equity = self.initial_capital + sum(trade.pnl for trade in self.trades if trade.pnl is not None)
            
            equity.append(current_equity)
        
        # 平仓所有未平仓交易
        if self.current_position is not None:
            last_timestamp = data.index[-1]
            last_price = data['close'].iloc[-1]
            self.current_position.exit_time = last_timestamp
            self.current_position.exit_price = last_price
            self.current_position.pnl = self.current_position.calculate_pnl()
            self.trades.append(self.current_position)
        
        # 计算回测指标
        equity_series = pd.Series(equity[1:], index=data.index)  # 移除初始值
        returns = equity_series.pct_change().dropna()
        
        # 总收益率
        total_return = (equity_series.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        trading_days = len(equity_series)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
        
        # 夏普比率
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # 最大回撤
        running_max = equity_series.expanding().max()
        drawdown = (running_max - equity_series) / running_max
        max_drawdown = drawdown.max()
        
        # 胜率
        winning_trades = [trade for trade in self.trades if trade.pnl and trade.pnl > 0]
        win_rate = len(winning_trades) / len(self.trades) if len(self.trades) > 0 else 0
        
        # 盈利因子
        total_profit = sum(trade.pnl for trade in self.trades if trade.pnl and trade.pnl > 0)
        total_loss = abs(sum(trade.pnl for trade in self.trades if trade.pnl and trade.pnl < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 平均交易收益率
        avg_trade_return = np.mean([trade.pnl / (trade.entry_price * trade.quantity) 
                                   for trade in self.trades if trade.pnl is not None]) if self.trades else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(self.trades),
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            trades=self.trades,
            equity_curve=equity_series
        )
    
    def plot_backtest_results(self, result: BacktestResult, benchmark: pd.Series = None):
        """
        绘制回测结果
        
        Args:
            result: 回测结果
            benchmark: 基准收益率序列
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 权益曲线
        axes[0, 0].plot(result.equity_curve.index, result.equity_curve.values, label='策略权益')
        if benchmark is not None:
            benchmark_normalized = benchmark / benchmark.iloc[0] * result.initial_capital
            axes[0, 0].plot(benchmark_normalized.index, benchmark_normalized.values, 
                           label='基准权益', alpha=0.7)
        axes[0, 0].set_title('权益曲线')
        axes[0, 0].legend()
        
        # 回撤曲线
        running_max = result.equity_curve.expanding().max()
        drawdown = (running_max - result.equity_curve) / running_max
        axes[0, 1].fill_between(drawdown.index, drawdown.values, alpha=0.3)
        axes[0, 1].set_title('回撤曲线')
        axes[0, 1].set_ylabel('回撤比例')
        
        # 收益率分布
        returns = result.equity_curve.pct_change().dropna()
        axes[1, 0].hist(returns, bins=50, alpha=0.7)
        axes[1, 0].axvline(returns.mean(), color='red', linestyle='--', label=f'均值: {returns.mean():.4f}')
        axes[1, 0].set_title('收益率分布')
        axes[1, 0].legend()
        
        # 月度收益率热力图
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_returns_matrix = monthly_returns.groupby([monthly_returns.index.year, 
                                                         monthly_returns.index.month]).mean()
        
        # 创建月度热力图数据
        years = sorted(monthly_returns.index.year.unique())
        months = range(1, 13)
        
        heatmap_data = pd.DataFrame(index=years, columns=months)
        for year in years:
            for month in months:
                mask = (monthly_returns.index.year == year) & (monthly_returns.index.month == month)
                if mask.any():
                    heatmap_data.loc[year, month] = monthly_returns[mask].iloc[0]
        
        heatmap_data = heatmap_data.fillna(0)
        
        im = axes[1, 1].imshow(heatmap_data.values, cmap='RdYlGn', aspect='auto')
        axes[1, 1].set_xticks(range(len(months)))
        axes[1, 1].set_xticklabels([f'{m}' for m in months])
        axes[1, 1].set_yticks(range(len(years)))
        axes[1, 1].set_yticklabels([f'{y}' for y in years])
        axes[1, 1].set_title('月度收益率热力图')
        plt.colorbar(im, ax=axes[1, 1])
        
        plt.tight_layout()
        plt.show()


class WalkForwardOptimizer:
    """Walk-Forward优化器"""
    
    def __init__(self, train_period: int = 252, test_period: int = 63, step_size: int = 21):
        self.train_period = train_period
        self.test_period = test_period
        self.step_size = step_size
    
    def generate_windows(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        生成训练和测试窗口
        
        Args:
            data: 完整数据集
            
        Returns:
            训练和测试窗口列表
        """
        windows = []
        total_periods = len(data)
        
        for i in range(0, total_periods - self.train_period - self.test_period, self.step_size):
            train_end = i + self.train_period
            test_end = train_end + self.test_period
            
            train_data = data.iloc[i:train_end]
            test_data = data.iloc[train_end:test_end]
            
            windows.append((train_data, test_data))
        
        return windows
    
    def optimize_strategy(self, data: pd.DataFrame, strategy_func, 
                         param_space: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化策略参数
        
        Args:
            data: 完整数据集
            strategy_func: 策略函数
            param_space: 参数空间
            
        Returns:
            优化结果
        """
        windows = self.generate_windows(data)
        best_params = None
        best_performance = float('-inf')
        
        performance_history = []
        
        for train_data, test_data in windows:
            # 在训练集上优化参数
            # 这里可以使用网格搜索或贝叶斯优化
            # 简化实现：使用固定参数
            params = param_space
            
            # 在测试集上评估策略
            signals = strategy_func(test_data, params)
            backtester = Backtester()
            result = backtester.run_backtest(test_data, signals)
            
            performance = result.sharpe_ratio  # 使用夏普比率作为评估指标
            performance_history.append(performance)
            
            if performance > best_performance:
                best_performance = performance
                best_params = params
        
        return {
            'best_params': best_params,
            'best_performance': best_performance,
            'performance_history': performance_history,
            'total_windows': len(windows)
        }