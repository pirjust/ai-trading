#!/usr/bin/env python3
"""
AI量化交易系统部署检查清单
用于验证部署环境的完整性和正确性
"""

import os
import sys
import subprocess
import requests
import psycopg2
import redis
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment_check.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DeploymentChecklist:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
        
        # 配置信息
        self.config = {
            'api_url': 'http://127.0.0.1:8000',
            'db_host': os.getenv('DB_HOST', 'localhost'),
            'db_port': int(os.getenv('DB_PORT', '5432')),
            'db_name': os.getenv('DB_NAME', 'ai_trading'),
            'db_user': os.getenv('DB_USER', 'ai_trader'),
            'db_password': os.getenv('DB_PASSWORD', 'your_secure_password_123'),
            'redis_host': os.getenv('REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('REDIS_PORT', '6379')),
            'redis_password': os.getenv('REDIS_PASSWORD', 'your_redis_password_123'),
            'nginx_port': 80
        }
    
    def record_result(self, check_name, passed, details=''):
        """记录检查结果"""
        status = '✅ 通过' if passed else '❌ 失败'
        result = {
            'check': check_name,
            'status': status,
            'details': details,
            'passed': passed
        }
        
        self.results.append(result)
        
        if passed:
            self.checks_passed += 1
            logger.info(f"{status} - {check_name}")
        else:
            self.checks_failed += 1
            logger.error(f"{status} - {check_name}: {details}")
    
    def check_system_resources(self):
        """检查系统资源"""
        try:
            # 检查磁盘空间
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            disk_usage = result.stdout
            
            # 检查内存使用
            result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            memory_usage = result.stdout
            
            # 检查CPU使用
            result = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
            cpu_usage = result.stdout
            
            self.record_result('系统资源检查', True, 
                              f"磁盘: {disk_usage.split('\n')[1]}\n内存: {memory_usage.split('\n')[1]}")
        except Exception as e:
            self.record_result('系统资源检查', False, str(e))
    
    def check_service_status(self, service_name):
        """检查服务状态"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.record_result(f"{service_name} 服务状态", True, '服务运行正常')
            else:
                self.record_result(f"{service_name} 服务状态", False, '服务未运行')
                
        except Exception as e:
            self.record_result(f"{service_name} 服务状态", False, str(e))
    
    def check_database_connection(self):
        """检查数据库连接"""
        try:
            conn = psycopg2.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                database=self.config['db_name'],
                user=self.config['db_user'],
                password=self.config['db_password']
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                
                # 检查关键表是否存在
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name IN ('users', 'strategies', 'trades', 'klines')
                """)
                tables = [row[0] for row in cur.fetchall()]
                
            conn.close()
            
            details = f"PostgreSQL版本: {version.split(',')[0]}\n关键表: {', '.join(tables)}"
            self.record_result('数据库连接', True, details)
            
        except Exception as e:
            self.record_result('数据库连接', False, str(e))
    
    def check_redis_connection(self):
        """检查Redis连接"""
        try:
            r = redis.Redis(
                host=self.config['redis_host'],
                port=self.config['redis_port'],
                password=self.config['redis_password'],
                decode_responses=True
            )
            
            # 测试连接
            r.ping()
            
            # 获取Redis信息
            info = r.info()
            version = info.get('redis_version', '未知')
            
            self.record_result('Redis连接', True, f"Redis版本: {version}")
            
        except Exception as e:
            self.record_result('Redis连接', False, str(e))
    
    def check_api_health(self):
        """检查API健康状态"""
        try:
            response = requests.get(f"{self.config['api_url']}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                details = f"API状态: {status}"
                self.record_result('API健康检查', True, details)
            else:
                self.record_result('API健康检查', False, 
                                  f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.record_result('API健康检查', False, str(e))
    
    def check_nginx_config(self):
        """检查Nginx配置"""
        try:
            # 检查Nginx配置语法
            result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.record_result('Nginx配置检查', True, '配置语法正确')
            else:
                self.record_result('Nginx配置检查', False, result.stderr)
                
        except Exception as e:
            self.record_result('Nginx配置检查', False, str(e))
    
    def check_application_logs(self):
        """检查应用日志"""
        try:
            log_files = [
                '/www/wwwroot/ai-trading/logs/api.log',
                '/www/wwwroot/ai-trading/logs/api-error.log',
                '/www/wwwroot/ai-trading/logs/monitor.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    # 检查文件大小和最近修改时间
                    stat = os.stat(log_file)
                    size_mb = stat.st_size / (1024 * 1024)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    if size_mb < 100:  # 小于100MB
                        self.record_result(f"日志文件检查: {os.path.basename(log_file)}", 
                                          True, f"大小: {size_mb:.2f}MB, 修改时间: {modified_time}")
                    else:
                        self.record_result(f"日志文件检查: {os.path.basename(log_file)}", 
                                          False, f"文件过大: {size_mb:.2f}MB")
                else:
                    self.record_result(f"日志文件检查: {os.path.basename(log_file)}", 
                                      False, '文件不存在')
                    
        except Exception as e:
            self.record_result('应用日志检查', False, str(e))
    
    def check_file_permissions(self):
        """检查文件权限"""
        try:
            paths_to_check = [
                '/www/wwwroot/ai-trading',
                '/www/wwwroot/ai-trading/logs',
                '/www/wwwroot/ai-trading/config'
            ]
            
            for path in paths_to_check:
                if os.path.exists(path):
                    stat = os.stat(path)
                    
                    # 检查目录权限
                    if stat.st_mode & 0o755 == 0o755:
                        self.record_result(f"文件权限检查: {path}", True, 
                                          f"权限: {oct(stat.st_mode)[-3:]}")
                    else:
                        self.record_result(f"文件权限检查: {path}", False, 
                                          f"权限不足: {oct(stat.st_mode)[-3:]}")
                else:
                    self.record_result(f"文件权限检查: {path}", False, '路径不存在')
                    
        except Exception as e:
            self.record_result('文件权限检查', False, str(e))
    
    def check_dependencies(self):
        """检查Python依赖"""
        try:
            # 检查关键Python包
            packages = ['fastapi', 'uvicorn', 'psycopg2', 'redis', 'ccxt', 'pandas']
            
            for package in packages:
                result = subprocess.run(
                    ['python3', '-c', f'import {package}; print({package}.__version__)'],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.record_result(f"Python包检查: {package}", True, f"版本: {version}")
                else:
                    self.record_result(f"Python包检查: {package}", False, '未安装或导入失败')
                    
        except Exception as e:
            self.record_result('Python依赖检查', False, str(e))
    
    def check_network_connectivity(self):
        """检查网络连通性"""
        try:
            # 检查本地端口
            ports_to_check = [80, 8000, 5432, 6379]
            
            for port in ports_to_check:
                result = subprocess.run(
                    ['netstat', '-tlnp'],
                    capture_output=True, text=True
                )
                
                if f":{port} " in result.stdout:
                    self.record_result(f"端口检查: {port}", True, '端口监听正常')
                else:
                    self.record_result(f"端口检查: {port}", False, '端口未监听')
                    
            # 检查外部网络连接（可选）
            try:
                response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
                if response.status_code == 200:
                    self.record_result('外部网络连接', True, '可以访问外部API')
                else:
                    self.record_result('外部网络连接', False, '无法访问外部API')
            except:
                self.record_result('外部网络连接', False, '网络连接超时')
                
        except Exception as e:
            self.record_result('网络连通性检查', False, str(e))
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*60)
        print("AI量化交易系统部署检查报告")
        print("="*60)
        
        for result in self.results:
            print(f"{result['status']} {result['check']}")
            if result['details']:
                print(f"   详情: {result['details']}")
        
        print("\n" + "="*60)
        print(f"检查结果: {self.checks_passed} 项通过, {self.checks_failed} 项失败")
        print("="*60)
        
        # 保存详细报告
        with open('logs/deployment_report.txt', 'w') as f:
            f.write("AI量化交易系统部署检查报告\n")
            f.write("="*60 + "\n")
            f.write(f"检查时间: {datetime.now()}\n")
            f.write(f"检查结果: {self.checks_passed} 项通过, {self.checks_failed} 项失败\n\n")
            
            for result in self.results:
                f.write(f"{result['status']} {result['check']}\n")
                if result['details']:
                    f.write(f"   详情: {result['details']}\n")
                f.write("\n")
        
        if self.checks_failed == 0:
            print("🎉 所有检查项通过！系统部署成功！")
            return True
        else:
            print("⚠️  发现一些问题，请检查失败的检查项")
            return False
    
    def run_all_checks(self):
        """运行所有检查"""
        logger.info("开始部署检查...")
        
        # 系统资源检查
        self.check_system_resources()
        
        # 服务状态检查
        services = ['nginx', 'postgresql', 'redis', 'supervisor']
        for service in services:
            self.check_service_status(service)
        
        # 数据库检查
        self.check_database_connection()
        self.check_redis_connection()
        
        # 应用检查
        self.check_api_health()
        self.check_nginx_config()
        self.check_application_logs()
        self.check_file_permissions()
        self.check_dependencies()
        self.check_network_connectivity()
        
        # 生成报告
        return self.generate_report()

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        # 快速检查模式
        checklist = DeploymentChecklist()
        
        # 只运行关键检查
        checklist.check_api_health()
        checklist.check_database_connection()
        checklist.check_redis_connection()
        
        checklist.generate_report()
    else:
        # 完整检查模式
        checklist = DeploymentChecklist()
        success = checklist.run_all_checks()
        
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()