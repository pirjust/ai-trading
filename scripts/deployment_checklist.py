#!/usr/bin/env python3
"""
AI量化交易系统部署检查清单
自动检查部署环境和配置状态
"""

import os
import sys
import subprocess
import json
import requests
import psutil
from datetime import datetime
from typing import Dict, List, Tuple


class DeploymentChecker:
    """部署检查器"""
    
    def __init__(self):
        self.checks = []
        self.results = {}
        self.server_info = {}
    
    def check_system_resources(self) -> Tuple[bool, str]:
        """检查系统资源"""
        try:
            # CPU检查
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存检查
            memory = psutil.virtual_memory()
            
            # 磁盘检查
            disk = psutil.disk_usage('/')
            
            results = []
            
            # CPU使用率
            if cpu_percent > 90:
                results.append(f"❌ CPU使用率过高: {cpu_percent}%")
            else:
                results.append(f"✅ CPU使用率正常: {cpu_percent}%")
            
            # 内存使用率
            if memory.percent > 85:
                results.append(f"❌ 内存使用率过高: {memory.percent}%")
            else:
                results.append(f"✅ 内存使用率正常: {memory.percent}%")
            
            # 磁盘使用率
            if disk.percent > 90:
                results.append(f"❌ 磁盘使用率过高: {disk.percent}%")
            else:
                results.append(f"✅ 磁盘使用率正常: {disk.percent}%")
            
            success = cpu_percent <= 90 and memory.percent <= 85 and disk.percent <= 90
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 系统资源检查失败: {e}"
    
    def check_network_connectivity(self) -> Tuple[bool, str]:
        """检查网络连接"""
        try:
            results = []
            
            # 检查本地网络
            try:
                subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                             capture_output=True, timeout=5)
                results.append("✅ 外网连接正常")
            except:
                results.append("❌ 外网连接失败")
            
            # 检查DNS解析
            try:
                subprocess.run(['nslookup', 'github.com'], 
                             capture_output=True, timeout=5)
                results.append("✅ DNS解析正常")
            except:
                results.append("❌ DNS解析失败")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 网络连接检查失败: {e}"
    
    def check_baota_panel(self) -> Tuple[bool, str]:
        """检查宝塔面板"""
        try:
            results = []
            
            # 检查宝塔服务状态
            try:
                result = subprocess.run(['systemctl', 'status', 'bt'], 
                                     capture_output=True, text=True)
                if 'active (running)' in result.stdout:
                    results.append("✅ 宝塔面板服务运行正常")
                else:
                    results.append("❌ 宝塔面板服务未运行")
            except:
                results.append("❌ 宝塔面板服务检查失败")
            
            # 检查面板端口
            try:
                result = subprocess.run(['netstat', '-tlnp'], 
                                     capture_output=True, text=True)
                if ':8888' in result.stdout or ':19999' in result.stdout:
                    results.append("✅ 宝塔面板端口监听正常")
                else:
                    results.append("❌ 宝塔面板端口未监听")
            except:
                results.append("❌ 宝塔面板端口检查失败")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 宝塔面板检查失败: {e}"
    
    def check_database_services(self) -> Tuple[bool, str]:
        """检查数据库服务"""
        try:
            results = []
            
            # 检查PostgreSQL
            try:
                result = subprocess.run(['systemctl', 'status', 'postgresql'], 
                                     capture_output=True, text=True)
                if 'active (running)' in result.stdout:
                    results.append("✅ PostgreSQL服务运行正常")
                else:
                    results.append("❌ PostgreSQL服务未运行")
            except:
                results.append("❌ PostgreSQL服务检查失败")
            
            # 检查Redis
            try:
                result = subprocess.run(['systemctl', 'status', 'redis'], 
                                     capture_output=True, text=True)
                if 'active (running)' in result.stdout:
                    results.append("✅ Redis服务运行正常")
                else:
                    results.append("❌ Redis服务未运行")
            except:
                results.append("❌ Redis服务检查失败")
            
            # 测试数据库连接
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host='localhost',
                    database='ai_trading',
                    user='ai_trader',
                    password='your_secure_password_123'
                )
                conn.close()
                results.append("✅ 数据库连接正常")
            except Exception as e:
                results.append(f"❌ 数据库连接失败: {e}")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 数据库服务检查失败: {e}"
    
    def check_web_services(self) -> Tuple[bool, str]:
        """检查Web服务"""
        try:
            results = []
            
            # 检查Nginx
            try:
                result = subprocess.run(['systemctl', 'status', 'nginx'], 
                                     capture_output=True, text=True)
                if 'active (running)' in result.stdout:
                    results.append("✅ Nginx服务运行正常")
                else:
                    results.append("❌ Nginx服务未运行")
            except:
                results.append("❌ Nginx服务检查失败")
            
            # 检查API服务
            try:
                response = requests.get('http://127.0.0.1:8000/health', timeout=5)
                if response.status_code == 200:
                    results.append("✅ API服务运行正常")
                else:
                    results.append(f"❌ API服务异常: {response.status_code}")
            except Exception as e:
                results.append(f"❌ API服务检查失败: {e}")
            
            # 检查端口监听
            try:
                result = subprocess.run(['netstat', '-tlnp'], 
                                     capture_output=True, text=True)
                ports_to_check = [':80', ':443', ':8000']
                for port in ports_to_check:
                    if port in result.stdout:
                        results.append(f"✅ 端口{port}监听正常")
                    else:
                        results.append(f"❌ 端口{port}未监听")
            except:
                results.append("❌ 端口检查失败")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ Web服务检查失败: {e}"
    
    def check_application_status(self) -> Tuple[bool, str]:
        """检查应用状态"""
        try:
            results = []
            
            # 检查项目目录
            project_path = "/www/wwwroot/ai-trading"
            if os.path.exists(project_path):
                results.append("✅ 项目目录存在")
                
                # 检查关键文件
                required_files = [
                    'app/main.py',
                    'requirements.txt',
                    'config/trading_config.py',
                    'frontend/dist/index.html'
                ]
                
                for file_path in required_files:
                    full_path = os.path.join(project_path, file_path)
                    if os.path.exists(full_path):
                        results.append(f"✅ 文件存在: {file_path}")
                    else:
                        results.append(f"❌ 文件缺失: {file_path}")
            else:
                results.append("❌ 项目目录不存在")
            
            # 检查Python环境
            try:
                venv_path = "/opt/ai-trading"
                if os.path.exists(venv_path):
                    results.append("✅ Python虚拟环境存在")
                else:
                    results.append("❌ Python虚拟环境不存在")
            except:
                results.append("❌ Python环境检查失败")
            
            # 检查进程状态
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                processes_to_check = ['uvicorn', 'gunicorn', 'python']
                found_processes = []
                
                for process in processes_to_check:
                    if process in result.stdout:
                        found_processes.append(process)
                
                if found_processes:
                    results.append(f"✅ 应用进程运行中: {', '.join(found_processes)}")
                else:
                    results.append("❌ 应用进程未运行")
            except:
                results.append("❌ 进程检查失败")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 应用状态检查失败: {e}"
    
    def check_security_config(self) -> Tuple[bool, str]:
        """检查安全配置"""
        try:
            results = []
            
            # 检查防火墙
            try:
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
                if 'Status: active' in result.stdout:
                    results.append("✅ 防火墙已启用")
                else:
                    results.append("❌ 防火墙未启用")
            except:
                results.append("❌ 防火墙检查失败")
            
            # 检查SSH配置
            try:
                with open('/etc/ssh/sshd_config', 'r') as f:
                    ssh_config = f.read()
                
                security_checks = [
                    ('PermitRootLogin no', "SSH root登录已禁用"),
                    ('PasswordAuthentication no', "SSH密码认证已禁用"),
                    ('Port 22', "SSH默认端口")
                ]
                
                for check, message in security_checks:
                    if check in ssh_config:
                        results.append(f"✅ {message}")
                    else:
                        results.append(f"⚠️  {message}未配置")
            except:
                results.append("❌ SSH配置检查失败")
            
            # 检查SSL证书（如果配置了HTTPS）
            try:
                result = subprocess.run(['ls', '/www/server/panel/ssl/'], 
                                     capture_output=True, text=True)
                if 'cert.pem' in result.stdout and 'key.pem' in result.stdout:
                    results.append("✅ SSL证书存在")
                else:
                    results.append("⚠️  SSL证书未配置")
            except:
                results.append("❌ SSL证书检查失败")
            
            success = "❌" not in "\n".join(results)
            return success, "\n".join(results)
            
        except Exception as e:
            return False, f"❌ 安全配置检查失败: {e}"
    
    def run_all_checks(self) -> Dict[str, Dict]:
        """运行所有检查"""
        checks = [
            ("系统资源", self.check_system_resources),
            ("网络连接", self.check_network_connectivity),
            ("宝塔面板", self.check_baota_panel),
            ("数据库服务", self.check_database_services),
            ("Web服务", self.check_web_services),
            ("应用状态", self.check_application_status),
            ("安全配置", self.check_security_config)
        ]
        
        results = {}
        for check_name, check_func in checks:
            print(f"🔍 检查 {check_name}...")
            success, message = check_func()
            results[check_name] = {
                'success': success,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        return results
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = ["🚀 AI量化交易系统部署检查报告"]
        report.append("=" * 50)
        report.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result['success'])
        success_rate = (passed_checks / total_checks) * 100
        
        report.append("📊 检查结果汇总:")
        report.append(f"总检查项: {total_checks}")
        report.append(f"通过项: {passed_checks}")
        report.append(f"失败项: {total_checks - passed_checks}")
        report.append(f"成功率: {success_rate:.1f}%")
        report.append("")
        
        # 详细检查结果
        report.append("📋 详细检查结果:")
        for check_name, result in self.results.items():
            status_icon = "✅" if result['success'] else "❌"
            report.append(f"{status_icon} {check_name}")
            
            # 显示详细消息
            for line in result['message'].split('\n'):
                if line.strip():
                    report.append(f"   {line}")
            report.append("")
        
        # 总体评估
        report.append("🎯 总体评估:")
        if success_rate >= 90:
            report.append("🟢 部署状态: 优秀 (≥90%)")
            report.append("系统运行正常，可以投入使用")
        elif success_rate >= 75:
            report.append("🟡 部署状态: 良好 (75-89%)")
            report.append("系统基本正常，建议检查失败项")
        elif success_rate >= 50:
            report.append("🟠 部署状态: 一般 (50-74%)")
            report.append("系统存在问题，需要修复")
        else:
            report.append("🔴 部署状态: 需要改进 (<50%)")
            report.append("系统存在严重问题，需要立即修复")
        
        # 改进建议
        if success_rate < 100:
            report.append("")
            report.append("💡 改进建议:")
            failed_checks = [name for name, result in self.results.items() 
                           if not result['success']]
            
            for check_name in failed_checks:
                report.append(f"- 修复 {check_name} 相关问题")
        
        return "\n".join(report)
    
    def save_report(self, file_path: str = "deployment_check_report.txt") -> None:
        """保存检查报告"""
        report = self.generate_report()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 检查报告已保存: {file_path}")
    
    def main(self):
        """主函数"""
        print("🚀 AI量化交易系统部署检查器")
        print("=" * 50)
        
        # 运行所有检查
        self.results = self.run_all_checks()
        
        # 生成报告
        report = self.generate_report()
        print(report)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"deployment_check_report_{timestamp}.txt"
        self.save_report(report_file)
        
        # 退出码
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result['success'])
        
        if passed_checks == total_checks:
            print("\n🎉 所有检查通过！系统可以正常部署。")
            sys.exit(0)
        else:
            print(f"\n⚠️  有 {total_checks - passed_checks} 个检查失败，请检查相关问题。")
            sys.exit(1)


def main():
    """入口函数"""
    checker = DeploymentChecker()
    checker.main()


if __name__ == "__main__":
    main()