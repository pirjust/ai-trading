"""
策略回测数据管理模块
负责存储、查询和分析回测结果数据
"""
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict

from strategies.backtesting import BacktestResult


@dataclass
class BacktestDataPoint:
    """回测数据点"""
    timestamp: datetime
    equity: float
    price: float
    position: float
    capital: float


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    timestamp: datetime
    symbol: str
    action: str  # buy, sell
    price: float
    quantity: float
    commission: float
    slippage: float
    position_before: float
    position_after: float
    capital_before: float
    capital_after: float
    profit_loss: float = 0.0


class BacktestDataManager:
    """回测数据管理器"""
    
    def __init__(self, data_dir: str = "data/backtest_results"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        self.equity_curves: Dict[str, List[BacktestDataPoint]] = {}
        self.trade_records: Dict[str, List[TradeRecord]] = {}
        
    async def save_backtest_result(self, result: BacktestResult) -> str:
        """保存回测结果"""
        try:
            # 生成唯一标识
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_id = f"{result.strategy_name}_{result.symbol}_{timestamp}"
            
            # 保存到内存
            self.backtest_results[result_id] = result
            
            # 保存到文件
            file_path = self.data_dir / f"{result_id}.pkl"
            with open(file_path, 'wb') as f:
                pickle.dump(result, f)
            
            # 保存性能指标
            await self._save_performance_metrics(result_id, result)
            
            # 保存权益曲线
            await self._save_equity_curve(result_id, result)
            
            # 保存交易记录
            await self._save_trade_records(result_id, result)
            
            return result_id
            
        except Exception as e:
            raise Exception(f"保存回测结果失败: {str(e)}")
    
    async def load_backtest_result(self, result_id: str) -> BacktestResult:
        """加载回测结果"""
        try:
            # 检查内存缓存
            if result_id in self.backtest_results:
                return self.backtest_results[result_id]
            
            # 从文件加载
            file_path = self.data_dir / f"{result_id}.pkl"
            if not file_path.exists():
                raise FileNotFoundError(f"回测结果不存在: {result_id}")
            
            with open(file_path, 'rb') as f:
                result = pickle.load(f)
            
            # 缓存到内存
            self.backtest_results[result_id] = result
            
            return result
            
        except Exception as e:
            raise Exception(f"加载回测结果失败: {str(e)}")
    
    async def get_performance_summary(self, result_id: str) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            result = await self.load_backtest_result(result_id)
            
            summary = {
                "strategy_name": result.strategy_name,
                "symbol": result.symbol,
                "start_date": result.start_date,
                "end_date": result.end_date,
                "total_return": result.total_return,
                "annual_return": result.annual_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "profit_factor": result.profit_factor,
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "volatility": result.volatility,
                "var_95": result.var_95,
                "calmar_ratio": result.calmar_ratio,
                "total_duration_days": (result.end_date - result.start_date).days
            }
            
            return summary
            
        except Exception as e:
            raise Exception(f"获取性能摘要失败: {str(e)}")
    
    async def get_comparison_report(self, result_ids: List[str]) -> Dict[str, Any]:
        """生成策略比较报告"""
        try:
            comparison_data = {}
            
            for result_id in result_ids:
                summary = await self.get_performance_summary(result_id)
                comparison_data[result_id] = summary
            
            # 计算排名
            metrics = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]
            rankings = {}
            
            for metric in metrics:
                sorted_results = sorted(
                    comparison_data.items(),
                    key=lambda x: x[1][metric],
                    reverse=(metric != "max_drawdown")  # 最大回撤越小越好
                )
                rankings[metric] = {result_id: rank + 1 
                                   for rank, (result_id, _) in enumerate(sorted_results)}
            
            report = {
                "comparison_data": comparison_data,
                "rankings": rankings,
                "summary": {
                    "total_strategies": len(result_ids),
                    "best_return": max(s["total_return"] for s in comparison_data.values()),
                    "best_sharpe": max(s["sharpe_ratio"] for s in comparison_data.values()),
                    "lowest_drawdown": min(s["max_drawdown"] for s in comparison_data.values())
                }
            }
            
            return report
            
        except Exception as e:
            raise Exception(f"生成比较报告失败: {str(e)}")
    
    async def get_equity_curve_data(self, result_id: str) -> List[Dict[str, Any]]:
        """获取权益曲线数据"""
        try:
            if result_id in self.equity_curves:
                equity_curve = self.equity_curves[result_id]
            else:
                result = await self.load_backtest_result(result_id)
                equity_curve = await self._convert_to_data_points(result)
                self.equity_curves[result_id] = equity_curve
            
            # 转换为可序列化格式
            return [
                {
                    "timestamp": point.timestamp.isoformat(),
                    "equity": point.equity,
                    "price": point.price,
                    "position": point.position,
                    "capital": point.capital
                }
                for point in equity_curve
            ]
            
        except Exception as e:
            raise Exception(f"获取权益曲线数据失败: {str(e)}")
    
    async def get_trade_analysis(self, result_id: str) -> Dict[str, Any]:
        """获取交易分析"""
        try:
            if result_id not in self.trade_records:
                result = await self.load_backtest_result(result_id)
                trade_records = await self._convert_to_trade_records(result)
                self.trade_records[result_id] = trade_records
            else:
                trade_records = self.trade_records[result_id]
            
            # 计算交易统计
            total_trades = len(trade_records)
            winning_trades = len([t for t in trade_records if t.profit_loss > 0])
            losing_trades = len([t for t in trade_records if t.profit_loss < 0])
            
            avg_profit = np.mean([t.profit_loss for t in trade_records if t.profit_loss > 0])
            avg_loss = np.mean([t.profit_loss for t in trade_records if t.profit_loss < 0])
            
            trade_durations = []
            for i in range(1, len(trade_records)):
                if trade_records[i].action == "sell" and trade_records[i-1].action == "buy":
                    duration = (trade_records[i].timestamp - trade_records[i-1].timestamp).total_seconds() / 3600
                    trade_durations.append(duration)
            
            analysis = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
                "avg_profit": avg_profit,
                "avg_loss": avg_loss,
                "profit_factor": abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf'),
                "avg_trade_duration_hours": np.mean(trade_durations) if trade_durations else 0,
                "trades_by_hour": await self._analyze_trade_timing(trade_records),
                "profit_distribution": await self._analyze_profit_distribution(trade_records)
            }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"获取交易分析失败: {str(e)}")
    
    async def cleanup_old_results(self, days_to_keep: int = 30):
        """清理旧的回测结果"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for file_path in self.data_dir.glob("*.pkl"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    
                    # 清理内存缓存
                    result_id = file_path.stem
                    if result_id in self.backtest_results:
                        del self.backtest_results[result_id]
                    if result_id in self.performance_metrics:
                        del self.performance_metrics[result_id]
                    if result_id in self.equity_curves:
                        del self.equity_curves[result_id]
                    if result_id in self.trade_records:
                        del self.trade_records[result_id]
            
        except Exception as e:
            raise Exception(f"清理旧结果失败: {str(e)}")
    
    async def _save_performance_metrics(self, result_id: str, result: BacktestResult):
        """保存性能指标"""
        metrics = await self.get_performance_summary(result_id)
        self.performance_metrics[result_id] = metrics
        
        # 保存到JSON文件
        json_path = self.data_dir / f"{result_id}_metrics.json"
        with open(json_path, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
    
    async def _save_equity_curve(self, result_id: str, result: BacktestResult):
        """保存权益曲线"""
        equity_curve = await self._convert_to_data_points(result)
        self.equity_curves[result_id] = equity_curve
        
        # 保存到CSV文件
        csv_path = self.data_dir / f"{result_id}_equity.csv"
        df = pd.DataFrame([asdict(point) for point in equity_curve])
        df.to_csv(csv_path, index=False)
    
    async def _save_trade_records(self, result_id: str, result: BacktestResult):
        """保存交易记录"""
        trade_records = await self._convert_to_trade_records(result)
        self.trade_records[result_id] = trade_records
        
        # 保存到CSV文件
        csv_path = self.data_dir / f"{result_id}_trades.csv"
        df = pd.DataFrame([asdict(trade) for trade in trade_records])
        df.to_csv(csv_path, index=False)
    
    async def _convert_to_data_points(self, result: BacktestResult) -> List[BacktestDataPoint]:
        """转换回测结果为数据点"""
        data_points = []
        
        # 简化的转换逻辑，实际应根据回测结果结构调整
        for i, point in enumerate(result.equity_curve):
            data_point = BacktestDataPoint(
                timestamp=point['timestamp'],
                equity=point['equity'],
                price=point['price'],
                position=0.0,  # 需要从回测结果中获取
                capital=point['equity']  # 简化的资本计算
            )
            data_points.append(data_point)
        
        return data_points
    
    async def _convert_to_trade_records(self, result: BacktestResult) -> List[TradeRecord]:
        """转换回测结果为交易记录"""
        trade_records = []
        
        # 简化的转换逻辑，实际应根据回测结果结构调整
        for i, trade in enumerate(result.trades):
            trade_record = TradeRecord(
                trade_id=f"{result.strategy_name}_{i}",
                timestamp=trade['timestamp'],
                symbol=result.symbol,
                action=trade['action'],
                price=trade['price'],
                quantity=trade['quantity'],
                commission=trade['commission'],
                slippage=trade['slippage'],
                position_before=trade['position_before'],
                position_after=trade['position_after'],
                capital_before=trade['capital_before'],
                capital_after=trade['capital_after'],
                profit_loss=0.0  # 需要计算
            )
            trade_records.append(trade_record)
        
        return trade_records
    
    async def _analyze_trade_timing(self, trade_records: List[TradeRecord]) -> Dict[str, int]:
        """分析交易时间分布"""
        trades_by_hour = {str(hour): 0 for hour in range(24)}
        
        for trade in trade_records:
            hour = trade.timestamp.hour
            trades_by_hour[str(hour)] += 1
        
        return trades_by_hour
    
    async def _analyze_profit_distribution(self, trade_records: List[TradeRecord]) -> Dict[str, int]:
        """分析利润分布"""
        profit_ranges = {
            "<-10%": 0,
            "-10% to -5%": 0,
            "-5% to -1%": 0,
            "-1% to 1%": 0,
            "1% to 5%": 0,
            "5% to 10%": 0,
            ">10%": 0
        }
        
        for trade in trade_records:
            if trade.profit_loss != 0 and trade.capital_before > 0:
                profit_pct = (trade.profit_loss / trade.capital_before) * 100
                
                if profit_pct < -10:
                    profit_ranges["<-10%"] += 1
                elif profit_pct < -5:
                    profit_ranges["-10% to -5%"] += 1
                elif profit_pct < -1:
                    profit_ranges["-5% to -1%"] += 1
                elif profit_pct < 1:
                    profit_ranges["-1% to 1%"] += 1
                elif profit_pct < 5:
                    profit_ranges["1% to 5%"] += 1
                elif profit_pct < 10:
                    profit_ranges["5% to 10%"] += 1
                else:
                    profit_ranges[">10%"] += 1
        
        return profit_ranges