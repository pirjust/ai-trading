"""
系统监控API端点
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime

router = APIRouter()

class SystemStatus(BaseModel):
    """系统状态模型"""
    status: str  # HEALTHY, DEGRADED, CRITICAL
    uptime: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_throughput: Dict[str, float]
    last_check: str

class ExchangeStatus(BaseModel):
    """交易所状态模型"""
    exchange: str
    status: str  # CONNECTED, DISCONNECTED, DEGRADED
    latency: float
    last_trade: str
    api_calls: int
    error_rate: float

class StrategyStatus(BaseModel):
    """策略状态模型"""
    strategy_id: str
    name: str
    status: str  # RUNNING, PAUSED, STOPPED, ERROR
    symbol: str
    profit_loss: float
    trades_today: int
    last_signal: str
    error_message: str

class PerformanceMetric(BaseModel):
    """性能指标模型"""
    timestamp: str
    metric_type: str  # CPU, MEMORY, DISK, NETWORK, TRADES
    value: float

# 模拟数据
system_status = SystemStatus(
    status="HEALTHY",
    uptime="15天2小时30分钟",
    cpu_usage=45.2,
    memory_usage=62.8,
    disk_usage=35.7,
    network_throughput={"in": 125.5, "out": 89.3},
    last_check=datetime.now().isoformat()
)

exchange_statuses = [
    ExchangeStatus(
        exchange="binance",
        status="CONNECTED",
        latency=45.2,
        last_trade=datetime.now().isoformat(),
        api_calls=1250,
        error_rate=0.5
    ),
    ExchangeStatus(
        exchange="okx", 
        status="CONNECTED",
        latency=38.7,
        last_trade=datetime.now().isoformat(),
        api_calls=890,
        error_rate=0.3
    )
]

strategy_statuses = [
    StrategyStatus(
        strategy_id="1",
        name="移动平均交叉策略",
        status="RUNNING",
        symbol="BTCUSDT",
        profit_loss=1250.5,
        trades_today=8,
        last_signal=datetime.now().isoformat(),
        error_message=""
    ),
    StrategyStatus(
        strategy_id="2",
        name="RSI超买超卖策略", 
        status="RUNNING",
        symbol="ETHUSDT",
        profit_loss=850.25,
        trades_today=5,
        last_signal=datetime.now().isoformat(),
        error_message=""
    ),
    StrategyStatus(
        strategy_id="3",
        name="期权波动率策略",
        status="PAUSED",
        symbol="BTC-OPTION",
        profit_loss=-150.75,
        trades_today=0,
        last_signal=datetime.now().isoformat(),
        error_message="市场波动率过低"
    )
]

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@router.get("/system", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    # 更新系统状态
    system_status.last_check = datetime.now().isoformat()
    return system_status

@router.get("/exchanges", response_model=List[ExchangeStatus])
async def get_exchange_statuses():
    """获取交易所状态"""
    return exchange_statuses

@router.get("/exchanges/{exchange}", response_model=ExchangeStatus)
async def get_exchange_status(exchange: str):
    """获取特定交易所状态"""
    for status in exchange_statuses:
        if status.exchange == exchange:
            return status
    raise HTTPException(status_code=404, detail="Exchange not found")

@router.get("/strategies", response_model=List[StrategyStatus])
async def get_strategy_statuses(status: str = None):
    """获取策略状态列表"""
    if status:
        return [s for s in strategy_statuses if s.status == status.upper()]
    return strategy_statuses

@router.get("/strategies/{strategy_id}", response_model=StrategyStatus)
async def get_strategy_status(strategy_id: str):
    """获取特定策略状态"""
    for status in strategy_statuses:
        if status.strategy_id == strategy_id:
            return status
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.post("/strategies/{strategy_id}/start")
async def start_strategy(strategy_id: str):
    """启动策略"""
    for status in strategy_statuses:
        if status.strategy_id == strategy_id:
            status.status = "RUNNING"
            status.last_signal = datetime.now().isoformat()
            return {"message": f"Strategy {strategy_id} started successfully"}
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.post("/strategies/{strategy_id}/pause")
async def pause_strategy(strategy_id: str):
    """暂停策略"""
    for status in strategy_statuses:
        if status.strategy_id == strategy_id:
            status.status = "PAUSED"
            return {"message": f"Strategy {strategy_id} paused successfully"}
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.post("/strategies/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """停止策略"""
    for status in strategy_statuses:
        if status.strategy_id == strategy_id:
            status.status = "STOPPED"
            return {"message": f"Strategy {strategy_id} stopped successfully"}
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.get("/performance")
async def get_performance_metrics(metric_type: str = None, limit: int = 100):
    """获取性能指标"""
    # 模拟性能数据
    metrics = []
    base_time = datetime.now()
    
    for i in range(limit):
        timestamp = (base_time - timedelta(minutes=i)).isoformat()
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            metric_type="CPU",
            value=40 + i % 20
        ))
        
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            metric_type="MEMORY",
            value=60 + i % 15
        ))
        
        metrics.append(PerformanceMetric(
            timestamp=timestamp,
            metric_type="TRADES",
            value=i % 5
        ))
    
    if metric_type:
        metrics = [m for m in metrics if m.metric_type == metric_type.upper()]
    
    return metrics[:limit]

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时监控"""
    await manager.connect(websocket)
    try:
        while True:
            # 发送实时数据
            data = {
                "type": "monitoring_update",
                "timestamp": datetime.now().isoformat(),
                "system_status": system_status.dict(),
                "exchange_statuses": [s.dict() for s in exchange_statuses],
                "strategy_statuses": [s.dict() for s in strategy_statuses]
            }
            
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)  # 每5秒更新一次
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/alerts")
async def get_system_alerts(level: str = None):
    """获取系统报警"""
    alerts = [
        {
            "id": "1",
            "level": "LOW",
            "type": "PERFORMANCE",
            "message": "CPU使用率偏高",
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        },
        {
            "id": "2",
            "level": "MEDIUM", 
            "type": "NETWORK",
            "message": "网络延迟增加",
            "timestamp": datetime.now().isoformat(),
            "resolved": True
        }
    ]
    
    if level:
        alerts = [a for a in alerts if a["level"] == level.upper()]
    
    return alerts

from datetime import timedelta