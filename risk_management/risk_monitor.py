"""
风险监控服务
实时监控交易风险，集成风控引擎和策略回测
"""
import asyncio
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from risk_management.risk_engine import RiskEngine, RiskAlert
from strategies.backtesting import BacktestManager
from config.risk_config import RiskLevel, RiskType, RISK_CONFIG, ALERT_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str
    timestamp: datetime
    risk_level: RiskLevel
    risk_type: RiskType
    symbol: str
    message: str
    value: float
    threshold: float
    action_taken: str = ""

class RiskMonitor:
    """风险监控器"""
    
    def __init__(self, risk_engine: RiskEngine, backtest_manager: BacktestManager):
        self.risk_engine = risk_engine
        self.backtest_manager = backtest_manager
        
        self.is_running = False
        self.monitoring_tasks = {}
        self.subscribers: List[Callable] = []
        self.risk_events: List[RiskEvent] = []
        
        # 监控配置
        self.monitoring_config = {
            "position_risk": {"interval": 30, "enabled": True},
            "market_risk": {"interval": 60, "enabled": True},
            "liquidity_risk": {"interval": 120, "enabled": True},
            "portfolio_risk": {"interval": 300, "enabled": True}
        }
        
        # 监控历史
        self.monitoring_history = {
            "position_risk": [],
            "market_risk": [],
            "liquidity_risk": [],
            "portfolio_risk": []
        }
    
    async def start_monitoring(self):
        """启动风险监控"""
        logger.info("启动风险监控服务")
        
        self.is_running = True
        
        # 启动各个监控任务
        for risk_type, config in self.monitoring_config.items():
            if config["enabled"]:
                task = asyncio.create_task(
                    self._monitor_risk_type(risk_type, config["interval"])
                )
                self.monitoring_tasks[risk_type] = task
        
        # 启动警报处理任务
        self.alert_task = asyncio.create_task(self._process_alerts())
        
        logger.info("风险监控服务已启动")
    
    async def stop_monitoring(self):
        """停止风险监控"""
        logger.info("停止风险监控服务")
        
        self.is_running = False
        
        # 取消所有监控任务
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # 取消警报处理任务
        self.alert_task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        await asyncio.gather(self.alert_task, return_exceptions=True)
        
        logger.info("风险监控服务已停止")
    
    async def _monitor_risk_type(self, risk_type: str, interval: int):
        """监控特定风险类型"""
        while self.is_running:
            try:
                await self._execute_risk_monitoring(risk_type)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{risk_type}监控失败: {str(e)}")
                await asyncio.sleep(interval)
    
    async def _execute_risk_monitoring(self, risk_type: str):
        """执行风险监控"""
        timestamp = datetime.now()
        
        try:
            if risk_type == "position_risk":
                await self._monitor_position_risk()
            elif risk_type == "market_risk":
                await self._monitor_market_risk()
            elif risk_type == "liquidity_risk":
                await self._monitor_liquidity_risk()
            elif risk_type == "portfolio_risk":
                await self._monitor_portfolio_risk()
            
            # 记录监控历史
            self.monitoring_history[risk_type].append({
                "timestamp": timestamp,
                "status": "success"
            })
            
            # 清理历史记录
            if len(self.monitoring_history[risk_type]) > 1000:
                self.monitoring_history[risk_type] = self.monitoring_history[risk_type][-1000:]
                
        except Exception as e:
            self.monitoring_history[risk_type].append({
                "timestamp": timestamp,
                "status": "error",
                "error": str(e)
            })
            raise
    
    async def _monitor_position_risk(self):
        """监控仓位风险"""
        # 获取当前仓位数据
        portfolio = await self._get_current_portfolio()
        
        for symbol, position in portfolio.items():
            # 检查单个仓位风险
            risk_check = await self.risk_engine.check_trade_risk(
                symbol=symbol,
                side="hold",
                quantity=0,
                order_type="monitor"
            )
            
            if risk_check["risk_level"] in ["high", "critical"]:
                await self._trigger_risk_event(
                    RiskType.MARKET,
                    RiskLevel(risk_check["risk_level"]),
                    symbol,
                    f"仓位风险过高: {risk_check.get('reason', '未知原因')}",
                    position,
                    0  # 阈值需要根据具体配置设置
                )
    
    async def _monitor_market_risk(self):
        """监控市场风险"""
        # 获取市场数据
        market_data = await self._get_market_data()
        
        for symbol, data in market_data.items():
            volatility = data.get("volatility", 0)
            
            # 检查市场波动率
            if volatility > 0.1:  # 10%波动率阈值
                await self._trigger_risk_event(
                    RiskType.MARKET,
                    RiskLevel.HIGH if volatility > 0.2 else RiskLevel.MEDIUM,
                    symbol,
                    f"市场波动率过高: {volatility:.2%}",
                    volatility,
                    0.1
                )
    
    async def _monitor_liquidity_risk(self):
        """监控流动性风险"""
        # 获取流动性数据
        liquidity_data = await self._get_liquidity_data()
        
        for symbol, data in liquidity_data.items():
            liquidity_score = data.get("liquidity_score", 1.0)
            
            # 检查流动性风险
            if liquidity_score < 0.5:  # 流动性评分阈值
                await self._trigger_risk_event(
                    RiskType.LIQUIDITY,
                    RiskLevel.HIGH if liquidity_score < 0.3 else RiskLevel.MEDIUM,
                    symbol,
                    f"流动性风险: 评分 {liquidity_score:.2f}",
                    liquidity_score,
                    0.5
                )
    
    async def _monitor_portfolio_risk(self):
        """监控投资组合风险"""
        portfolio = await self._get_current_portfolio()
        
        if portfolio:
            # 计算组合风险指标
            risk_metrics = await self.risk_engine.monitor_portfolio_risk(portfolio)
            
            # 检查VaR阈值
            if risk_metrics.get("var_95", 0) > 1000:  # 示例阈值
                await self._trigger_risk_event(
                    RiskType.MARKET,
                    RiskLevel.HIGH,
                    "PORTFOLIO",
                    f"投资组合VaR超过阈值: {risk_metrics['var_95']:.2f}",
                    risk_metrics["var_95"],
                    1000
                )
            
            # 检查集中度风险
            if risk_metrics.get("concentration_risk", 0) > 0.3:  # 30%集中度阈值
                await self._trigger_risk_event(
                    RiskType.MARKET,
                    RiskLevel.MEDIUM,
                    "PORTFOLIO",
                    f"投资组合集中度过高: {risk_metrics['concentration_risk']:.2%}",
                    risk_metrics["concentration_risk"],
                    0.3
                )
    
    async def _process_alerts(self):
        """处理风险警报"""
        while self.is_running:
            try:
                # 检查风险引擎中的警报
                active_alerts = self.risk_engine.active_alerts
                
                for alert in active_alerts:
                    # 处理高风险警报
                    if alert.level in ["high", "critical"]:
                        await self._handle_high_risk_alert(alert)
                
                await asyncio.sleep(10)  # 每10秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"警报处理失败: {str(e)}")
                await asyncio.sleep(10)
    
    async def _handle_high_risk_alert(self, alert: RiskAlert):
        """处理高风险警报"""
        logger.warning(f"处理高风险警报: {alert.message}")
        
        # 根据警报级别采取相应措施
        if alert.level == "critical":
            # 紧急措施：停止交易
            await self._execute_emergency_action("stop_trading", alert)
        elif alert.level == "high":
            # 高风险措施：减仓
            await self._execute_risk_action("reduce_position", alert)
        
        # 通知订阅者
        await self._notify_subscribers(alert)
    
    async def _execute_emergency_action(self, action: str, alert: RiskAlert):
        """执行紧急措施"""
        logger.critical(f"执行紧急措施: {action} - {alert.message}")
        
        if action == "stop_trading":
            # 停止所有交易
            await self._stop_all_trading()
        elif action == "emergency_liquidation":
            # 紧急平仓
            await self._liquidate_positions()
    
    async def _execute_risk_action(self, action: str, alert: RiskAlert):
        """执行风险控制措施"""
        logger.warning(f"执行风险控制: {action} - {alert.message}")
        
        if action == "reduce_position":
            # 减仓操作
            await self._reduce_position(alert.symbol, 0.5)  # 减仓50%
        elif action == "increase_hedge":
            # 增加对冲
            await self._increase_hedging()
    
    async def _trigger_risk_event(
        self,
        risk_type: RiskType,
        risk_level: RiskLevel,
        symbol: str,
        message: str,
        value: float,
        threshold: float
    ):
        """触发风险事件"""
        event = RiskEvent(
            event_id=f"risk_{int(time.time())}",
            timestamp=datetime.now(),
            risk_level=risk_level,
            risk_type=risk_type,
            symbol=symbol,
            message=message,
            value=value,
            threshold=threshold
        )
        
        self.risk_events.append(event)
        
        # 限制事件数量
        if len(self.risk_events) > 1000:
            self.risk_events = self.risk_events[-1000:]
        
        logger.info(f"风险事件: {risk_level.value} - {message}")
    
    async def subscribe(self, callback: Callable):
        """订阅风险事件"""
        self.subscribers.append(callback)
    
    async def _notify_subscribers(self, alert: RiskAlert):
        """通知订阅者"""
        for callback in self.subscribers:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"通知订阅者失败: {str(e)}")
    
    async def get_monitoring_status(self) -> Dict:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "monitoring_tasks": len(self.monitoring_tasks),
            "active_alerts": len(self.risk_engine.active_alerts),
            "risk_events": len(self.risk_events),
            "subscribers": len(self.subscribers)
        }
    
    async def get_risk_summary(self) -> Dict:
        """获取风险摘要"""
        portfolio = await self._get_current_portfolio()
        
        if portfolio:
            risk_metrics = await self.risk_engine.monitor_portfolio_risk(portfolio)
            risk_report = await self.risk_engine.get_risk_report(portfolio)
            
            return {
                "portfolio_value": sum(portfolio.values()),
                "risk_metrics": risk_metrics,
                "active_alerts": [
                    {
                        "level": alert.level,
                        "type": alert.type,
                        "symbol": alert.symbol,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in self.risk_engine.active_alerts[:10]  # 最近10个警报
                ],
                "monitoring_status": await self.get_monitoring_status()
            }
        
        return {"error": "无法获取投资组合数据"}
    
    # 以下方法需要根据实际系统实现
    async def _get_current_portfolio(self) -> Dict:
        """获取当前投资组合"""
        # 这里应该从数据库或交易系统获取真实数据
        return {"BTCUSDT": 5000, "ETHUSDT": 3000, "BNBUSDT": 2000}
    
    async def _get_market_data(self) -> Dict:
        """获取市场数据"""
        # 这里应该从交易所API获取真实数据
        return {
            "BTCUSDT": {"volatility": 0.05, "price": 50000},
            "ETHUSDT": {"volatility": 0.08, "price": 3000},
            "BNBUSDT": {"volatility": 0.12, "price": 400}
        }
    
    async def _get_liquidity_data(self) -> Dict:
        """获取流动性数据"""
        # 这里应该从交易所API获取真实数据
        return {
            "BTCUSDT": {"liquidity_score": 0.9},
            "ETHUSDT": {"liquidity_score": 0.8},
            "BNBUSDT": {"liquidity_score": 0.7}
        }
    
    async def _stop_all_trading(self):
        """停止所有交易"""
        logger.critical("停止所有交易")
        # 实现停止交易逻辑
    
    async def _liquidate_positions(self):
        """紧急平仓"""
        logger.critical("执行紧急平仓")
        # 实现平仓逻辑
    
    async def _reduce_position(self, symbol: str, ratio: float):
        """减仓"""
        logger.warning(f"减仓操作: {symbol} - 比例: {ratio}")
        # 实现减仓逻辑
    
    async def _increase_hedging(self):
        """增加对冲"""
        logger.warning("增加对冲操作")
        # 实现增加对冲逻辑

# 全局风险监控器实例
risk_monitor: Optional[RiskMonitor] = None

async def get_risk_monitor() -> RiskMonitor:
    """获取风险监控器实例"""
    global risk_monitor
    if risk_monitor is None:
        risk_engine = RiskEngine()
        backtest_manager = BacktestManager()
        risk_monitor = RiskMonitor(risk_engine, backtest_manager)
    return risk_monitor