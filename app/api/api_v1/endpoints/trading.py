"""
交易API端点
处理交易相关的HTTP请求
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from core.database import get_db
from core.logger import get_logger
from data.data_manager import get_data_manager
from agents.strategy_manager import get_strategy_manager

logger = get_logger(__name__)
router = APIRouter()


# Pydantic模型定义
class KlineRequest(BaseModel):
    symbol: str = Field(..., description="交易对")
    interval: str = Field(default="1h", description="时间间隔")
    limit: int = Field(default=100, description="数据条数")
    exchange: str = Field(default="binance", description="交易所")


class TradeRequest(BaseModel):
    symbol: str = Field(..., description="交易对")
    side: str = Field(..., description="交易方向: buy/sell")
    order_type: str = Field(default="market", description="订单类型: market/limit")
    quantity: float = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格（限价单）")
    exchange: str = Field(default="binance", description="交易所")


class StrategyRequest(BaseModel):
    name: Optional[str] = Field(None, description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    symbols: List[str] = Field(..., description="交易对列表")
    parameters: Dict[str, Any] = Field(default={}, description="策略参数")
    is_active: bool = Field(default=True, description="是否激活")


class BacktestRequest(BaseModel):
    strategy_id: int = Field(..., description="策略ID")
    symbol: str = Field(..., description="交易对")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    initial_balance: float = Field(default=10000.0, description="初始资金")
    parameters: Optional[Dict[str, Any]] = Field(None, description="覆盖参数")


# API端点实现

@router.get("/klines")
async def get_kline_data(request: KlineRequest):
    """获取K线数据"""
    try:
        data_manager = await get_data_manager()
        df = await data_manager.get_kline_data(
            symbol=request.symbol,
            interval=request.interval,
            limit=request.limit,
            exchange=request.exchange
        )
        
        # 转换为API响应格式
        klines = []
        for timestamp, row in df.iterrows():
            klines.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        return {
            "success": True,
            "data": klines,
            "symbol": request.symbol,
            "interval": request.interval,
            "exchange": request.exchange,
            "count": len(klines)
        }
        
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_ticker_data(symbol: str, exchange: str = "binance"):
    """获取行情数据"""
    try:
        data_manager = await get_data_manager()
        ticker_data = await data_manager.get_ticker_data(symbol, exchange)
        
        return {
            "success": True,
            "data": ticker_data,
            "symbol": symbol,
            "exchange": exchange
        }
        
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orderbook/{symbol}")
async def get_orderbook_data(symbol: str, exchange: str = "binance", depth: int = 20):
    """获取订单簿数据"""
    try:
        data_manager = await get_data_manager()
        orderbook_data = await data_manager.get_orderbook_data(symbol, depth, exchange)
        
        return {
            "success": True,
            "data": orderbook_data,
            "symbol": symbol,
            "exchange": exchange,
            "depth": depth
        }
        
    except Exception as e:
        logger.error(f"获取订单簿数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{symbol}")
async def get_latest_price(symbol: str, exchange: str = "binance"):
    """获取最新价格"""
    try:
        data_manager = await get_data_manager()
        price = await data_manager.get_latest_price(symbol, exchange)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "price": price,
                "exchange": exchange,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取最新价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def place_order(request: TradeRequest, db: AsyncSession = Depends(get_db)):
    """下单"""
    try:
        # 这里应该实现实际的交易逻辑
        # 包括风险检查、仓位管理、订单执行等
        
        # 模拟下单响应
        order_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(request.symbol)}"
        
        order_response = {
            "order_id": order_id,
            "symbol": request.symbol,
            "side": request.side,
            "order_type": request.order_type,
            "quantity": request.quantity,
            "price": request.price,
            "status": "submitted",
            "exchange": request.exchange,
            "created_at": datetime.now().isoformat()
        }
        
        # 记录交易日志
        logger.info(f"订单提交: {order_response}")
        
        return {
            "success": True,
            "data": order_response,
            "message": "订单提交成功"
        }
        
    except Exception as e:
        logger.error(f"下单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表"""
    try:
        # 这里应该从数据库查询订单
        # 简化实现，返回模拟数据
        
        orders = [
            {
                "order_id": "order_001",
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "market",
                "quantity": 0.01,
                "price": 50000.0,
                "status": "filled",
                "created_at": "2024-01-01T10:00:00",
                "exchange": "binance"
            },
            {
                "order_id": "order_002",
                "symbol": "ETHUSDT",
                "side": "sell",
                "order_type": "limit",
                "quantity": 0.1,
                "price": 3000.0,
                "status": "pending",
                "created_at": "2024-01-01T10:30:00",
                "exchange": "binance"
            }
        ]
        
        # 根据参数过滤
        if symbol:
            orders = [order for order in orders if order["symbol"] == symbol]
        if status:
            orders = [order for order in orders if order["status"] == status]
        
        return {
            "success": True,
            "data": orders[:limit],
            "total": len(orders),
            "filters": {
                "symbol": symbol,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """获取持仓信息"""
    try:
        # 这里应该从数据库查询持仓
        # 简化实现，返回模拟数据
        
        positions = [
            {
                "symbol": "BTCUSDT",
                "side": "long",
                "size": 0.05,
                "entry_price": 48000.0,
                "current_price": 50000.0,
                "unrealized_pnl": 100.0,
                "pnl_percentage": 4.17,
                "margin_used": 2500.0,
                "exchange": "binance"
            },
            {
                "symbol": "ETHUSDT",
                "side": "short",
                "size": 0.2,
                "entry_price": 3200.0,
                "current_price": 3000.0,
                "unrealized_pnl": 40.0,
                "pnl_percentage": 6.25,
                "margin_used": 640.0,
                "exchange": "binance"
            }
        ]
        
        total_pnl = sum(pos["unrealized_pnl"] for pos in positions)
        total_margin = sum(pos["margin_used"] for pos in positions)
        
        return {
            "success": True,
            "data": positions,
            "summary": {
                "total_positions": len(positions),
                "total_unrealized_pnl": total_pnl,
                "total_margin_used": total_margin,
                "margin_percentage": (total_margin / 10000.0) * 100  # 假设总资金10000
            }
        }
        
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance(db: AsyncSession = Depends(get_db)):
    """获取账户余额"""
    try:
        # 这里应该从数据库或交易所API查询余额
        # 简化实现，返回模拟数据
        
        balances = [
            {
                "asset": "USDT",
                "free": 5000.0,
                "locked": 1000.0,
                "total": 6000.0
            },
            {
                "asset": "BTC",
                "free": 0.05,
                "locked": 0.01,
                "total": 0.06
            },
            {
                "asset": "ETH",
                "free": 0.2,
                "locked": 0.0,
                "total": 0.2
            }
        ]
        
        # 计算总价值（假设BTC=50000, ETH=3000）
        total_usdt_value = 0.0
        for balance in balances:
            if balance["asset"] == "USDT":
                total_usdt_value += balance["total"]
            elif balance["asset"] == "BTC":
                total_usdt_value += balance["total"] * 50000.0
            elif balance["asset"] == "ETH":
                total_usdt_value += balance["total"] * 3000.0
        
        return {
            "success": True,
            "data": balances,
            "summary": {
                "total_usdt_value": total_usdt_value,
                "free_usdt_value": total_usdt_value - 1000.0,  # 减去锁定部分
                "locked_usdt_value": 1000.0
            }
        }
        
    except Exception as e:
        logger.error(f"获取账户余额失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy")
async def create_strategy(request: StrategyRequest, db: AsyncSession = Depends(get_db)):
    """创建策略"""
    try:
        strategy_manager = get_strategy_manager()
        
        # 创建策略
        strategy_id = await strategy_manager.create_strategy(
            name=request.name,
            strategy_type=request.strategy_type,
            symbols=request.symbols,
            parameters=request.parameters,
            is_active=request.is_active
        )
        
        return {
            "success": True,
            "data": {
                "strategy_id": strategy_id,
                "name": request.name,
                "strategy_type": request.strategy_type,
                "symbols": request.symbols,
                "is_active": request.is_active,
                "created_at": datetime.now().isoformat()
            },
            "message": "策略创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_strategies(is_active: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    """获取策略列表"""
    try:
        strategy_manager = get_strategy_manager()
        strategies = await strategy_manager.list_strategies(is_active=is_active)
        
        return {
            "success": True,
            "data": strategies,
            "total": len(strategies),
            "filters": {
                "is_active": is_active
            }
        }
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """运行回测"""
    try:
        # 生成回测任务ID
        backtest_id = f"backtest_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(request.symbol)}"
        
        # 添加后台任务运行回测
        background_tasks.add_task(
            _run_backtest_task,
            backtest_id,
            request.strategy_id,
            request.symbol,
            request.start_time,
            request.end_time,
            request.initial_balance,
            request.parameters or {}
        )
        
        return {
            "success": True,
            "data": {
                "backtest_id": backtest_id,
                "status": "running",
                "strategy_id": request.strategy_id,
                "symbol": request.symbol,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "initial_balance": request.initial_balance
            },
            "message": "回测任务已启动"
        }
        
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    try:
        # 这里应该从数据库或缓存中获取回测结果
        # 简化实现，返回模拟结果
        
        result = {
            "backtest_id": backtest_id,
            "status": "completed",
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-31T23:59:59",
            "initial_balance": 10000.0,
            "final_balance": 11500.0,
            "total_return": 15.0,
            "max_drawdown": 5.2,
            "sharpe_ratio": 1.8,
            "win_rate": 0.65,
            "total_trades": 45,
            "profit_trades": 29,
            "loss_trades": 16
        }
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取回测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchanges")
async def get_supported_exchanges():
    """获取支持的交易所"""
    try:
        data_manager = await get_data_manager()
        
        exchanges = []
        for exchange_name in ['binance', 'okx', 'bybit']:
            try:
                symbols = await data_manager.get_supported_symbols(exchange_name)
                exchanges.append({
                    "name": exchange_name,
                    "display_name": exchange_name.upper(),
                    "is_active": len(symbols) > 0,
                    "symbol_count": len(symbols)
                })
            except Exception as e:
                logger.warning(f"获取{exchange_name}交易对失败: {e}")
                exchanges.append({
                    "name": exchange_name,
                    "display_name": exchange_name.upper(),
                    "is_active": False,
                    "symbol_count": 0
                })
        
        return {
            "success": True,
            "data": exchanges
        }
        
    except Exception as e:
        logger.error(f"获取交易所列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
async def _run_backtest_task(backtest_id: str, strategy_id: int, symbol: str,
                           start_time: str, end_time: str, initial_balance: float,
                           parameters: Dict[str, Any]):
    """后台回测任务"""
    try:
        logger.info(f"开始执行回测任务: {backtest_id}")
        
        # 这里应该实现实际的回测逻辑
        # 包括数据获取、策略执行、收益计算等
        
        # 模拟回测执行时间
        await asyncio.sleep(10)
        
        logger.info(f"回测任务完成: {backtest_id}")
        
    except Exception as e:
        logger.error(f"回测任务失败: {backtest_id} - {e}")


# 错误处理
@router.exception_handler(Exception)
async def trading_exception_handler(request, exc):
    logger.error(f"交易API异常: {exc}")
    return {
        "success": False,
        "error": str(exc),
        "timestamp": datetime.now().isoformat()
    }