"""
交易监控模块
"""
import time
import logging
from typing import Dict, Any, List
from threading import Thread
from .prometheus_client import PrometheusClient

logger = logging.getLogger(__name__)


class TradingMonitor:
    """交易监控器"""
    
    def __init__(self, prometheus_client: PrometheusClient):
        self.prometheus_client = prometheus_client
        self.is_running = False
        self.monitor_thread = None
        self.trading_data = {}
        self.risk_alerts = []
    
    def start(self):
        """启动交易监控"""
        self.is_running = True
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("交易监控已启动")
    
    def stop(self):
        """停止交易监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("交易监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 更新交易数据
                self._update_trading_metrics()
                
                # 检查风险指标
                self._check_risk_alerts()
                
                time.sleep(5)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"交易监控错误: {e}")
                time.sleep(10)  # 错误后等待10秒
    
    def update_trading_data(self, exchange: str, symbol: str, trade_data: Dict[str, Any]):
        """更新交易数据"""
        try:
            key = f"{exchange}:{symbol}"
            self.trading_data[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "price": trade_data.get('price', 0),
                "volume": trade_data.get('volume', 0),
                "timestamp": time.time(),
                "last_update": trade_data
            }
            
            # 更新Prometheus指标
            self.prometheus_client.update_trading_metrics(exchange, symbol, trade_data)
            
        except Exception as e:
            logger.error(f"更新交易数据失败: {e}")
    
    def record_trade(self, exchange: str, symbol: str, trade_type: str, quantity: float, price: float):
        """记录交易"""
        try:
            self.prometheus_client.record_trade(exchange, symbol, trade_type, quantity)
            
            # 记录交易详情
            trade_record = {
                "exchange": exchange,
                "symbol": symbol,
                "type": trade_type,
                "quantity": quantity,
                "price": price,
                "timestamp": time.time(),
                "total_value": quantity * price
            }
            
            # 这里可以保存到数据库或日志文件
            logger.info(f"交易记录: {trade_record}")
            
        except Exception as e:
            logger.error(f"记录交易失败: {e}")
    
    def _update_trading_metrics(self):
        """更新交易指标"""
        try:
            # 清理过期数据（超过10分钟）
            current_time = time.time()
            expired_keys = []
            
            for key, data in self.trading_data.items():
                if current_time - data['timestamp'] > 600:  # 10分钟
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.trading_data[key]
                
        except Exception as e:
            logger.error(f"更新交易指标失败: {e}")
    
    def _check_risk_alerts(self):
        """检查风险告警"""
        try:
            current_time = time.time()
            
            # 检查数据更新延迟
            for key, data in self.trading_data.items():
                delay = current_time - data['timestamp']
                if delay > 60:  # 超过60秒没有更新
                    alert = {
                        "level": "warning",
                        "message": f"{key} 数据更新延迟: {delay:.1f}秒",
                        "timestamp": current_time
                    }
                    
                    if alert not in self.risk_alerts:
                        self.risk_alerts.append(alert)
                        logger.warning(alert["message"])
            
            # 清理过期告警（超过1小时）
            self.risk_alerts = [
                alert for alert in self.risk_alerts 
                if current_time - alert['timestamp'] < 3600
            ]
                
        except Exception as e:
            logger.error(f"检查风险告警失败: {e}")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """获取交易摘要"""
        try:
            active_symbols = len(self.trading_data)
            total_volume = sum(data.get('volume', 0) for data in self.trading_data.values())
            
            return {
                "active_symbols": active_symbols,
                "total_volume": total_volume,
                "last_update": time.time(),
                "trading_data": self.trading_data
            }
            
        except Exception as e:
            logger.error(f"获取交易摘要失败: {e}")
            return {}
    
    def get_risk_alerts(self) -> List[Dict[str, Any]]:
        """获取风险告警"""
        return self.risk_alerts.copy()
    
    def update_risk_metrics(self, exchange: str, account_type: str, risk_data: Dict[str, Any]):
        """更新风险指标"""
        try:
            self.prometheus_client.update_risk_metrics(exchange, account_type, risk_data)
            
            # 检查风险阈值
            if risk_data.get('var', 0) > 1000:  # VaR超过1000
                alert = {
                    "level": "critical",
                    "message": f"{exchange} {account_type} VaR过高: {risk_data['var']}",
                    "timestamp": time.time()
                }
                
                if alert not in self.risk_alerts:
                    self.risk_alerts.append(alert)
                    logger.warning(alert["message"])
                    
        except Exception as e:
            logger.error(f"更新风险指标失败: {e}")
    
    def clear_alert(self, alert_message: str):
        """清除特定告警"""
        self.risk_alerts = [
            alert for alert in self.risk_alerts 
            if alert["message"] != alert_message
        ]