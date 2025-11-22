"""
风控引擎 - 核心风险管理模块
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    max_drawdown: float  # 最大回撤
    sharpe_ratio: float  # 夏普比率
    sortino_ratio: float  # 索提诺比率
    volatility: float  # 波动率
    beta: float  # Beta值
    correlation_matrix: Optional[np.ndarray] = None  # 相关性矩阵


@dataclass
class RiskAlert:
    """风险警报"""
    alert_id: str
    risk_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    symbol: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    action_required: Optional[str] = None


class RiskEngine:
    """风控引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.alerts: List[RiskAlert] = []
        self.position_limits = {}
        self.risk_metrics = {}
        self.market_data = {}
        self.portfolio_data = {}
        
        # 风险阈值
        self.risk_thresholds = {
            'max_position_size': config.get('max_position_size', 0.1),
            'max_daily_loss': config.get('max_daily_loss', 0.05),
            'max_drawdown': config.get('max_drawdown', 0.15),
            'max_var_95': config.get('max_var_95', 0.03),
            'min_sharpe_ratio': config.get('min_sharpe_ratio', 0.5),
            'max_volatility': config.get('max_volatility', 0.3)
        }
        
        # 监控间隔
        self.check_interval = config.get('check_interval', 60)  # 秒
        
        self.callbacks = []
    
    def add_callback(self, callback):
        """添加风险警报回调"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """移除风险警报回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def notify_callbacks(self, alert: RiskAlert):
        """通知所有回调"""
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"风险警报回调失败: {e}")
    
    async def start(self):
        """启动风控引擎"""
        self.is_running = True
        logger.info("风控引擎已启动")
        
        # 启动风险监控循环
        asyncio.create_task(self._risk_monitoring_loop())
    
    async def stop(self):
        """停止风控引擎"""
        self.is_running = False
        logger.info("风控引擎已停止")
    
    async def _risk_monitoring_loop(self):
        """风险监控循环"""
        while self.is_running:
            try:
                # 执行风险检查
                await self._perform_risk_checks()
                
                # 等待下一次检查
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"风险监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _perform_risk_checks(self):
        """执行风险检查"""
        try:
            # 检查仓位风险
            await self._check_position_risks()
            
            # 检查市场风险
            await self._check_market_risks()
            
            # 检查组合风险
            await self._check_portfolio_risks()
            
            # 检查系统风险
            await self._check_system_risks()
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
    
    async def _check_position_risks(self):
        """检查仓位风险"""
        for symbol, position_data in self.portfolio_data.items():
            try:
                # 检查单仓位大小
                position_size = position_data.get('position_size', 0)
                max_position = self.risk_thresholds['max_position_size']
                
                if abs(position_size) > max_position:
                    await self._create_alert(
                        risk_type="position_size",
                        severity="high",
                        message=f"{symbol} 仓位过大: {position_size:.2%} > {max_position:.2%}",
                        symbol=symbol,
                        value=abs(position_size),
                        threshold=max_position,
                        action_required="reduce_position"
                    )
                
                # 检查止损
                current_price = self.market_data.get(symbol, {}).get('price', 0)
                entry_price = position_data.get('entry_price', 0)
                
                if current_price > 0 and entry_price > 0:
                    pnl_pct = (current_price - entry_price) / entry_price
                    
                    # 检查最大日损失
                    if pnl_pct < -self.risk_thresholds['max_daily_loss']:
                        await self._create_alert(
                            risk_type="daily_loss",
                            severity="critical",
                            message=f"{symbol} 日损失过大: {pnl_pct:.2%}",
                            symbol=symbol,
                            value=pnl_pct,
                            threshold=-self.risk_thresholds['max_daily_loss'],
                            action_required="stop_loss"
                        )
                
            except Exception as e:
                logger.error(f"检查 {symbol} 仓位风险失败: {e}")
    
    async def _check_market_risks(self):
        """检查市场风险"""
        try:
            # 检查市场波动率
            for symbol, market_data in self.market_data.items():
                price_data = market_data.get('price_history', [])
                
                if len(price_data) >= 30:  # 需要30个数据点计算波动率
                    returns = np.diff(price_data) / price_data[:-1]
                    volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
                    
                    if volatility > self.risk_thresholds['max_volatility']:
                        await self._create_alert(
                            risk_type="high_volatility",
                            severity="medium",
                            message=f"{symbol} 市场波动率过高: {volatility:.2%}",
                            symbol=symbol,
                            value=volatility,
                            threshold=self.risk_thresholds['max_volatility'],
                            action_required="reduce_position"
                        )
                
        except Exception as e:
            logger.error(f"检查市场风险失败: {e}")
    
    async def _check_portfolio_risks(self):
        """检查组合风险"""
        try:
            # 计算组合VaR
            var_metrics = await self.calculate_var()
            
            if var_metrics and var_metrics.var_95 > self.risk_thresholds['max_var_95']:
                await self._create_alert(
                    risk_type="portfolio_var",
                    severity="high",
                    message=f"组合VaR过高: {var_metrics.var_95:.2%}",
                    value=var_metrics.var_95,
                    threshold=self.risk_thresholds['max_var_95'],
                    action_required="reduce_risk"
                )
            
            # 检查最大回撤
            drawdown = await self.calculate_max_drawdown()
            
            if drawdown > self.risk_thresholds['max_drawdown']:
                await self._create_alert(
                    risk_type="max_drawdown",
                    severity="critical",
                    message=f"组合最大回撤过大: {drawdown:.2%}",
                    value=drawdown,
                    threshold=self.risk_thresholds['max_drawdown'],
                    action_required="emergency_stop"
                )
                
        except Exception as e:
            logger.error(f"检查组合风险失败: {e}")
    
    async def _check_system_risks(self):
        """检查系统风险"""
        try:
            # 检查API连接状态
            # 检查数据延迟
            # 检查系统负载等
            pass
            
        except Exception as e:
            logger.error(f"检查系统风险失败: {e}")
    
    async def _create_alert(self, risk_type: str, severity: str, message: str,
                          symbol: str = None, value: float = None, 
                          threshold: float = None, action_required: str = None):
        """创建风险警报"""
        alert = RiskAlert(
            alert_id=f"{risk_type}_{int(time.time())}",
            risk_type=risk_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            symbol=symbol,
            value=value,
            threshold=threshold,
            action_required=action_required
        )
        
        # 添加到警报列表
        self.alerts.append(alert)
        
        # 保持最近1000个警报
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # 通知回调
        self.notify_callbacks(alert)
        
        # 记录日志
        log_level = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"[{severity.upper()}] {message}")
    
    def update_market_data(self, symbol: str, data: Dict[str, Any]):
        """更新市场数据"""
        if symbol not in self.market_data:
            self.market_data[symbol] = {
                'price_history': [],
                'volume_history': [],
                'timestamp_history': []
            }
        
        # 更新最新数据
        self.market_data[symbol].update(data)
        
        # 保存历史数据（保留最近1000个数据点）
        if 'price' in data:
            price_history = self.market_data[symbol]['price_history']
            price_history.append(data['price'])
            
            if len(price_history) > 1000:
                price_history.pop(0)
            
            self.market_data[symbol]['price_history'] = price_history
    
    def update_portfolio_data(self, symbol: str, data: Dict[str, Any]):
        """更新组合数据"""
        self.portfolio_data[symbol] = data
    
    async def calculate_var(self, confidence_levels: List[float] = [0.95, 0.99],
                          time_horizon: int = 1) -> Optional[RiskMetrics]:
        """计算风险价值(VaR)"""
        try:
            # 收集所有资产收益率
            returns_data = []
            
            for symbol, market_data in self.market_data.items():
                price_history = market_data.get('price_history', [])
                
                if len(price_history) >= 100:  # 需要足够的历史数据
                    returns = np.diff(price_history) / price_history[:-1]
                    returns_data.append(returns)
            
            if not returns_data:
                return None
            
            # 计算组合收益率
            portfolio_weights = []
            for symbol in self.market_data.keys():
                position_data = self.portfolio_data.get(symbol, {})
                weight = position_data.get('weight', 0)
                portfolio_weights.append(weight)
            
            # 标准化权重
            total_weight = sum(portfolio_weights)
            if total_weight > 0:
                portfolio_weights = [w / total_weight for w in portfolio_weights]
            else:
                portfolio_weights = [1.0 / len(portfolio_weights)] * len(portfolio_weights)
            
            # 计算组合收益率
            portfolio_returns = np.zeros(len(returns_data[0]))
            for i, returns in enumerate(returns_data):
                portfolio_returns += returns * portfolio_weights[i]
            
            # 计算VaR
            var_values = {}
            for confidence in confidence_levels:
                var_values[f'var_{int(confidence*100)}'] = -np.percentile(portfolio_returns, (1-confidence)*100)
            
            # 计算其他风险指标
            volatility = np.std(portfolio_returns) * np.sqrt(252)
            mean_return = np.mean(portfolio_returns) * 252
            
            # 夏普比率
            risk_free_rate = 0.02  # 假设无风险利率2%
            sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # 索提诺比率
            downside_returns = portfolio_returns[portfolio_returns < 0]
            downside_volatility = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = (mean_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
            
            return RiskMetrics(
                var_95=var_values.get('var_95', 0),
                var_99=var_values.get('var_99', 0),
                max_drawdown=await self.calculate_max_drawdown(),
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                volatility=volatility,
                beta=1.0,  # 需要市场数据计算
                correlation_matrix=None
            )
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return None
    
    async def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        try:
            # 计算组合价值曲线
            portfolio_values = []
            
            for i in range(100):  # 假设100个时间点
                portfolio_value = 0
                for symbol, market_data in self.market_data.items():
                    price_history = market_data.get('price_history', [])
                    if i < len(price_history):
                        price = price_history[i]
                    else:
                        price = price_history[-1] if price_history else 0
                    
                    position_data = self.portfolio_data.get(symbol, {})
                    position_size = position_data.get('position_size', 0)
                    portfolio_value += price * position_size
                
                portfolio_values.append(portfolio_value)
            
            if len(portfolio_values) < 2:
                return 0.0
            
            # 计算回撤
            peak = np.maximum.accumulate(portfolio_values)
            drawdown = (peak - portfolio_values) / peak
            
            return np.max(drawdown)
            
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return 0.0
    
    def get_risk_metrics(self, symbol: str = None) -> Dict[str, Any]:
        """获取风险指标"""
        if symbol:
            return self.risk_metrics.get(symbol, {})
        return self.risk_metrics.copy()
    
    def get_active_alerts(self, severity: str = None, 
                         risk_type: str = None) -> List[RiskAlert]:
        """获取活跃警报"""
        alerts = self.alerts.copy()
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if risk_type:
            alerts = [a for a in alerts if a.risk_type == risk_type]
        
        # 只返回最近24小时的警报
        cutoff_time = datetime.now() - timedelta(hours=24)
        alerts = [a for a in alerts if a.timestamp > cutoff_time]
        
        return alerts
    
    def clear_alerts(self, older_than_hours: int = 24):
        """清除过期警报"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """更新风险阈值"""
        self.risk_thresholds.update(new_thresholds)
        logger.info(f"风险阈值已更新: {new_thresholds}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        recent_alerts = self.get_active_alerts()
        
        alert_counts = {}
        for alert in recent_alerts:
            alert_counts[alert.severity] = alert_counts.get(alert.severity, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'alert_counts': alert_counts,
            'latest_alert': recent_alerts[-1] if recent_alerts else None,
            'risk_thresholds': self.risk_thresholds,
            'monitored_symbols': list(self.market_data.keys()),
            'portfolio_value': self._calculate_portfolio_value(),
            'is_running': self.is_running
        }
    
    def _calculate_portfolio_value(self) -> float:
        """计算组合总价值"""
        total_value = 0.0
        
        for symbol, market_data in self.market_data.items():
            current_price = market_data.get('price', 0)
            position_data = self.portfolio_data.get(symbol, {})
            position_size = position_data.get('position_size', 0)
            
            total_value += current_price * position_size
        
        return total_value


# 使用示例
async def example_usage():
    """使用示例"""
    # 风控引擎配置
    config = {
        'max_position_size': 0.1,
        'max_daily_loss': 0.05,
        'max_drawdown': 0.15,
        'max_var_95': 0.03,
        'min_sharpe_ratio': 0.5,
        'max_volatility': 0.3,
        'check_interval': 30
    }
    
    # 创建风控引擎
    risk_engine = RiskEngine(config)
    
    def alert_callback(alert: RiskAlert):
        print(f"风险警报: {alert.message}")
    
    risk_engine.add_callback(alert_callback)
    
    try:
        # 启动风控引擎
        await risk_engine.start()
        
        # 模拟市场数据
        market_data = {
            'price': 50000.0,
            'price_history': [49000, 49500, 48500, 49000, 50000],
            'volume': 1000.0
        }
        risk_engine.update_market_data('BTCUSDT', market_data)
        
        # 模拟组合数据
        portfolio_data = {
            'position_size': 0.05,
            'entry_price': 48000.0,
            'weight': 0.3
        }
        risk_engine.update_portfolio_data('BTCUSDT', portfolio_data)
        
        # 获取风险摘要
        summary = risk_engine.get_risk_summary()
        print(f"风险摘要: {summary}")
        
        # 运行一段时间
        await asyncio.sleep(60)
        
        # 停止风控引擎
        await risk_engine.stop()
        
    except Exception as e:
        print(f"示例执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())