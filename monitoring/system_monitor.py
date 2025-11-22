"""
系统监控模块
"""
import psutil
import time
import logging
from typing import Dict, Any
from threading import Thread
from .prometheus_client import PrometheusClient

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, prometheus_client: PrometheusClient):
        self.prometheus_client = prometheus_client
        self.is_running = False
        self.monitor_thread = None
    
    def start(self):
        """启动系统监控"""
        self.is_running = True
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("系统监控已启动")
    
    def stop(self):
        """停止系统监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                system_data = self._collect_system_metrics()
                self.prometheus_client.update_system_metrics(system_data)
                time.sleep(10)  # 每10秒更新一次
                
            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                time.sleep(30)  # 错误后等待30秒
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            memory = psutil.virtual_memory()
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            
            # 网络IO
            net_io = psutil.net_io_counters()
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.used,
                "memory_total": memory.total,
                "memory_percent": memory.percent,
                "disk_usage": disk.used,
                "disk_total": disk.total,
                "disk_percent": disk.percent,
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv,
                "process_count": len(psutil.pids())
            }
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {}
    
    def check_system_health(self) -> Dict[str, bool]:
        """检查系统健康状态"""
        try:
            health_status = {
                "cpu": True,
                "memory": True,
                "disk": True,
                "network": True
            }
            
            # 检查CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                health_status["cpu"] = False
                logger.warning(f"CPU使用率过高: {cpu_percent}%")
            
            # 检查内存
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                health_status["memory"] = False
                logger.warning(f"内存使用率过高: {memory.percent}%")
            
            # 检查磁盘
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                health_status["disk"] = False
                logger.warning(f"磁盘使用率过高: {disk.percent}%")
            
            return health_status
            
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}")
            return {"cpu": False, "memory": False, "disk": False, "network": False}
    
    def get_system_alerts(self) -> list:
        """获取系统告警"""
        alerts = []
        
        try:
            system_data = self._collect_system_metrics()
            
            if system_data.get('cpu_usage', 0) > 80:
                alerts.append({
                    "level": "warning",
                    "message": f"CPU使用率过高: {system_data['cpu_usage']}%"
                })
            
            if system_data.get('memory_percent', 0) > 85:
                alerts.append({
                    "level": "warning",
                    "message": f"内存使用率过高: {system_data['memory_percent']}%"
                })
            
            if system_data.get('disk_percent', 0) > 90:
                alerts.append({
                    "level": "critical",
                    "message": f"磁盘使用率过高: {system_data['disk_percent']}%"
                })
                
        except Exception as e:
            logger.error(f"获取系统告警失败: {e}")
        
        return alerts