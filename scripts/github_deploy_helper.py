#!/usr/bin/env python3
# GitHub部署助手脚本
# 用于辅助GitHub Actions部署到腾讯云宝塔面板

import os
import sys
import json
import yaml
import requests
import time
from datetime import datetime
from pathlib import Path

class GitHubDeployHelper:
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_file = self.project_root / "config" / "deployment_config.yaml"
        self.deploy_log = self.project_root / "logs" / "deployment.log"
        
        # 加载配置
        self.config = self.load_config()
        
        # GitHub环境变量
        self.github_env = {
            'repository': os.getenv('GITHUB_REPOSITORY', ''),
            'ref': os.getenv('GITHUB_REF', ''),
            'sha': os.getenv('GITHUB_SHA', ''),
            'workflow': os.getenv('GITHUB_WORKFLOW', ''),
            'run_id': os.getenv('GITHUB_RUN_ID', '')
        }
        
    def load_config(self):
        """加载部署配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
        
    def log_deployment(self, message, level="INFO"):
        """记录部署日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 确保日志目录存在
        self.deploy_log.parent.mkdir(exist_ok=True)
        
        with open(self.deploy_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
        print(f"[{level}] {message}")
        
    def validate_environment(self):
        """验证部署环境"""
        self.log_deployment("开始验证部署环境...")
        
        # 检查必要的环境变量
        required_env_vars = [
            'TENCENT_CLOUD_HOST',
            'TENCENT_CLOUD_SSH_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.log_deployment(f"缺少必要的环境变量: {', '.join(missing_vars)}", "ERROR")
            return False
            
        self.log_deployment("环境变量验证通过")
        
        # 检查配置文件
        if not self.config:
            self.log_deployment("部署配置文件不存在或格式错误", "WARNING")
            
        return True
        
    def generate_deployment_package(self):
        """生成部署包"""
        self.log_deployment("开始生成部署包...")
        
        package_dir = self.project_root / "deploy-package"
        
        # 清理旧的部署包
        if package_dir.exists():
            import shutil
            shutil.rmtree(package_dir)
            
        package_dir.mkdir(exist_ok=True)
        
        # 需要包含的文件和目录
        include_patterns = [
            "app/**/*",
            "config/**/*", 
            "core/**/*",
            "data/**/*",
            "ai_engine/**/*",
            "strategies/**/*",
            "scripts/**/*",
            "requirements.txt",
            "pyproject.toml",
            "Dockerfile",
            "docker-compose.yml",
            "README.md"
        ]
        
        # 复制文件
        for pattern in include_patterns:
            pattern_path = Path(pattern)
            if pattern_path.exists():
                if pattern_path.is_dir():
                    # 复制目录
                    dst_dir = package_dir / pattern_path.relative_to(self.project_root)
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    
                    import shutil
                    shutil.copytree(pattern_path, dst_dir, dirs_exist_ok=True)
                else:
                    # 复制文件
                    dst_file = package_dir / pattern_path.name
                    shutil.copy2(pattern_path, dst_file)
                    
        # 创建部署脚本
        self.create_deployment_scripts(package_dir)
        
        # 创建环境配置文件
        self.create_environment_config(package_dir)
        
        self.log_deployment("部署包生成完成")
        return package_dir
        
    def create_deployment_scripts(self, package_dir):
        """创建部署脚本"""
        # 创建主部署脚本
        deploy_script = """#!/bin/bash
# AI量化交易系统部署脚本

set -e

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    exit 1
}

# 部署信息
DEPLOY_INFO=""" + f"""
部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
代码版本: {self.github_env.get('sha', 'unknown')}
部署分支: {self.github_env.get('ref', 'unknown')}
""" + """

# 主部署函数
deploy() {
    log "开始部署AI量化交易系统..."
    echo "$DEPLOY_INFO"
    
    # 检查环境
    check_environment
    
    # 备份现有应用
    backup_current
    
    # 安装依赖
    install_dependencies
    
    # 配置数据库
    setup_database
    
    # 启动服务
    start_services
    
    # 健康检查
    health_check
    
    log "🎉 AI量化交易系统部署完成！"
}

# 环境检查
check_environment() {
    log "检查部署环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error "Python3未安装"
    fi
    
    # 检查虚拟环境
    if [ ! -d "/opt/ai-trading" ]; then
        warn "虚拟环境不存在，将自动创建"
        python3 -m venv /opt/ai-trading
    fi
    
    log "环境检查完成"
}

# 备份现有应用
backup_current() {
    DEPLOY_PATH="/www/wwwroot/ai-trading"
    
    if [ -d "$DEPLOY_PATH" ]; then
        log "备份现有应用..."
        backup_dir="/backup/ai-trading/$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$backup_dir"
        cp -r "$DEPLOY_PATH" "$backup_dir/"
        log "应用已备份到: $backup_dir"
    fi
}

# 安装依赖
install_dependencies() {
    log "安装Python依赖..."
    
    source /opt/ai-trading/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "依赖安装完成"
}

# 配置数据库
setup_database() {
    log "配置数据库..."
    
    if [ -f "scripts/init_database.sql" ]; then
        psql -h localhost -U ai_trader -d ai_trading -f scripts/init_database.sql
    fi
    
    if [ -f "scripts/database_migration.py" ]; then
        source /opt/ai-trading/bin/activate
        python scripts/database_migration.py migrate
    fi
    
    log "数据库配置完成"
}

# 启动服务
start_services() {
    log "启动服务..."
    
    # 停止现有服务
    pkill -f "uvicorn" || true
    pkill -f "trading_monitor" || true
    sleep 2
    
    # 启动新服务
    source /opt/ai-trading/bin/activate
    
    # API服务
    nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > logs/api.log 2>&1 &
    
    # 监控服务
    nohup python -m monitoring.trading_monitor > logs/monitor.log 2>&1 &
    
    sleep 5
    
    # 检查服务状态
    if pgrep -f "uvicorn" > /dev/null; then
        log "API服务启动成功"
    else
        error "API服务启动失败"
    fi
    
    log "服务启动完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://127.0.0.1:8000/health > /dev/null 2>&1; then
            log "健康检查通过"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "健康检查失败"
        fi
        
        warn "健康检查失败，第${attempt}次重试..."
        sleep 5
        ((attempt++))
    done
}

# 主程序
main() {
    case "${1:-deploy}" in
        deploy)
            deploy
            ;;
        rollback)
            rollback "$2"
            ;;
        status)
            check_status
            ;;
        *)
            echo "用法: $0 {deploy|rollback|status}"
            exit 1
            ;;
    esac
}

# 执行部署
main "$@"
"""
        
        with open(package_dir / "deploy.sh", 'w') as f:
            f.write(deploy_script)
            
        # 设置可执行权限
        import stat
        os.chmod(package_dir / "deploy.sh", stat.S_IRWXU)
        
    def create_environment_config(self, package_dir):
        """创建环境配置文件"""
        env_config = {
            "deployment": {
                "timestamp": datetime.now().isoformat(),
                "version": self.github_env.get('sha', 'unknown'),
                "branch": self.github_env.get('ref', 'unknown'),
                "repository": self.github_env.get('repository', 'unknown')
            },
            "application": {
                "name": "ai-trading",
                "version": "1.0.0",
                "environment": "production"
            }
        }
        
        with open(package_dir / "deployment-info.json", 'w') as f:
            json.dump(env_config, f, indent=2)
            
    def create_deployment_report(self, success=True, message=""):
        """创建部署报告"""
        report = {
            "deployment_id": self.github_env.get('run_id', 'manual'),
            "timestamp": datetime.now().isoformat(),
            "status": "success" if success else "failed",
            "message": message,
            "environment": {
                "repository": self.github_env.get('repository'),
                "branch": self.github_env.get('ref'),
                "commit": self.github_env.get('sha'),
                "workflow": self.github_env.get('workflow')
            },
            "system_info": {
                "python_version": sys.version,
                "working_directory": str(self.project_root)
            }
        }
        
        report_file = self.project_root / "deployment-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log_deployment(f"部署报告已生成: {report_file}")
        
    def send_notification(self, success=True, message=""):
        """发送部署通知"""
        if not os.getenv('SLACK_WEBHOOK'):
            self.log_deployment("未配置Slack通知，跳过", "INFO")
            return
            
        status = "✅ 成功" if success else "❌ 失败"
        
        payload = {
            "text": f"AI量化交易系统部署 {status}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI量化交易系统部署 {status}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn", 
                            "text": f"*仓库:* {self.github_env.get('repository')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*分支:* {self.github_env.get('ref')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*提交:* {self.github_env.get('sha')[:8]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*时间:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*消息:* {message}"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                os.getenv('SLACK_WEBHOOK'),
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                self.log_deployment("Slack通知发送成功")
            else:
                self.log_deployment(f"Slack通知发送失败: {response.status_code}", "WARNING")
        except Exception as e:
            self.log_deployment(f"Slack通知发送异常: {e}", "WARNING")
            
    def run_pre_deployment_checks(self):
        """运行预部署检查"""
        self.log_deployment("运行预部署检查...")
        
        checks = [
            ("检查Python版本", self.check_python_version),
            ("检查依赖文件", self.check_requirements),
            ("检查配置文件", self.check_config_files),
            ("检查测试", self.run_tests)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    self.log_deployment(f"{check_name}: 通过")
                else:
                    self.log_deployment(f"{check_name}: 失败", "WARNING")
                    all_passed = False
            except Exception as e:
                self.log_deployment(f"{check_name}: 异常 - {e}", "ERROR")
                all_passed = False
                
        return all_passed
        
    def check_python_version(self):
        """检查Python版本"""
        import sys
        version_info = sys.version_info
        
        # 要求Python 3.8+
        if version_info.major == 3 and version_info.minor >= 8:
            return True
        return False
        
    def check_requirements(self):
        """检查依赖文件"""
        requirements_file = self.project_root / "requirements.txt"
        return requirements_file.exists()
        
    def check_config_files(self):
        """检查配置文件"""
        config_files = [
            "config/deployment_config.yaml",
            "config/app_config.py",
            "pyproject.toml"
        ]
        
        for config_file in config_files:
            if not (self.project_root / config_file).exists():
                self.log_deployment(f"配置文件不存在: {config_file}", "WARNING")
                return False
                
        return True
        
    def run_tests(self):
        """运行测试"""
        # 如果有测试目录，运行测试
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            import subprocess
            
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "tests/", "-v"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode == 0:
                    self.log_deployment("测试通过")
                    return True
                else:
                    self.log_deployment(f"测试失败: {result.stderr}", "WARNING")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log_deployment("测试超时", "WARNING")
                return False
            except Exception as e:
                self.log_deployment(f"测试异常: {e}", "WARNING")
                return False
        
        self.log_deployment("未找到测试目录，跳过测试")
        return True
        
    def main(self):
        """主函数"""
        try:
            self.log_deployment("GitHub部署助手启动")
            
            # 验证环境
            if not self.validate_environment():
                self.create_deployment_report(False, "环境验证失败")
                self.send_notification(False, "环境验证失败")
                return 1
                
            # 预部署检查
            if not self.run_pre_deployment_checks():
                self.create_deployment_report(False, "预部署检查失败")
                self.send_notification(False, "预部署检查失败")
                return 1
                
            # 生成部署包
            package_dir = self.generate_deployment_package()
            
            # 创建部署报告
            self.create_deployment_report(True, "部署包生成完成")
            
            self.log_deployment("GitHub部署助手执行完成")
            self.send_notification(True, "部署包准备就绪")
            
            return 0
            
        except Exception as e:
            self.log_deployment(f"部署助手执行失败: {e}", "ERROR")
            self.create_deployment_report(False, f"执行失败: {e}")
            self.send_notification(False, f"执行失败: {e}")
            return 1

if __name__ == "__main__":
    helper = GitHubDeployHelper()
    sys.exit(helper.main())