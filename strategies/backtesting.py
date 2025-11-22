"""
策略回测模块
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class BacktestResult:
    """回测结果数据类"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    
    # 业绩指标
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    # 风险指标
    volatility: float
    var_95: float
    calmar_ratio: float
    
    # 详细数据
    trades: List[Dict]
    equity_curve: List[Dict]
    daily_returns: List[float]

class BacktestingEngine:
    """回测引擎"""
    
    def __init__(self):
        self.historical_data = {}
        self.commission_rate = 0.001  # 默认手续费率
        self.slippage_rate = 0.0005  # 默认滑点率
    
    async def run_backtest(
        self,
        strategy_class,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000,
        strategy_config: Dict = None
    ) -> BacktestResult:
        """运行回测"""
        
        # 加载历史数据
        data = await self._load_historical_data(symbol, start_date, end_date)
        if data.empty:
            raise ValueError(f"无法获取 {symbol} 的历史数据")
        
        # 初始化策略
        strategy = strategy_class(symbol, strategy_config or {})
        await strategy.initialize()
        
        # 运行回测
        results = await self._execute_backtest(strategy, data, initial_capital)
        
        # 计算性能指标
        performance = await self._calculate_performance_metrics(results)
        
        return BacktestResult(
            strategy_name=strategy.__class__.__name__,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            **performance
        )
    
    async def _execute_backtest(self, strategy, data: pd.DataFrame, initial_capital: float) -> Dict:
        """执行回测"""
        
        capital = initial_capital
        position = 0.0
        trades = []
        equity_curve = []
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            current_price = data.iloc[i]['close']
            
            # 生成交易信号
            signal = await strategy.generate_signal(current_data)
            
            # 执行交易
            if signal['signal'] != 'hold' and signal['confidence'] > 0.6:
                trade_result = await self._execute_trade(
                    signal, current_price, position, capital
                )
                
                if trade_result:
                    trades.append(trade_result)
                    position = trade_result['position_after']
                    capital = trade_result['capital_after']
            
            # 更新权益曲线
            portfolio_value = capital + position * current_price
            equity_curve.append({
                'timestamp': data.index[i],
                'equity': portfolio_value,
                'price': current_price
            })
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'initial_capital': initial_capital,
            'final_capital': capital + position * data.iloc[-1]['close']
        }
    
    async def _execute_trade(
        self,
        signal: Dict,
        price: float,
        position: float,
        capital: float
    ) -> Optional[Dict]:
        """执行交易"""
        
        # 计算手续费和滑点
        commission = price * self.commission_rate
        slippage = price * self.slippage_rate
        
        if signal['signal'] == 'buy' and capital > 0:
            # 计算可购买数量
            max_quantity = capital / (price + commission + slippage)
            quantity = min(max_quantity, signal.get('quantity', max_quantity))
            
            if quantity > 0:
                cost = quantity * (price + commission + slippage)
                
                return {
                    'action': 'buy',
                    'timestamp': datetime.now(),
                    'price': price,
                    'quantity': quantity,
                    'commission': commission,
                    'slippage': slippage,
                    'position_before': position,
                    'position_after': position + quantity,
                    'capital_before': capital,
                    'capital_after': capital - cost
                }
        
        elif signal['signal'] == 'sell' and position > 0:
            quantity = min(position, signal.get('quantity', position))
            
            if quantity > 0:
                revenue = quantity * (price - commission - slippage)
                
                return {
                    'action': 'sell',
                    'timestamp': datetime.now(),
                    'price': price,
                    'quantity': quantity,
                    'commission': commission,
                    'slippage': slippage,
                    'position_before': position,
                    'position_after': position - quantity,
                    'capital_before': capital,
                    'capital_after': capital + revenue
                }
        
        return None
    
    async def _calculate_performance_metrics(self, results: Dict) -> Dict:
        """计算性能指标"""
        
        trades = results['trades']
        equity_curve = results['equity_curve']
        
        if not trades:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'volatility': 0.0,
                'var_95': 0.0,
                'calmar_ratio': 0.0,
                'trades': [],
                'equity_curve': [],
                'daily_returns': []
            }
        
        # 计算总收益
        initial_capital = results['initial_capital']
        final_capital = results['final_capital']
        total_return = (final_capital - initial_capital) / initial_capital
        
        # 计算年化收益
        days = len(equity_curve) / 252  # 假设252个交易日
        annual_return = (1 + total_return) ** (1 / days) - 1 if days > 0 else 0
        
        # 计算夏普比率
        daily_returns = self._calculate_daily_returns(equity_curve)
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 计算胜率
        winning_trades = len([t for t in trades if t['capital_after'] > t['capital_before']])
        win_rate = winning_trades / len(trades) if trades else 0
        
        # 计算盈亏比
        profit_factor = self._calculate_profit_factor(trades)
        
        # 计算波动率
        volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0
        
        # 计算VaR
        var_95 = np.percentile(daily_returns, 5) if len(daily_returns) > 1 else 0
        
        # 计算Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': len(trades) - winning_trades,
            'volatility': volatility,
            'var_95': var_95,
            'calmar_ratio': calmar_ratio,
            'trades': trades,
            'equity_curve': equity_curve,
            'daily_returns': daily_returns
        }
    
    def _calculate_daily_returns(self, equity_curve: List[Dict]) -> List[float]:
        """计算日收益率"""
        if len(equity_curve) < 2:
            return []
        
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1]['equity']
            curr_equity = equity_curve[i]['equity']
            
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
        
        return returns
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        if len(equity_curve) < 2:
            return 0.0
        
        equity_values = [point['equity'] for point in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0.0
        
        for value in equity_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """计算盈亏比"""
        if not trades:
            return 0.0
        
        total_profit = 0.0
        total_loss = 0.0
        
        for trade in trades:
            pnl = trade['capital_after'] - trade['capital_before']
            if pnl > 0:
                total_profit += pnl
            else:
                total_loss += abs(pnl)
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        return total_profit / total_loss
    
    async def _load_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """加载历史数据"""
        # 这里应该从数据库或API获取历史数据
        # 暂时返回模拟数据
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='1H')
        n = len(date_range)
        
        # 生成模拟价格数据
        np.random.seed(42)
        prices = [100.0]
        
        for i in range(1, n):
            change = np.random.normal(0, 0.01)
            prices.append(prices[-1] * (1 + change))
        
        data = pd.DataFrame({
            'timestamp': date_range,
            'open': prices,
            'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n)
        })
        
        data.set_index('timestamp', inplace=True)
        return data

class BacktestManager:
    """回测管理器"""
    
    def __init__(self):
        self.backtesting_engine = BacktestingEngine()
        self.backtest_results = {}
    
    async def run_strategy_backtest(
        self,
        strategy_name: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        parameters: Dict
    ) -> BacktestResult:
        """运行策略回测"""
        
        # 根据策略名称获取策略类
        strategy_class = self._get_strategy_class(strategy_name)
        
        # 运行回测
        result = await self.backtesting_engine.run_backtest(
            strategy_class, symbol, start_date, end_date, parameters
        )
        
        # 保存结果
        self.backtest_results[strategy_name] = result
        
        return result
    
    def _get_strategy_class(self, strategy_name: str):
        """获取策略类"""
        # 这里应该根据策略名称返回对应的策略类
        from strategies.ai_strategies import MachineLearningStrategy, LSTMPredictionStrategy, ReinforcementLearningStrategy
        
        strategy_map = {
            'ml_strategy': MachineLearningStrategy,
            'lstm_strategy': LSTMPredictionStrategy,
            'rl_strategy': ReinforcementLearningStrategy
        }
        
        return strategy_map.get(strategy_name, MachineLearningStrategy)
    
    async def compare_strategies(
        self,
        strategies: List[str],
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        parameters: Dict
    ) -> Dict:
        """比较多个策略"""
        
        comparison_results = {}
        
        for strategy_name in strategies:
            result = await self.run_strategy_backtest(
                strategy_name, symbol, start_date, end_date, parameters
            )
            
            comparison_results[strategy_name] = {
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate
            }
        
        return comparison_results