"""
Prometheus监控客户端
"""
import time
import logging
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Prometheus监控客户端"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        
        # 交易指标
        self.trades_total = Counter('trading_trades_total', 'Total number of trades', ['exchange', 'symbol', 'type'])
        self.trading_volume = Counter('trading_volume_total', 'Total trading volume', ['exchange', 'symbol'])
        self.current_price = Gauge('trading_current_price', 'Current price', ['exchange', 'symbol'])
        self.profit_loss = Gauge('trading_profit_loss', 'Profit/Loss', ['exchange', 'symbol'])
        
        # 系统指标
        self.system_uptime = Gauge('system_uptime_seconds', 'System uptime in seconds')
        self.memory_usage = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        
        # 风险指标
        self.risk_value = Gauge('risk_value_at_risk', 'Value at Risk', ['exchange', 'account_type'])
        self.max_drawdown = Gauge('risk_max_drawdown', 'Maximum drawdown', ['exchange', 'account_type'])
        self.sharpe_ratio = Gauge('risk_sharpe_ratio', 'Sharpe ratio', ['exchange', 'account_type'])
        
        # 性能指标
        self.request_duration = Histogram('api_request_duration_seconds', 'API request duration')
        self.data_latency = Histogram('data_latency_seconds', 'Data processing latency')
        
        self.start_time = time.time()
    
    def start_server(self):
        """启动Prometheus HTTP服务器"""
        try:
            start_http_server(self.port)
            logger.info(f"Prometheus监控服务器已启动，端口: {self.port}")
        except Exception as e:
            logger.error(f"启动Prometheus服务器失败: {e}")
    
    def update_trading_metrics(self, exchange: str, symbol: str, trade_data: Dict[str, Any]):
        """更新交易指标"""
        try:
            self.current_price.labels(exchange=exchange, symbol=symbol).set(trade_data.get('price', 0))
            
            if 'volume' in trade_data:
                self.trading_volume.labels(exchange=exchange, symbol=symbol).inc(trade_data['volume'])
            
            if 'pnl' in trade_data:
                self.profit_loss.labels(exchange=exchange, symbol=symbol).set(trade_data['pnl'])
                
        except Exception as e:
            logger.error(f"更新交易指标失败: {e}")
    
    def record_trade(self, exchange: str, symbol: str, trade_type: str, quantity: float):
        """记录交易"""
        try:
            self.trades_total.labels(exchange=exchange, symbol=symbol, type=trade_type).inc()
            self.trading_volume.labels(exchange=exchange, symbol=symbol).inc(quantity)
        except Exception as e:
            logger.error(f"记录交易失败: {e}")
    
    def update_risk_metrics(self, exchange: str, account_type: str, risk_data: Dict[str, Any]):
        """更新风险指标"""
        try:
            if 'var' in risk_data:
                self.risk_value.labels(exchange=exchange, account_type=account_type).set(risk_data['var'])
            
            if 'max_drawdown' in risk_data:
                self.max_drawdown.labels(exchange=exchange, account_type=account_type).set(risk_data['max_drawdown'])
            
            if 'sharpe_ratio' in risk_data:
                self.sharpe_ratio.labels(exchange=exchange, account_type=account_type).set(risk_data['sharpe_ratio'])
                
        except Exception as e:
            logger.error(f"更新风险指标失败: {e}")
    
    def update_system_metrics(self, system_data: Dict[str, Any]):
        """更新系统指标"""
        try:
            self.system_uptime.set(time.time() - self.start_time)
            
            if 'memory_usage' in system_data:
                self.memory_usage.set(system_data['memory_usage'])
            
            if 'cpu_usage' in system_data:
                self.cpu_usage.set(system_data['cpu_usage'])
                
        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")
    
    def record_request_duration(self, duration: float):
        """记录请求持续时间"""
        try:
            self.request_duration.observe(duration)
        except Exception as e:
            logger.error(f"记录请求持续时间失败: {e}")
    
    def record_data_latency(self, latency: float):
        """记录数据延迟"""
        try:
            self.data_latency.observe(latency)
        except Exception as e:
            logger.error(f"记录数据延迟失败: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "uptime": time.time() - self.start_time,
            "trades_total": {
                "value": self.trades_total._value.get(),
                "labels": list(self.trades_total._metrics.keys())
            },
            "trading_volume": {
                "value": self.trading_volume._value.get(),
                "labels": list(self.trading_volume._metrics.keys())
            }
        }