#!/usr/bin/env python3
"""
AI量化交易系统健康检查脚本
用于自动化健康检查和监控
"""

import sys
import time
import requests
import psutil
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json
import subprocess
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ai-trading-health.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.checks = []
        self.results = {}
        
        # 默认配置
        self.default_config = {
            'api_url': 'http://127.0.0.1:8000',
            'timeout': 10,
            'thresholds': {
                'cpu_usage': 80,
                'memory_usage': 85,
                'disk_usage': 90,
                'response_time': 5000,
            }
        }
        
        # 合并配置
        self.config = {**self.default_config, **self.config}
        
    def register_check(self, name: str, check_func, critical: bool = False):
        """注册健康检查"""
        self.checks.append({
            'name': name,
            'func': check_func,
            'critical': critical
        })
    
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            memory = psutil.virtual_memory()
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            
            # 网络连接
            net_io = psutil.net_io_counters()
            
            # 进程数量
            process_count = len(psutil.pids())
            
            result = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_used': memory.used,
                'memory_total': memory.total,
                'disk_usage': disk.percent,
                'disk_used': disk.used,
                'disk_total': disk.total,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'process_count': process_count,
                'status': 'healthy' if cpu_percent < self.config['thresholds']['cpu_usage'] 
                         and memory.percent < self.config['thresholds']['memory_usage'] 
                         and disk.percent < self.config['thresholds']['disk_usage'] else 'warning'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"系统资源检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_api_health(self) -> Dict[str, Any]:
        """检查API健康状态"""
        try:
            start_time = time.time()
            
            response = requests.get(
                f"{self.config['api_url']}/health",
                timeout=self.config['timeout']
            )
            
            response_time = (time.time() - start_time) * 1000  # 毫秒
            
            result = {
                'status_code': response.status_code,
                'response_time': response_time,
                'status': 'healthy' if response.status_code == 200 
                         and response_time < self.config['thresholds']['response_time'] else 'warning'
            }
            
            # 尝试解析响应内容
            try:
                data = response.json()
                result.update(data)
            except:
                pass
                
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API健康检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 检查PostgreSQL
            postgres_result = subprocess.run(
                ['pg_isready', '-h', 'localhost', '-p', '5432'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 检查Redis
            redis_result = subprocess.run(
                ['redis-cli', '-h', 'localhost', '-p', '6379', 'ping'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            result = {
                'postgresql': 'healthy' if postgres_result.returncode == 0 else 'error',
                'redis': 'healthy' if 'PONG' in redis_result.stdout else 'error',
                'status': 'healthy' if postgres_result.returncode == 0 and 'PONG' in redis_result.stdout else 'error'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_service_status(self) -> Dict[str, Any]:
        """检查服务状态"""
        try:
            services = ['nginx', 'postgresql', 'redis', 'supervisor']
            status = {}
            
            for service in services:
                try:
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    status[service] = result.stdout.strip()
                    
                except Exception as e:
                    status[service] = 'unknown'
                    logger.warning(f"检查服务 {service} 状态失败: {e}")
            
            # 检查应用进程
            app_processes = []
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'uvicorn' in str(process.info['cmdline']):
                        app_processes.append({
                            'pid': process.info['pid'],
                            'name': process.info['name']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            result = {
                'services': status,
                'app_processes': app_processes,
                'status': 'healthy' if all(s == 'active' for s in status.values()) 
                         and len(app_processes) > 0 else 'warning'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"服务状态检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            partitions = []
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                    
                except PermissionError:
                    # 跳过无权限访问的分区
                    continue
            
            critical_partitions = [
                p for p in partitions 
                if p['percent'] > self.config['thresholds']['disk_usage']
            ]
            
            result = {
                'partitions': partitions,
                'critical_count': len(critical_partitions),
                'status': 'healthy' if len(critical_partitions) == 0 else 'warning'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"磁盘空间检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_log_files(self) -> Dict[str, Any]:
        """检查日志文件"""
        try:
            log_files = [
                '/var/log/ai-trading/api.log',
                '/var/log/ai-trading/monitor.log',
                '/var/log/nginx/access.log',
                '/var/log/nginx/error.log'
            ]
            
            log_status = {}
            
            for log_file in log_files:
                try:
                    if os.path.exists(log_file):
                        # 检查文件大小
                        size = os.path.getsize(log_file)
                        
                        # 检查最近错误（最后100行）
                        if size > 0:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()[-100:]
                                error_count = sum(1 for line in lines if 'ERROR' in line.upper())
                        else:
                            error_count = 0
                        
                        log_status[log_file] = {
                            'exists': True,
                            'size': size,
                            'error_count': error_count
                        }
                    else:
                        log_status[log_file] = {'exists': False}
                        
                except Exception as e:
                    log_status[log_file] = {'error': str(e)}
            
            total_errors = sum(
                status.get('error_count', 0) 
                for status in log_status.values() 
                if isinstance(status, dict)
            )
            
            result = {
                'log_files': log_status,
                'total_errors': total_errors,
                'status': 'healthy' if total_errors == 0 else 'warning'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"日志文件检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        logger.info("开始运行健康检查...")
        
        start_time = time.time()
        
        # 注册检查
        self.register_check('system_resources', self.check_system_resources, critical=True)
        self.register_check('api_health', self.check_api_health, critical=True)
        self.register_check('database_connection', self.check_database_connection, critical=True)
        self.register_check('service_status', self.check_service_status, critical=True)
        self.register_check('disk_space', self.check_disk_space)
        self.register_check('log_files', self.check_log_files)
        
        # 运行检查
        results = {}
        critical_failures = 0
        
        for check in self.checks:
            try:
                check_start = time.time()
                result = check['func']()
                check_time = time.time() - check_start
                
                result['duration'] = check_time
                results[check['name']] = result
                
                # 统计关键检查失败
                if check['critical'] and result.get('status') == 'error':
                    critical_failures += 1
                    
                logger.info(f"检查 {check['name']}: {result.get('status', 'unknown')} ({check_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"执行检查 {check['name']} 失败: {e}")
                results[check['name']] = {'status': 'error', 'error': str(e)}
                
                if check['critical']:
                    critical_failures += 1
        
        total_time = time.time() - start_time
        
        # 汇总结果
        overall_status = 'healthy'
        if critical_failures > 0:
            overall_status = 'critical'
        elif any(result.get('status') == 'warning' for result in results.values()):
            overall_status = 'warning'
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'total_checks': len(self.checks),
            'critical_failures': critical_failures,
            'total_time': total_time,
            'results': results
        }
        
        logger.info(f"健康检查完成: {overall_status} (耗时: {total_time:.2f}s)")
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any]) -> str:
        """生成健康检查报告"""
        report = []
        
        report.append("=" * 60)
        report.append("AI量化交易系统健康检查报告")
        report.append("=" * 60)
        report.append(f"检查时间: {summary['timestamp']}")
        report.append(f"总体状态: {summary['overall_status'].upper()}")
        report.append(f"检查数量: {summary['total_checks']}")
        report.append(f"关键失败: {summary['critical_failures']}")
        report.append(f"总耗时: {summary['total_time']:.2f}秒")
        report.append("")
        
        # 详细结果
        for check_name, result in summary['results'].items():
            status = result.get('status', 'unknown')
            duration = result.get('duration', 0)
            
            status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'warning' else "❌"
            
            report.append(f"{status_icon} {check_name}: {status} ({duration:.2f}s)")
            
            # 显示详细信息
            if status == 'warning' or status == 'error':
                for key, value in result.items():
                    if key not in ['status', 'duration']:
                        if isinstance(value, dict):
                            report.append(f"    {key}:")
                            for k, v in value.items():
                                report.append(f"      {k}: {v}")
                        else:
                            report.append(f"    {key}: {value}")
        
        report.append("")
        
        # 建议
        if summary['overall_status'] == 'critical':
            report.append("🚨 紧急建议:")
            report.append("1. 立即检查关键服务状态")
            report.append("2. 查看错误日志进行故障排除")
            report.append("3. 考虑执行回滚操作")
        elif summary['overall_status'] == 'warning':
            report.append("⚠️ 警告建议:")
            report.append("1. 监控资源使用情况")
            report.append("2. 清理不必要的文件")
            report.append("3. 优化系统配置")
        else:
            report.append("✅ 系统运行正常")
        
        return "\n".join(report)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI量化交易系统健康检查')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    # 创建检查器
    checker = HealthChecker(config)
    
    # 运行检查
    summary = checker.run_all_checks()
    
    # 生成报告
    report = checker.generate_report(summary)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        logger.info(f"报告已保存到: {args.output}")
    
    if args.verbose or summary['overall_status'] != 'healthy':
        print(report)
    
    # 返回退出码
    if summary['overall_status'] == 'critical':
        sys.exit(2)
    elif summary['overall_status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()