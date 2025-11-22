#!/usr/bin/env python3
# 宝塔面板自动化配置脚本
# 用于在腾讯云Ubuntu系统上自动配置宝塔面板和AI量化交易系统

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

class BaotaPanelSetup:
    def __init__(self):
        self.base_dir = Path("/www/wwwroot/ai-trading")
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = Path("/etc/ai-trading")
        
        # 宝塔面板配置
        self.baota_panel_url = "http://localhost:8888"
        self.baota_api_key = os.getenv("BAOTA_API_KEY", "")
        
        # 应用配置
        self.app_config = {
            "name": "ai-trading",
            "path": str(self.base_dir),
            "python_version": "3.9",
            "port": 8000,
            "workers": 4
        }
        
    def run_command(self, cmd, check=True, capture_output=True):
        """运行系统命令"""
        print(f"执行命令: {cmd}")
        
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=check,
                capture_output=capture_output,
                text=True
            )
            if capture_output and result.stdout:
                print(f"输出: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            if e.stdout:
                print(f"错误输出: {e.stdout}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            if check:
                raise
            return None
    
    def install_baota_panel(self):
        """安装宝塔面板"""
        print("正在安装宝塔面板...")
        
        # 下载宝塔面板安装脚本
        install_script = """
        wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh
        bash install.sh
        """
        
        self.run_command(install_script, check=False)
        
        # 等待安装完成
        time.sleep(60)
        
        print("宝塔面板安装完成")
        
    def configure_firewall(self):
        """配置防火墙"""
        print("配置防火墙...")
        
        firewall_rules = """
        # 安装ufw
        apt-get update
        apt-get install -y ufw
        
        # 配置防火墙规则
        ufw allow 22/tcp    # SSH
        ufw allow 80/tcp    # HTTP
        ufw allow 443/tcp   # HTTPS
        ufw allow 8888/tcp  # 宝塔面板
        ufw allow 8000/tcp # 应用端口
        
        # 启用防火墙
        ufw --force enable
        """
        
        self.run_command(firewall_rules)
        print("防火墙配置完成")
        
    def install_system_dependencies(self):
        """安装系统依赖"""
        print("安装系统依赖...")
        
        dependencies = """
        # 更新系统
        apt-get update
        apt-get upgrade -y
        
        # 安装基础依赖
        apt-get install -y \\
            curl wget git vim \\
            build-essential \\
            python3 python3-pip python3-venv \\
            nginx \\
            postgresql postgresql-contrib \\
            redis-server \\
            supervisor
        
        # 安装Python开发工具
        pip3 install --upgrade pip
        pip3 install virtualenv
        """
        
        self.run_command(dependencies)
        print("系统依赖安装完成")
        
    def setup_python_environment(self):
        """设置Python虚拟环境"""
        print("设置Python虚拟环境...")
        
        # 创建虚拟环境
        venv_cmds = f"""
        # 创建虚拟环境
        python3 -m venv /opt/ai-trading
        
        # 激活虚拟环境安装依赖
        source /opt/ai-trading/bin/activate && \\
        pip install --upgrade pip && \\
        pip install -r {self.base_dir}/requirements.txt
        """
        
        self.run_command(venv_cmds)
        print("Python虚拟环境设置完成")
        
    def configure_database(self):
        """配置数据库"""
        print("配置数据库...")
        
        db_commands = """
        # 切换到postgres用户
        sudo -u postgres psql << EOF
        -- 创建数据库用户
        CREATE USER ai_trader WITH PASSWORD 'ai_trading_password_123';
        
        -- 创建数据库
        CREATE DATABASE ai_trading OWNER ai_trader;
        
        -- 授予权限
        GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
        
        -- 创建测试数据库
        CREATE DATABASE ai_trading_test OWNER ai_trader;
        GRANT ALL PRIVILEGES ON DATABASE ai_trading_test TO ai_trader;
        
        -- 退出
        \\q
        EOF
        
        # 配置PostgreSQL
        echo "host ai_trading ai_trader 127.0.0.1/32 md5" >> /etc/postgresql/*/main/pg_hba.conf
        
        # 重启PostgreSQL
        systemctl restart postgresql
        """
        
        self.run_command(db_commands)
        print("数据库配置完成")
        
    def configure_redis(self):
        """配置Redis"""
        print("配置Redis...")
        
        redis_config = """
        # 备份原始配置
        cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
        
        # 修改Redis配置
        sed -i 's/^# requirepass.*/requirepass ai_redis_password_123/' /etc/redis/redis.conf
        sed -i 's/^bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
        sed -i 's/^# maxmemory .*/maxmemory 2gb/' /etc/redis/redis.conf
        sed -i 's/^# maxmemory-policy.*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
        
        # 重启Redis
        systemctl restart redis-server
        """
        
        self.run_command(redis_config)
        print("Redis配置完成")
        
    def setup_application_directory(self):
        """设置应用目录"""
        print("设置应用目录...")
        
        # 创建必要的目录
        dirs_to_create = [
            self.base_dir,
            self.logs_dir,
            self.config_dir,
            Path("/var/log/ai-trading"),
            Path("/backup/ai-trading")
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
            
        # 设置权限
        chown_cmd = f"chown -R www:www {self.base_dir}"
        self.run_command(chown_cmd)
        
        print("应用目录设置完成")
        
    def create_nginx_config(self):
        """创建Nginx配置"""
        print("创建Nginx配置...")
        
        nginx_config = f"""
        server {{
            listen 80;
            server_name _;
            
            # 前端静态文件
            location / {{
                root {self.base_dir}/frontend/dist;
                index index.html;
                try_files $uri $uri/ /index.html;
            }}
            
            # API代理
            location /api/ {{
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                
                # 超时设置
                proxy_connect_timeout 60s;
                proxy_send_timeout 60s;
                proxy_read_timeout 60s;
            }}
            
            # 静态资源缓存
            location ~* \\\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
                expires 1y;
                add_header Cache-Control "public, immutable";
                root {self.base_dir}/frontend/dist;
            }}
            
            # 健康检查
            location /health {{
                proxy_pass http://127.0.0.1:8000/health;
                access_log off;
            }}
        }}
        """
        
        # 写入Nginx配置
        nginx_conf_path = "/etc/nginx/sites-available/ai-trading"
        with open(nginx_conf_path, 'w') as f:
            f.write(nginx_config)
            
        # 启用站点
        self.run_command(f"ln -sf {nginx_conf_path} /etc/nginx/sites-enabled/")
        
        # 测试配置
        self.run_command("nginx -t")
        
        # 重启Nginx
        self.run_command("systemctl restart nginx")
        
        print("Nginx配置完成")
        
    def create_supervisor_config(self):
        """创建Supervisor配置"""
        print("创建Supervisor配置...")
        
        supervisor_config = f"""
        [program:ai-trading-api]
        command=/opt/ai-trading/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
        directory={self.base_dir}
        user=www
        autostart=true
        autorestart=true
        redirect_stderr=true
        stdout_logfile={self.logs_dir}/api.log
        stderr_logfile={self.logs_dir}/api-error.log
        environment=PYTHONPATH="{self.base_dir}"
        
        [program:ai-trading-monitor]
        command=/opt/ai-trading/bin/python -m monitoring.trading_monitor
        directory={self.base_dir}
        user=www
        autostart=true
        autorestart=true
        redirect_stderr=true
        stdout_logfile={self.logs_dir}/monitor.log
        stderr_logfile={self.logs_dir}/monitor-error.log
        environment=PYTHONPATH="{self.base_dir}"
        """
        
        # 写入Supervisor配置
        supervisor_conf_path = "/etc/supervisor/conf.d/ai-trading.conf"
        with open(supervisor_conf_path, 'w') as f:
            f.write(supervisor_config)
            
        # 重载配置
        self.run_command("supervisorctl reread")
        self.run_command("supervisorctl update")
        self.run_command("supervisorctl start ai-trading-api ai-trading-monitor")
        
        print("Supervisor配置完成")
        
    def create_environment_file(self):
        """创建环境变量文件"""
        print("创建环境变量文件...")
        
        env_content = f"""
        # 数据库配置
        DATABASE_URL=postgresql://ai_trader:ai_trading_password_123@localhost:5432/ai_trading
        
        # Redis配置
        REDIS_URL=redis://:ai_redis_password_123@localhost:6379/0
        
        # 应用配置
        DEBUG=False
        LOG_LEVEL=INFO
        SECRET_KEY=your_secret_key_here
        
        # 交易配置
        API_KEY=your_api_key_here
        SECRET_KEY=your_secret_key_here
        
        # 监控配置
        PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
        
        # 路径配置
        PYTHONPATH={self.base_dir}
        """
        
        # 写入环境文件
        env_file_path = self.base_dir / ".env"
        with open(env_file_path, 'w') as f:
            f.write(env_content)
            
        print("环境变量文件创建完成")
        
    def run_health_check(self):
        """运行健康检查"""
        print("运行健康检查...")
        
        # 检查服务状态
        services_to_check = [
            "nginx",
            "postgresql", 
            "redis-server",
            "supervisor"
        ]
        
        for service in services_to_check:
            result = self.run_command(f"systemctl is-active {service}")
            if result.returncode != 0:
                print(f"警告: {service} 服务未运行")
                
        # 检查应用健康
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=10)
            if response.status_code == 200:
                print("应用健康检查通过")
            else:
                print(f"应用健康检查失败: {response.status_code}")
        except Exception as e:
            print(f"应用健康检查异常: {e}")
            
        print("健康检查完成")
        
    def setup_log_rotation(self):
        """设置日志轮转"""
        print("设置日志轮转...")
        
        logrotate_config = f"""
        {self.base_dir}/logs/*.log {{
            daily
            missingok
            rotate 7
            compress
            delaycompress
            notifempty
            copytruncate
        }}
        
        /var/log/ai-trading/*.log {{
            daily
            missingok
            rotate 30
            compress
            delaycompress
            notifempty
            copytruncate
        }}
        """
        
        # 写入logrotate配置
        logrotate_path = "/etc/logrotate.d/ai-trading"
        with open(logrotate_path, 'w') as f:
            f.write(logrotate_config)
            
        print("日志轮转设置完成")
        
    def create_backup_script(self):
        """创建备份脚本"""
        print("创建备份脚本...")
        
        backup_script = f"""
        #!/bin/bash
        # AI量化交易系统备份脚本
        
        BACKUP_DIR="/backup/ai-trading"
        DATE=$(date +%Y%m%d_%H%M%S)
        
        # 创建备份目录
        mkdir -p $BACKUP_DIR
        
        # 备份数据库
        pg_dump -h localhost -U ai_trader ai_trading > $BACKUP_DIR/ai_trading_$DATE.sql
        
        # 备份应用代码
        tar -czf $BACKUP_DIR/app_$DATE.tar.gz {self.base_dir}
        
        # 备份配置文件
        tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/nginx/sites-available/ai-trading /etc/supervisor/conf.d/ai-trading.conf
        
        # 清理旧备份（保留7天）
        find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
        find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
        
        echo "备份完成: $BACKUP_DIR"
        """
        
        # 写入备份脚本
        backup_script_path = "/usr/local/bin/backup-ai-trading.sh"
        with open(backup_script_path, 'w') as f:
            f.write(backup_script)
            
        # 设置可执行权限
        self.run_command(f"chmod +x {backup_script_path}")
        
        print("备份脚本创建完成")
        
    def setup_cron_jobs(self):
        """设置定时任务"""
        print("设置定时任务...")
        
        cron_jobs = """
        # 每天凌晨2点备份数据库
        0 2 * * * /usr/local/bin/backup-ai-trading.sh
        
        # 每天凌晨3点清理日志
        0 3 * * * find /var/log/ai-trading -name "*.log.*" -mtime +30 -delete
        
        # 每分钟检查服务状态
        * * * * * systemctl is-active nginx > /dev/null || systemctl restart nginx
        """
        
        # 添加定时任务
        self.run_command(f"(crontab -l ; echo '{cron_jobs}') | crontab -")
        
        print("定时任务设置完成")
        
    def run_setup(self):
        """运行完整的设置流程"""
        print("开始AI量化交易系统宝塔面板设置...")
        
        steps = [
            ("安装系统依赖", self.install_system_dependencies),
            ("配置防火墙", self.configure_firewall),
            ("设置应用目录", self.setup_application_directory),
            ("配置数据库", self.configure_database),
            ("配置Redis", self.configure_redis),
            ("设置Python环境", self.setup_python_environment),
            ("创建环境变量文件", self.create_environment_file),
            ("创建Nginx配置", self.create_nginx_config),
            ("创建Supervisor配置", self.create_supervisor_config),
            ("设置日志轮转", self.setup_log_rotation),
            ("创建备份脚本", self.create_backup_script),
            ("设置定时任务", self.setup_cron_jobs),
            ("运行健康检查", self.run_health_check)
        ]
        
        for step_name, step_func in steps:
            print(f"\n=== {step_name} ===")
            try:
                step_func()
                print(f"✓ {step_name} 完成")
            except Exception as e:
                print(f"✗ {step_name} 失败: {e}")
                # 可以继续执行其他步骤
                
        print("\n=== AI量化交易系统宝塔面板设置完成 ===")
        print("请检查以下服务是否正常运行:")
        print("1. Nginx: systemctl status nginx")
        print("2. PostgreSQL: systemctl status postgresql")
        print("3. Redis: systemctl status redis-server")
        print("4. Supervisor: supervisorctl status")
        print("5. 应用: curl http://127.0.0.1:8000/health")

if __name__ == "__main__":
    setup = BaotaPanelSetup()
    setup.run_setup()