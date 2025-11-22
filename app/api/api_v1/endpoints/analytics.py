"""
数据分析API端点
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class TradingPerformance(BaseModel):
    """交易性能分析模型"""
    total_profit: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    average_trade: float
    best_trade: float
    worst_trade: float

class StrategyAnalytics(BaseModel):
    """策略分析模型"""
    strategy_id: str
    name: str
    performance: TradingPerformance
    daily_returns: List[float]
    monthly_returns: List[float]
    correlation_matrix: Dict[str, float]

class MarketAnalytics(BaseModel):
    """市场分析模型"""
    symbol: str
    current_price: float
    volume_24h: float
    price_change_24h: float
    volatility: float
    support_levels: List[float]
    resistance_levels: List[float]

# 模拟数据
trading_performance = TradingPerformance(
    total_profit=2450.50,
    total_trades=125,
    win_rate=68.5,
    sharpe_ratio=2.1,
    max_drawdown=8.2,
    profit_factor=1.85,
    average_trade=19.6,
    best_trade=450.0,
    worst_trade=-280.5
)

strategy_analytics = [
    StrategyAnalytics(
        strategy_id="1",
        name="移动平均交叉策略",
        performance=TradingPerformance(
            total_profit=1250.5,
            total_trades=45,
            win_rate=68.9,
            sharpe_ratio=2.3,
            max_drawdown=6.5,
            profit_factor=1.92,
            average_trade=27.8,
            best_trade=320.0,
            worst_trade=-150.0
        ),
        daily_returns=[1.2, -0.8, 2.5, 0.3, -1.1, 3.2, 0.7],
        monthly_returns=[8.5, 12.2, -3.8, 15.6, 7.3, 9.1],
        correlation_matrix={"BTC": 0.85, "ETH": 0.78, "ADA": 0.65}
    ),
    StrategyAnalytics(
        strategy_id="2",
        name="RSI超买超卖策略",
        performance=TradingPerformance(
            total_profit=850.25,
            total_trades=32,
            win_rate=72.3,
            sharpe_ratio=1.8,
            max_drawdown=5.8,
            profit_factor=1.76,
            average_trade=26.6,
            best_trade=280.0,
            worst_trade=-120.0
        ),
        daily_returns=[0.8, 1.5, -0.3, 1.8, 0.5, -0.2, 1.3],
        monthly_returns=[6.2, 8.7, 4.3, 9.8, 5.1, 7.4],
        correlation_matrix={"BTC": 0.78, "ETH": 0.82, "ADA": 0.71}
    )
]

market_analytics = [
    MarketAnalytics(
        symbol="BTCUSDT",
        current_price=45000.50,
        volume_24h=2850000000.0,
        price_change_24h=2.5,
        volatility=35.2,
        support_levels=[44500, 43800, 43200],
        resistance_levels=[45500, 46200, 46800]
    ),
    MarketAnalytics(
        symbol="ETHUSDT",
        current_price=2850.75,
        volume_24h=1850000000.0,
        price_change_24h=1.8,
        volatility=28.7,
        support_levels=[2800, 2750, 2700],
        resistance_levels=[2900, 2950, 3000]
    )
]

@router.get("/performance", response_model=TradingPerformance)
async def get_trading_performance():
    """获取整体交易性能"""
    return trading_performance

@router.get("/strategies", response_model=List[StrategyAnalytics])
async def get_strategy_analytics():
    """获取策略分析数据"""
    return strategy_analytics

@router.get("/strategies/{strategy_id}", response_model=StrategyAnalytics)
async def get_strategy_analytics_detail(strategy_id: str):
    """获取特定策略详细分析"""
    for analytics in strategy_analytics:
        if analytics.strategy_id == strategy_id:
            return analytics
    raise HTTPException(status_code=404, detail="Strategy analytics not found")

@router.get("/markets", response_model=List[MarketAnalytics])
async def get_market_analytics(symbol: str = None):
    """获取市场分析数据"""
    if symbol:
        return [m for m in market_analytics if m.symbol == symbol.upper()]
    return market_analytics

@router.get("/returns/daily")
async def get_daily_returns(days: int = 30):
    """获取每日收益数据"""
    # 模拟每日收益数据
    returns = []
    base_date = datetime.now()
    
    for i in range(days):
        date = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
        return_value = (i % 10 - 5) * 0.5  # 模拟收益数据
        returns.append({
            "date": date,
            "return": return_value,
            "cumulative": sum(r["return"] for r in returns) + return_value
        })
    
    return returns[::-1]  # 按时间顺序返回

@router.get("/returns/monthly")
async def get_monthly_returns(months: int = 12):
    """获取月度收益数据"""
    # 模拟月度收益数据
    returns = []
    base_date = datetime.now()
    
    for i in range(months):
        month = (base_date.replace(day=1) - timedelta(days=30*i)).strftime("%Y-%m")
        return_value = (i % 6 - 3) * 2.5  # 模拟月度收益
        returns.append({
            "month": month,
            "return": return_value,
            "cumulative": sum(r["return"] for r in returns) + return_value
        })
    
    return returns[::-1]

@router.get("/correlation")
async def get_correlation_analysis():
    """获取相关性分析"""
    # 模拟相关性矩阵
    symbols = ["BTC", "ETH", "ADA", "DOT", "SOL", "XRP"]
    correlation_matrix = {}
    
    for i, sym1 in enumerate(symbols):
        correlation_matrix[sym1] = {}
        for j, sym2 in enumerate(symbols):
            if i == j:
                correlation_matrix[sym1][sym2] = 1.0
            else:
                # 模拟相关性数据
                correlation_matrix[sym1][sym2] = round(0.7 - abs(i-j)*0.1, 2)
    
    return correlation_matrix

@router.get("/volatility")
async def get_volatility_analysis():
    """获取波动率分析"""
    # 模拟波动率数据
    volatility_data = []
    base_date = datetime.now()
    
    for i in range(30):
        date = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
        volatility_data.append({
            "date": date,
            "btc_volatility": 30 + i % 10,
            "eth_volatility": 25 + i % 8,
            "market_volatility": 28 + i % 9
        })
    
    return volatility_data[::-1]

@router.get("/risk-metrics")
async def get_risk_metrics():
    """获取风险指标"""
    return {
        "var_95": 2450.0,
        "cvar_95": 3120.0,
        "expected_shortfall": 2850.0,
        "value_at_risk": 2100.0,
        "stress_test_passed": True,
        "liquidity_ratio": 0.85,
        "leverage_ratio": 2.3
    }

@router.post("/backtest")
async def run_backtest(strategy_config: Dict[str, Any]):
    """执行策略回测"""
    # 模拟回测结果
    return {
        "status": "completed",
        "strategy_name": strategy_config.get("name", "自定义策略"),
        "period": "2024-01-01 to 2025-01-01",
        "results": {
            "total_return": 25.8,
            "annual_return": 28.3,
            "sharpe_ratio": 2.1,
            "max_drawdown": 12.5,
            "win_rate": 68.9,
            "profit_factor": 1.85,
            "total_trades": 156,
            "average_trade": 15.7
        },
        "equity_curve": [
            {"date": "2024-01-01", "equity": 10000},
            {"date": "2024-03-01", "equity": 10500},
            {"date": "2024-06-01", "equity": 11200},
            {"date": "2024-09-01", "equity": 11800},
            {"date": "2024-12-01", "equity": 12580}
        ]
    }