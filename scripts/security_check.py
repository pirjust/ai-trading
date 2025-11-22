#!/usr/bin/env python3
"""
AI量化交易系统安全检查脚本
用于自动化安全检查和漏洞扫描
"""

import sys
import time
import subprocess
import os
import re
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import requests
import socket

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityChecker:
    """安全检查器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.checks = []
        self.results = {}
        
        # 默认配置
        self.default_config = {
            'api_url': 'http://127.0.0.1:8000',
            'domain': 'localhost',
            'timeout': 10,
            'security_level': 'medium',  # low, medium, high
        }
        
        # 合并配置
        self.config = {**self.default_config, **self.config}
        
    def register_check(self, name: str, check_func, category: str, severity: str):
        """注册安全检查"""
        self.checks.append({
            'name': name,
            'func': check_func,
            'category': category,
            'severity': severity  # low, medium, high, critical
        })
    
    def check_firewall_status(self) -> Dict[str, Any]:
        """检查防火墙状态"""
        try:
            # 检查UFW状态
            ufw_result = subprocess.run(
                ['ufw', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 检查iptables
            iptables_result = subprocess.run(
                ['iptables', '-L'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 分析结果
            ufw_enabled = 'Status: active' in ufw_result.stdout
            rules_count = len(re.findall(r'^[A-Z]', iptables_result.stdout, re.MULTILINE))
            
            result = {
                'ufw_enabled': ufw_enabled,
                'iptables_rules': rules_count,
                'status': 'secure' if ufw_enabled and rules_count > 0 else 'insecure',
                'details': {
                    'ufw_output': ufw_result.stdout[:500],  # 限制输出长度
                    'iptables_summary': f"{rules_count} 条规则"
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"防火墙检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_ssh_security(self) -> Dict[str, Any]:
        """检查SSH安全配置"""
        try:
            ssh_config_file = '/etc/ssh/sshd_config'
            
            if not os.path.exists(ssh_config_file):
                return {'status': 'not_found', 'error': 'SSH配置文件不存在'}
            
            with open(ssh_config_file, 'r') as f:
                ssh_config = f.read()
            
            # 检查关键安全设置
            checks = {
                'password_auth_disabled': 'PasswordAuthentication no' in ssh_config,
                'root_login_disabled': 'PermitRootLogin no' in ssh_config,
                'port_changed': not re.search(r'^Port\s+22', ssh_config, re.MULTILINE),
                'max_auth_tries_set': 'MaxAuthTries' in ssh_config,
                'protocol_set': 'Protocol 2' in ssh_config,
            }
            
            secure_count = sum(checks.values())
            total_checks = len(checks)
            
            result = {
                'secure_checks': secure_count,
                'total_checks': total_checks,
                'status': 'secure' if secure_count == total_checks else 'insecure',
                'details': checks
            }
            
            return result
            
        except Exception as e:
            logger.error(f"SSH安全检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_ssl_configuration(self) -> Dict[str, Any]:
        """检查SSL配置"""
        try:
            # 检查SSL证书
            cert_checks = {}
            
            # 检查Nginx SSL配置
            nginx_conf_files = [
                '/etc/nginx/nginx.conf',
                '/etc/nginx/sites-enabled/default',
                '/www/server/panel/vhost/nginx/ai-trading.conf'
            ]
            
            ssl_enabled = False
            for conf_file in nginx_conf_files:
                if os.path.exists(conf_file):
                    with open(conf_file, 'r') as f:
                        content = f.read()
                        if 'ssl_certificate' in content or 'listen 443' in content:
                            ssl_enabled = True
                            break
            
            # 检查HTTPS重定向
            https_redirect = False
            for conf_file in nginx_conf_files:
                if os.path.exists(conf_file):
                    with open(conf_file, 'r') as f:
                        content = f.read()
                        if 'return 301 https://' in content:
                            https_redirect = True
                            break
            
            # 检查HSTS头
            hsts_enabled = False
            for conf_file in nginx_conf_files:
                if os.path.exists(conf_file):
                    with open(conf_file, 'r') as f:
                        content = f.read()
                        if 'Strict-Transport-Security' in content:
                            hsts_enabled = True
                            break
            
            result = {
                'ssl_enabled': ssl_enabled,
                'https_redirect': https_redirect,
                'hsts_enabled': hsts_enabled,
                'status': 'secure' if ssl_enabled and https_redirect and hsts_enabled else 'insecure',
                'details': {
                    'ssl_enabled': ssl_enabled,
                    'https_redirect': https_redirect,
                    'hsts_enabled': hsts_enabled
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"SSL配置检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_api_security(self) -> Dict[str, Any]:
        """检查API安全配置"""
        try:
            # 检查CORS配置
            cors_checks = {}
            
            # 测试API端点
            endpoints = ['/health', '/docs', '/openapi.json']
            
            security_headers = {}
            for endpoint in endpoints:
                try:
                    response = requests.get(
                        f"{self.config['api_url']}{endpoint}",
                        timeout=self.config['timeout']
                    )
                    
                    # 检查安全头
                    headers_to_check = [
                        'X-Frame-Options',
                        'X-Content-Type-Options', 
                        'X-XSS-Protection',
                        'Strict-Transport-Security',
                        'Content-Security-Policy'
                    ]
                    
                    for header in headers_to_check:
                        if header in response.headers:
                            security_headers[header] = True
                        else:
                            security_headers[header] = False
                    
                except requests.exceptions.RequestException:
                    continue
            
            # 统计安全头数量
            secure_headers = sum(security_headers.values())
            total_headers = len(security_headers)
            
            result = {
                'secure_headers': secure_headers,
                'total_headers': total_headers,
                'status': 'secure' if secure_headers == total_headers else 'insecure',
                'details': security_headers
            }
            
            return result
            
        except Exception as e:
            logger.error(f"API安全检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_database_security(self) -> Dict[str, Any]:
        """检查数据库安全配置"""
        try:
            # 检查PostgreSQL配置
            pg_conf_file = '/etc/postgresql/15/main/postgresql.conf'
            pg_hba_file = '/etc/postgresql/15/main/pg_hba.conf'
            
            pg_checks = {}
            
            if os.path.exists(pg_conf_file):
                with open(pg_conf_file, 'r') as f:
                    pg_conf = f.read()
                    
                pg_checks['ssl_enabled'] = 'ssl = on' in pg_conf
                pg_checks['log_connections'] = 'log_connections = on' in pg_conf
                pg_checks['log_disconnections'] = 'log_disconnections = on' in pg_conf
            
            if os.path.exists(pg_hba_file):
                with open(pg_hba_file, 'r') as f:
                    pg_hba = f.read()
                    
                # 检查是否允许远程连接
                pg_checks['remote_access_restricted'] = not re.search(r'^host\s+all\s+all\s+0\.0\.0\.0/0', pg_hba, re.MULTILINE)
            
            # 检查Redis配置
            redis_conf_file = '/etc/redis/redis.conf'
            redis_checks = {}
            
            if os.path.exists(redis_conf_file):
                with open(redis_conf_file, 'r') as f:
                    redis_conf = f.read()
                    
                redis_checks['password_protected'] = 'requirepass' in redis_conf
                redis_checks['bind_restricted'] = 'bind 127.0.0.1' in redis_conf or 'bind ::1' in redis_conf
                redis_checks['protected_mode'] = 'protected-mode yes' in redis_conf
            
            # 合并检查结果
            all_checks = {**pg_checks, **redis_checks}
            secure_count = sum(all_checks.values())
            total_checks = len(all_checks)
            
            result = {
                'secure_checks': secure_count,
                'total_checks': total_checks,
                'status': 'secure' if secure_count == total_checks else 'insecure',
                'details': {
                    'postgresql': pg_checks,
                    'redis': redis_checks
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"数据库安全检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """检查文件权限"""
        try:
            # 检查关键文件权限
            critical_files = [
                '/etc/passwd',
                '/etc/shadow', 
                '/etc/group',
                '/etc/sudoers',
                '/var/log/auth.log',
                '/www/wwwroot/ai-trading/config',
                '/www/wwwroot/ai-trading/.env'
            ]
            
            permission_checks = {}
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    try:
                        stat_info = os.stat(file_path)
                        
                        # 检查权限
                        mode = stat_info.st_mode
                        
                        # 检查是否过于宽松
                        world_writable = bool(mode & 0o002)  # 其他用户可写
                        group_writable = bool(mode & 0o020)  # 组用户可写
                        
                        # 对于敏感文件，应该严格限制权限
                        if file_path in ['/etc/shadow', '/etc/sudoers']:
                            secure = not (world_writable or group_writable) and mode & 0o400  # 只读
                        else:
                            secure = not world_writable
                        
                        permission_checks[file_path] = {
                            'secure': secure,
                            'permissions': oct(mode)[-3:],
                            'owner': stat_info.st_uid,
                            'group': stat_info.st_gid
                        }
                        
                    except Exception as e:
                        permission_checks[file_path] = {'error': str(e)}
                else:
                    permission_checks[file_path] = {'exists': False}
            
            secure_count = sum(1 for check in permission_checks.values() 
                            if isinstance(check, dict) and check.get('secure') == True)
            total_checks = len(permission_checks)
            
            result = {
                'secure_files': secure_count,
                'total_files': total_checks,
                'status': 'secure' if secure_count == total_checks else 'insecure',
                'details': permission_checks
            }
            
            return result
            
        except Exception as e:
            logger.error(f"文件权限检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_open_ports(self) -> Dict[str, Any]:
        """检查开放端口"""
        try:
            # 使用netstat检查开放端口
            netstat_result = subprocess.run(
                ['netstat', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析开放端口
            open_ports = []
            for line in netstat_result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        address = parts[3]
                        # 提取端口号
                        port_match = re.search(r':(\d+)$', address)
                        if port_match:
                            port = int(port_match.group(1))
                            open_ports.append(port)
            
            # 定义危险端口
            dangerous_ports = [21, 23, 135, 139, 445, 1433, 1521, 3306, 5432, 6379]  # 常见服务端口
            
            # 检查是否有不必要的端口开放
            unnecessary_ports = []
            for port in open_ports:
                if port in dangerous_ports and port not in [5432, 6379]:  # 允许数据库端口
                    unnecessary_ports.append(port)
            
            result = {
                'open_ports': open_ports,
                'unnecessary_ports': unnecessary_ports,
                'status': 'secure' if len(unnecessary_ports) == 0 else 'insecure',
                'details': {
                    'total_open_ports': len(open_ports),
                    'unnecessary_count': len(unnecessary_ports)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"开放端口检查失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有安全检查"""
        logger.info("开始运行安全检查...")
        
        start_time = time.time()
        
        # 注册检查
        self.register_check('firewall_status', self.check_firewall_status, 'network', 'high')
        self.register_check('ssh_security', self.check_ssh_security, 'access', 'critical')
        self.register_check('ssl_configuration', self.check_ssl_configuration, 'web', 'high')
        self.register_check('api_security', self.check_api_security, 'application', 'medium')
        self.register_check('database_security', self.check_database_security, 'database', 'high')
        self.register_check('file_permissions', self.check_file_permissions, 'system', 'medium')
        self.register_check('open_ports', self.check_open_ports, 'network', 'high')
        
        # 运行检查
        results = {}
        critical_issues = 0
        high_issues = 0
        
        for check in self.checks:
            try:
                check_start = time.time()
                result = check['func']()
                check_time = time.time() - check_start
                
                result['duration'] = check_time
                result['severity'] = check['severity']
                result['category'] = check['category']
                
                results[check['name']] = result
                
                # 统计问题
                if result.get('status') == 'insecure':
                    if check['severity'] == 'critical':
                        critical_issues += 1
                    elif check['severity'] == 'high':
                        high_issues += 1
                    
                logger.info(f"检查 {check['name']}: {result.get('status', 'unknown')} ({check_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"执行检查 {check['name']} 失败: {e}")
                results[check['name']] = {
                    'status': 'error', 
                    'error': str(e),
                    'severity': check['severity'],
                    'category': check['category']
                }
        
        total_time = time.time() - start_time
        
        # 汇总结果
        overall_status = 'secure'
        if critical_issues > 0:
            overall_status = 'critical'
        elif high_issues > 0:
            overall_status = 'high_risk'
        elif any(result.get('status') == 'insecure' for result in results.values()):
            overall_status = 'medium_risk'
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'total_checks': len(self.checks),
            'critical_issues': critical_issues,
            'high_issues': high_issues,
            'total_time': total_time,
            'results': results
        }
        
        logger.info(f"安全检查完成: {overall_status} (耗时: {total_time:.2f}s)")
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any]) -> str:
        """生成安全检查报告"""
        report = []
        
        report.append("=" * 70)
        report.append("AI量化交易系统安全检查报告")
        report.append("=" * 70)
        report.append(f"检查时间: {summary['timestamp']}")
        report.append(f"总体状态: {summary['overall_status'].upper()}")
        report.append(f"检查数量: {summary['total_checks']}")
        report.append(f"关键问题: {summary['critical_issues']}")
        report.append(f"高风险问题: {summary['high_issues']}")
        report.append(f"总耗时: {summary['total_time']:.2f}秒")
        report.append("")
        
        # 按严重程度分组
        issues_by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        
        for check_name, result in summary['results'].items():
            if result.get('status') == 'insecure':
                severity = result.get('severity', 'medium')
                issues_by_severity[severity].append({
                    'name': check_name,
                    'result': result
                })
        
        # 显示问题
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = issues_by_severity[severity]
            if issues:
                report.append(f"{severity.upper()} 严重程度问题:")
                for issue in issues:
                    status_icon = "🔴" if severity == 'critical' else "🟠" if severity == 'high' else "🟡"
                    report.append(f"  {status_icon} {issue['name']}")
                    
                    # 显示详细信息
                    details = issue['result'].get('details', {})
                    if details:
                        for key, value in details.items():
                            if isinstance(value, dict):
                                report.append(f"      {key}:")
                                for k, v in value.items():
                                    report.append(f"        {k}: {v}")
                            else:
                                report.append(f"      {key}: {value}")
                report.append("")
        
        # 安全建议
        report.append("安全建议:")
        
        if summary['critical_issues'] > 0:
            report.append("🚨 紧急修复:")
            report.append("1. 立即修复所有关键安全问题")
            report.append("2. 加强访问控制和身份验证")
            report.append("3. 考虑暂停服务进行安全加固")
        
        if summary['high_issues'] > 0:
            report.append("⚠️ 高风险修复:")
            report.append("1. 尽快修复高风险安全问题")
            report.append("2. 加强网络和系统安全配置")
            report.append("3. 定期进行安全审计")
        
        if summary['overall_status'] == 'secure':
            report.append("✅ 系统安全状态良好")
            report.append("建议继续保持并定期检查")
        
        report.append("")
        report.append("改进措施:")
        report.append("1. 定期更新系统和软件")
        report.append("2. 实施最小权限原则")
        report.append("3. 启用安全监控和日志记录")
        report.append("4. 定期进行渗透测试")
        
        return "\n".join(report)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI量化交易系统安全检查')
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
    checker = SecurityChecker(config)
    
    # 运行检查
    summary = checker.run_all_checks()
    
    # 生成报告
    report = checker.generate_report(summary)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        logger.info(f"报告已保存到: {args.output}")
    
    if args.verbose or summary['overall_status'] != 'secure':
        print(report)
    
    # 返回退出码
    if summary['overall_status'] == 'critical':
        sys.exit(2)
    elif summary['overall_status'] in ['high_risk', 'medium_risk']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()