#!/usr/bin/env python3
"""
AI量化交易系统 - 系统监控脚本
"""

import psutil
import time
import logging
import requests
import json
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    def __init__(self, config_file: str = "config/monitor_config.json"):
        self.config = self._load_config(config_file)
        self.setup_logging()
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载监控配置"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # 默认配置
            return {
                "monitor_interval": 60,
                "alert_thresholds": {
                    "cpu_usage": 80,
                    "memory_usage": 85,
                    "disk_usage": 90,
                    "network_traffic": 1000000000
                },
                "webhook_url": "http://localhost:8000/api/alerts",
                "log_file": "logs/system_monitor.log"
            }
    
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_system_metrics(self) -> Dict[str, float]:
        """获取系统指标"""
        metrics = {}
        
        # CPU使用率
        metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        metrics['memory_usage'] = memory.percent
        metrics['memory_used_gb'] = memory.used / (1024**3)
        metrics['memory_total_gb'] = memory.total / (1024**3)
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        metrics['disk_usage'] = disk.percent
        metrics['disk_used_gb'] = disk.used / (1024**3)
        metrics['disk_total_gb'] = disk.total / (1024**3)
        
        # 网络流量
        net_io = psutil.net_io_counters()
        metrics['network_sent_mbps'] = net_io.bytes_sent / (1024**2)
        metrics['network_recv_mbps'] = net_io.bytes_recv / (1024**2)
        
        # 系统负载
        load_avg = psutil.getloadavg()
        metrics['load_1min'] = load_avg[0]
        metrics['load_5min'] = load_avg[1]
        metrics['load_15min'] = load_avg[2]
        
        # 进程数量
        metrics['process_count'] = len(psutil.pids())
        
        return metrics
    
    def check_service_health(self) -> Dict[str, bool]:
        """检查服务健康状态"""
        services = {
            'web_app': 'http://localhost:8000/health',
            'postgres': 'postgresql',
            'redis': 'redis-server',
            'nginx': 'nginx'
        }
        
        health_status = {}
        
        # 检查Web应用
        try:
            response = requests.get(services['web_app'], timeout=5)
            health_status['web_app'] = response.status_code == 200
        except:
            health_status['web_app'] = False
        
        # 检查系统服务
        for service_name, service_cmd in [('postgres', 'postgresql'), ('redis', 'redis-server'), ('nginx', 'nginx')]:
            try:
                result = subprocess.run(['systemctl', 'is-active', service_cmd], 
                                       capture_output=True, text=True)
                health_status[service_name] = result.returncode == 0
            except:
                health_status[service_name] = False
        
        return health_status
    
    def check_trading_metrics(self) -> Dict[str, Any]:
        """检查交易相关指标"""
        try:
            response = requests.get('http://localhost:8000/api/metrics', timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {
            'active_strategies': 0,
            'total_orders': 0,
            'success_rate': 0.0,
            'api_errors': 0,
            'risk_alerts': 0
        }
    
    def check_alerts(self, metrics: Dict[str, float], health_status: Dict[str, bool]) -> list:
        """检查告警条件"""
        alerts = []
        thresholds = self.config['alert_thresholds']
        
        # CPU使用率告警
        if metrics['cpu_usage'] > thresholds['cpu_usage']:
            alerts.append({
                'level': 'warning',
                'message': f'CPU使用率过高: {metrics["cpu_usage"]:.1f}%',
                'metric': 'cpu_usage',
                'value': metrics['cpu_usage']
            })
        
        # 内存使用率告警
        if metrics['memory_usage'] > thresholds['memory_usage']:
            alerts.append({
                'level': 'warning',
                'message': f'内存使用率过高: {metrics["memory_usage"]:.1f}%',
                'metric': 'memory_usage',
                'value': metrics['memory_usage']
            })
        
        # 磁盘使用率告警
        if metrics['disk_usage'] > thresholds['disk_usage']:
            alerts.append({
                'level': 'critical',
                'message': f'磁盘使用率过高: {metrics["disk_usage"]:.1f}%',
                'metric': 'disk_usage',
                'value': metrics['disk_usage']
            })
        
        # 服务健康状态告警
        for service, status in health_status.items():
            if not status:
                alerts.append({
                    'level': 'critical',
                    'message': f'服务异常: {service}',
                    'metric': 'service_health',
                    'value': 0
                })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """发送告警"""
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'level': alert['level'],
                'message': alert['message'],
                'metric': alert['metric'],
                'value': alert['value']
            }
            
            response = requests.post(
                self.config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"告警发送成功: {alert['message']}")
            else:
                self.logger.error(f"告警发送失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"发送告警失败: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        metrics = self.get_system_metrics()
        health_status = self.check_service_health()
        trading_metrics = self.check_trading_metrics()
        alerts = self.check_alerts(metrics, health_status)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'health_status': health_status,
            'trading_metrics': trading_metrics,
            'alerts': alerts,
            'overall_status': 'healthy' if not alerts else 'warning'
        }
        
        # 发送严重告警
        critical_alerts = [alert for alert in alerts if alert['level'] == 'critical']
        for alert in critical_alerts:
            self.send_alert(alert)
        
        return report
    
    def run_monitor(self):
        """运行监控循环"""
        self.logger.info("启动系统监控服务")
        
        while True:
            try:
                report = self.generate_report()
                
                # 记录监控数据
                self.logger.info(f"监控报告 - 状态: {report['overall_status']}, "
                               f"CPU: {report['metrics']['cpu_usage']:.1f}%, "
                               f"内存: {report['metrics']['memory_usage']:.1f}%")
                
                # 如果有告警，记录详细信息
                if report['alerts']:
                    for alert in report['alerts']:
                        self.logger.warning(f"{alert['level'].upper()}: {alert['message']}")
                
                # 保存报告到文件
                self.save_report(report)
                
            except Exception as e:
                self.logger.error(f"监控执行错误: {e}")
            
            # 等待下一次监控
            time.sleep(self.config['monitor_interval'])
    
    def save_report(self, report: Dict[str, Any]):
        """保存监控报告"""
        try:
            report_file = f"logs/monitor_report_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 读取现有报告
            try:
                with open(report_file, 'r') as f:
                    existing_reports = json.load(f)
            except:
                existing_reports = []
            
            # 添加新报告
            existing_reports.append(report)
            
            # 只保留最近100条记录
            if len(existing_reports) > 100:
                existing_reports = existing_reports[-100:]
            
            # 保存报告
            with open(report_file, 'w') as f:
                json.dump(existing_reports, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

if __name__ == "__main__":
    import subprocess
    
    monitor = SystemMonitor()
    monitor.run_monitor()