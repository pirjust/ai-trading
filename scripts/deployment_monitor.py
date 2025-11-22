#!/usr/bin/env python3
# 部署监控脚本
# 用于监控GitHub到腾讯云宝塔面板的部署过程

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class DeploymentMonitor:
    def __init__(self):
        self.project_root = Path.cwd()
        self.log_dir = self.project_root / "logs"
        self.config_dir = self.project_root / "config"
        
        # 设置日志
        self.setup_logging()
        
        # 监控配置
        self.monitor_config = self.load_monitor_config()
        
        # 部署状态
        self.deployment_status = {
            "start_time": datetime.now().isoformat(),
            "status": "monitoring",
            "checks": {},
            "last_check": None,
            "errors": []
        }
        
    def setup_logging(self):
        """设置日志配置"""
        self.log_dir.mkdir(exist_ok=True)
        
        log_file = self.log_dir / "deployment_monitor.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def load_monitor_config(self):
        """加载监控配置"""
        config_file = self.config_dir / "deployment_checklist.yaml"
        
        if config_file.exists():
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        # 默认配置
        return {
            "check_interval": 30,  # 检查间隔（秒）
            "timeout": 3600,      # 总超时时间（秒）
            "checks": {
                "api_health": {
                    "endpoint": "http://127.0.0.1:8000/health",
                    "timeout": 10,
                    "required": True
                },
                "database": {
                    "command": "python scripts/check_database.py",
                    "timeout": 30,
                    "required": True
                },
                "redis": {
                    "command": "python scripts/check_redis.py", 
                    "timeout": 10,
                    "required": True
                }
            }
        }
        
    def log_check(self, check_name, status, message=""):
        """记录检查结果"""
        timestamp = datetime.now().isoformat()
        
        self.deployment_status["checks"][check_name] = {
            "timestamp": timestamp,
            "status": status,
            "message": message
        }
        
        self.deployment_status["last_check"] = timestamp
        
        level = "INFO" if status == "success" else "ERROR"
        self.logger.log(
            getattr(logging, level), 
            f"{check_name}: {status} - {message}"
        )
        
        if status == "error":
            self.deployment_status["errors"].append({
                "check": check_name,
                "timestamp": timestamp,
                "message": message
            })
            
    def check_api_health(self):
        """检查API健康状态"""
        check_config = self.monitor_config["checks"]["api_health"]
        
        try:
            response = requests.get(
                check_config["endpoint"],
                timeout=check_config["timeout"]
            )
            
            if response.status_code == 200:
                self.log_check("api_health", "success", "API健康检查通过")
                return True
            else:
                self.log_check("api_health", "error", 
                             f"API返回状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_check("api_health", "error", f"API请求失败: {e}")
            return False
            
    def check_database(self):
        """检查数据库连接"""
        check_config = self.monitor_config["checks"]["database"]
        
        try:
            result = subprocess.run(
                check_config["command"],
                shell=True,
                timeout=check_config["timeout"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_check("database", "success", "数据库连接正常")
                return True
            else:
                self.log_check("database", "error", 
                             f"数据库检查失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_check("database", "error", "数据库检查超时")
            return False
        except Exception as e:
            self.log_check("database", "error", f"数据库检查异常: {e}")
            return False
            
    def check_redis(self):
        """检查Redis连接"""
        check_config = self.monitor_config["checks"]["redis"]
        
        try:
            result = subprocess.run(
                check_config["command"],
                shell=True,
                timeout=check_config["timeout"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_check("redis", "success", "Redis连接正常")
                return True
            else:
                self.log_check("redis", "error", 
                             f"Redis检查失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_check("redis", "error", "Redis检查超时")
            return False
        except Exception as e:
            self.log_check("redis", "error", f"Redis检查异常: {e}")
            return False
            
    def check_system_resources(self):
        """检查系统资源"""
        try:
            # 检查磁盘空间
            result = subprocess.run(
                "df -h / | tail -1",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                disk_info = result.stdout.strip().split()
                if len(disk_info) >= 5:
                    usage = disk_info[4].replace('%', '')
                    if int(usage) > 90:
                        self.log_check("system_resources", "warning",
                                     f"磁盘使用率过高: {usage}%")
                    else:
                        self.log_check("system_resources", "success",
                                     f"磁盘使用率: {usage}%")
                        
            # 检查内存使用
            result = subprocess.run(
                "free -h",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_check("system_resources", "success", "内存检查完成")
                
            return True
            
        except Exception as e:
            self.log_check("system_resources", "error", f"系统资源检查异常: {e}")
            return False
            
    def check_service_status(self):
        """检查服务状态"""
        services = ["nginx", "postgresql", "redis-server", "supervisor"]
        
        all_healthy = True
        
        for service in services:
            try:
                result = subprocess.run(
                    f"systemctl is-active {service}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.log_check(f"service_{service}", "success",
                                 f"{service}服务运行正常")
                else:
                    self.log_check(f"service_{service}", "error",
                                 f"{service}服务未运行")
                    all_healthy = False
                    
            except Exception as e:
                self.log_check(f"service_{service}", "error",
                             f"{service}服务检查异常: {e}")
                all_healthy = False
                
        return all_healthy
        
    def run_all_checks(self):
        """运行所有检查"""
        self.logger.info("开始运行部署监控检查...")
        
        checks = [
            ("API健康检查", self.check_api_health),
            ("数据库检查", self.check_database),
            ("Redis检查", self.check_redis),
            ("系统资源检查", self.check_system_resources),
            ("服务状态检查", self.check_service_status)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.logger.error(f"{check_name}执行异常: {e}")
                all_passed = False
                
        return all_passed
        
    def generate_report(self):
        """生成监控报告"""
        report = {
            "monitoring_session": self.deployment_status,
            "summary": {
                "total_checks": len(self.deployment_status["checks"]),
                "successful_checks": len([c for c in self.deployment_status["checks"].values() 
                                        if c["status"] == "success"]),
                "failed_checks": len([c for c in self.deployment_status["checks"].values() 
                                    if c["status"] == "error"]),
                "total_errors": len(self.deployment_status["errors"])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存报告
        report_file = self.log_dir / f"deployment_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"监控报告已保存: {report_file}")
        
        return report
        
    def send_alerts(self, report):
        """发送告警通知"""
        if not self.deployment_status["errors"]:
            return
            
        # 如果有错误，发送通知
        slack_webhook = os.getenv('SLACK_WEBHOOK')
        
        if slack_webhook:
            payload = {
                "text": "🚨 部署监控告警",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*🚨 AI量化交易系统部署监控告警*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*错误数量:* {report['summary']['failed_checks']}"
                            },
                            {
                                "type": "mrkdwn", 
                                "text": f"*检查时间:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*错误详情:*"
                        }
                    }
                ]
            }
            
            # 添加错误详情
            for error in self.deployment_status["errors"][:5]:  # 最多显示5个错误
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• {error['check']}: {error['message']}"
                    }
                })
                
            try:
                response = requests.post(slack_webhook, json=payload, timeout=10)
                if response.status_code == 200:
                    self.logger.info("告警通知发送成功")
                else:
                    self.logger.warning(f"告警通知发送失败: {response.status_code}")
            except Exception as e:
                self.logger.error(f"告警通知发送异常: {e}")
                
    def monitor(self, duration_minutes=60):
        """主监控循环"""
        self.logger.info(f"开始部署监控，持续 {duration_minutes} 分钟")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        check_interval = self.monitor_config.get("check_interval", 30)
        
        while datetime.now() < end_time:
            try:
                # 运行检查
                all_passed = self.run_all_checks()
                
                # 生成报告
                report = self.generate_report()
                
                # 如果有错误，发送告警
                if not all_passed:
                    self.send_alerts(report)
                    
                # 如果所有检查都通过，可以提前结束
                if all_passed and len(self.deployment_status["checks"]) >= 5:
                    self.logger.info("所有检查通过，监控任务完成")
                    break
                    
                # 等待下一次检查
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("监控被用户中断")
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(check_interval)  # 继续监控
                
        # 最终报告
        final_report = self.generate_report()
        self.logger.info("部署监控任务结束")
        
        return final_report
        
    def continuous_monitoring(self):
        """持续监控模式"""
        self.logger.info("启动持续监控模式")
        
        while True:
            try:
                self.monitor(duration_minutes=60)  # 每60分钟重新开始
                time.sleep(300)  # 等待5分钟后继续
                
            except KeyboardInterrupt:
                self.logger.info("持续监控被用户中断")
                break
            except Exception as e:
                self.logger.error(f"持续监控异常: {e}")
                time.sleep(60)  # 等待1分钟后重试

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI量化交易系统部署监控')
    parser.add_argument('--duration', type=int, default=60,
                       help='监控持续时间（分钟）')
    parser.add_argument('--continuous', action='store_true',
                       help='持续监控模式')
    parser.add_argument('--check-interval', type=int, default=30,
                       help='检查间隔（秒）')
                       
    args = parser.parse_args()
    
    monitor = DeploymentMonitor()
    
    # 更新检查间隔
    if args.check_interval:
        monitor.monitor_config["check_interval"] = args.check_interval
        
    try:
        if args.continuous:
            monitor.continuous_monitoring()
        else:
            report = monitor.monitor(args.duration)
            
            # 打印总结
            summary = report["summary"]
            print(f"\n=== 监控报告总结 ===")
            print(f"总检查次数: {summary['total_checks']}")
            print(f"成功检查: {summary['successful_checks']}")
            print(f"失败检查: {summary['failed_checks']}")
            print(f"总错误数: {summary['total_errors']}")
            
            if summary['failed_checks'] > 0:
                sys.exit(1)
                
    except Exception as e:
        print(f"监控执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()