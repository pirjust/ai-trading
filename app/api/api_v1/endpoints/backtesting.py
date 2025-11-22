"""
策略回测相关API端点
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, List
import json

from strategies.backtesting import BacktestManager, BacktestResult

router = APIRouter()

# 全局回测管理器实例
backtest_manager = BacktestManager()

@router.post("/run-backtest")
async def run_backtest(
    strategy_name: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    parameters: Dict
) -> Dict:
    """运行策略回测"""
    try:
        result = await backtest_manager.run_strategy_backtest(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        
        # 转换为可序列化的字典
        return _backtest_result_to_dict(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测运行失败: {str(e)}")

@router.post("/compare-strategies")
async def compare_strategies(
    strategies: List[str],
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    parameters: Dict
) -> Dict:
    """比较多个策略"""
    try:
        comparison_results = await backtest_manager.compare_strategies(
            strategies=strategies,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        
        return comparison_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略比较失败: {str(e)}")

@router.get("/backtest-results/{strategy_name}")
async def get_backtest_result(strategy_name: str) -> Dict:
    """获取特定策略的回测结果"""
    try:
        if strategy_name not in backtest_manager.backtest_results:
            raise HTTPException(status_code=404, detail="回测结果不存在")
        
        result = backtest_manager.backtest_results[strategy_name]
        return _backtest_result_to_dict(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回测结果失败: {str(e)}")

@router.get("/backtest-results")
async def get_all_backtest_results() -> Dict:
    """获取所有回测结果"""
    try:
        results = {}
        for strategy_name, result in backtest_manager.backtest_results.items():
            results[strategy_name] = _backtest_result_to_dict(result)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回测结果失败: {str(e)}")

@router.get("/available-strategies")
async def get_available_strategies() -> List[str]:
    """获取可用的策略列表"""
    try:
        # 返回支持的策略名称
        return ["ml_strategy", "lstm_strategy", "rl_strategy"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")

@router.get("/strategy-performance")
async def get_strategy_performance(strategy_name: str) -> Dict:
    """获取策略性能摘要"""
    try:
        if strategy_name not in backtest_manager.backtest_results:
            raise HTTPException(status_code=404, detail="回测结果不存在")
        
        result = backtest_manager.backtest_results[strategy_name]
        
        performance_summary = {
            "strategy_name": result.strategy_name,
            "symbol": result.symbol,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades
        }
        
        return performance_summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略性能失败: {str(e)}")

@router.get("/equity-curve/{strategy_name}")
async def get_equity_curve(strategy_name: str) -> List[Dict]:
    """获取策略权益曲线"""
    try:
        if strategy_name not in backtest_manager.backtest_results:
            raise HTTPException(status_code=404, detail="回测结果不存在")
        
        result = backtest_manager.backtest_results[strategy_name]
        
        # 转换权益曲线数据为可序列化格式
        equity_curve = []
        for point in result.equity_curve:
            equity_curve.append({
                "timestamp": point['timestamp'].isoformat(),
                "equity": point['equity'],
                "price": point['price']
            })
        
        return equity_curve
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取权益曲线失败: {str(e)}")

@router.get("/trades/{strategy_name}")
async def get_trades(strategy_name: str) -> List[Dict]:
    """获取策略交易记录"""
    try:
        if strategy_name not in backtest_manager.backtest_results:
            raise HTTPException(status_code=404, detail="回测结果不存在")
        
        result = backtest_manager.backtest_results[strategy_name]
        
        # 转换交易记录为可序列化格式
        trades = []
        for trade in result.trades:
            trades.append({
                "action": trade['action'],
                "timestamp": trade['timestamp'].isoformat(),
                "price": trade['price'],
                "quantity": trade['quantity'],
                "commission": trade['commission'],
                "slippage": trade['slippage'],
                "position_before": trade['position_before'],
                "position_after": trade['position_after'],
                "capital_before": trade['capital_before'],
                "capital_after": trade['capital_after']
            })
        
        return trades
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易记录失败: {str(e)}")

def _backtest_result_to_dict(result: BacktestResult) -> Dict:
    """将回测结果转换为字典格式"""
    return {
        "strategy_name": result.strategy_name,
        "symbol": result.symbol,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
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
        "calmar_ratio": result.calmar_ratio
    }