#!/usr/bin/env python3
"""
AI量化交易系统部署环境配置
用于GitHub Actions和宝塔面板部署
"""

import os
import json
import yaml
from typing import Dict, Any, List


class DeploymentConfig:
    """部署配置类"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        config_file = f"config/deployment_{self.environment}.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "environment": self.environment,
            "database": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "ai_trading",
                    "username": "ai_trader",
                    "password": "your_secure_password_123",
                    "pool_size": 20,
                    "max_overflow": 30
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "password": "your_redis_password_123",
                    "db": 0,
                    "decode_responses": True
                }
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "workers": 4,
                "timeout": 120,
                "log_level": "INFO"
            },
            "frontend": {
                "build_path": "frontend/dist",
                "public_path": "/www/wwwroot/ai-trading/frontend/dist"
            },
            "monitoring": {
                "enabled": True,
                "port": 9090,
                "metrics_path": "/metrics"
            },
            "security": {
                "allowed_hosts": ["*"],
                "cors_origins": ["*"],
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 100
                }
            }
        }
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        db_config = self.config["database"]["postgresql"]
        return f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        redis_config = self.config["database"]["redis"]
        if redis_config["password"]:
            return f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        else:
            return f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
    
    def generate_env_file(self, output_path: str = ".env") -> None:
        """生成环境变量文件"""
        env_content = f"""
# AI量化交易系统环境配置
# 环境: {self.environment}

# 数据库配置
DATABASE_URL={self.get_database_url()}
REDIS_URL={self.get_redis_url()}

# API配置
API_HOST={self.config['api']['host']}
API_PORT={self.config['api']['port']}
LOG_LEVEL={self.config['api']['log_level']}
DEBUG=False

# 安全配置
SECRET_KEY=your_secret_key_change_in_production
ALLOWED_HOSTS={','.join(self.config['security']['allowed_hosts'])}

# 监控配置
PROMETHEUS_ENABLED={self.config['monitoring']['enabled']}

# 交易所API配置（请替换为实际值）
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase

# 风控配置
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
MAX_DRAWDOWN=0.15
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(env_content.strip())
        
        print(f"✅ 环境文件已生成: {output_path}")
    
    def generate_nginx_config(self, domain: str = "your-domain.com") -> str:
        """生成Nginx配置"""
        return f"""
server {{
    listen 80;
    server_name {domain};
    
    # 前端静态文件
    location / {{
        root {self.config['frontend']['public_path']};
        index index.html;
        try_files $uri $uri/ /index.html;
    }}
    
    # API代理
    location /api/ {{
        proxy_pass http://{self.config['api']['host']}:{self.config['api']['port']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲区设置
        proxy_buffer_size 64k;
        proxy_buffers 4 64k;
        proxy_busy_buffers_size 128k;
    }}
    
    # 静态资源缓存
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
        root {self.config['frontend']['public_path']};
    }}
    
    # 健康检查
    location /health {{
        proxy_pass http://{self.config['api']['host']}:{self.config['api']['port']}/health;
        access_log off;
    }}
    
    # 安全设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}}
"""
    
    def generate_supervisor_config(self) -> str:
        """生成Supervisor配置"""
        return f"""
[program:ai-trading-api]
command=/opt/ai-trading/bin/python -m uvicorn app.main:app --host {self.config['api']['host']} --port {self.config['api']['port']} --workers {self.config['api']['workers']}
directory=/www/wwwroot/ai-trading
user=www
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/www/wwwroot/ai-trading/logs/api.log
stderr_logfile=/www/wwwroot/ai-trading/logs/api-error.log

[program:ai-trading-monitor]
command=/opt/ai-trading/bin/python -m monitoring.trading_monitor
directory=/www/wwwroot/ai-trading
user=www
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/www/wwwroot/ai-trading/logs/monitor.log
stderr_logfile=/www/wwwroot/ai-trading/logs/monitor-error.log
"""


class DependencyManager:
    """依赖管理类"""
    
    def __init__(self):
        self.dependencies = self._load_dependencies()
    
    def _load_dependencies(self) -> Dict[str, List[str]]:
        """加载依赖配置"""
        return {
            "core": [
                "fastapi>=0.100.0",
                "uvicorn[standard]>=0.23.0",
                "gunicorn>=21.0.0",
                "python-multipart>=0.0.6"
            ],
            "database": [
                "psycopg2-binary>=2.9.7",
                "redis>=5.0.0",
                "sqlalchemy>=2.0.0",
                "alembic>=1.12.0"
            ],
            "trading": [
                "ccxt>=4.1.0",
                "pandas>=2.0.0",
                "numpy>=1.24.0",
                "requests>=2.31.0",
                "websocket-client>=1.6.0"
            ],
            "ai_ml": [
                "scikit-learn>=1.3.0",
                "torch>=2.0.0",
                "torchvision>=0.15.0",
                "tensorflow>=2.13.0"
            ],
            "monitoring": [
                "prometheus-client>=0.17.0",
                "psutil>=5.9.0"
            ],
            "dev": [
                "pytest>=7.4.0",
                "pytest-asyncio>=0.21.0",
                "black>=23.0.0",
                "flake8>=6.0.0",
                "mypy>=1.5.0"
            ]
        }
    
    def generate_requirements_txt(self, include_dev: bool = False) -> str:
        """生成requirements.txt文件内容"""
        requirements = []
        
        for category, deps in self.dependencies.items():
            if category == "dev" and not include_dev:
                continue
            requirements.extend(deps)
        
        return "\n".join(sorted(set(requirements)))
    
    def generate_pyproject_toml(self, project_name: str = "ai-trading") -> str:
        """生成pyproject.toml文件内容"""
        return f"""
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "1.0.0"
description = "AI量化交易系统"
authors = [
    {{name = "AI Trading Team", email = "team@ai-trading.com"}}
]
readme = "README.md"
license = {{file = "LICENSE"}}
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "gunicorn>=21.0.0",
    "python-multipart>=0.0.6",
    "psycopg2-binary>=2.9.7",
    "redis>=5.0.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "ccxt>=4.1.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "requests>=2.31.0",
    "websocket-client>=1.6.0",
    "scikit-learn>=1.3.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "tensorflow>=2.13.0",
    "prometheus-client>=0.17.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.urls]
Homepage = "https://github.com/your-org/ai-trading"
Repository = "https://github.com/your-org/ai-trading"
Documentation = "https://ai-trading.readthedocs.io"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "E501", "W503"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
"""


def main():
    """主函数"""
    print("🚀 AI量化交易系统部署配置生成器")
    print("=" * 50)
    
    # 生成环境配置
    config = DeploymentConfig("production")
    config.generate_env_file(".env.production")
    
    # 生成Nginx配置
    nginx_config = config.generate_nginx_config("your-domain.com")
    with open("config/nginx.conf", "w", encoding='utf-8') as f:
        f.write(nginx_config)
    print("✅ Nginx配置已生成: config/nginx.conf")
    
    # 生成Supervisor配置
    supervisor_config = config.generate_supervisor_config()
    with open("config/supervisor.conf", "w", encoding='utf-8') as f:
        f.write(supervisor_config)
    print("✅ Supervisor配置已生成: config/supervisor.conf")
    
    # 生成依赖文件
    dep_manager = DependencyManager()
    
    # 生成requirements.txt
    requirements = dep_manager.generate_requirements_txt()
    with open("requirements.txt", "w", encoding='utf-8') as f:
        f.write(requirements)
    print("✅ requirements.txt已生成")
    
    # 生成pyproject.toml
    pyproject_content = dep_manager.generate_pyproject_toml()
    with open("pyproject.toml", "w", encoding='utf-8') as f:
        f.write(pyproject_content)
    print("✅ pyproject.toml已生成")
    
    print("\n🎯 部署配置完成！")
    print("请检查以下文件并根据实际情况修改配置：")
    print("1. .env.production - 环境变量配置")
    print("2. config/nginx.conf - Nginx服务器配置")
    print("3. config/supervisor.conf - 进程管理配置")
    print("4. requirements.txt - Python依赖包")
    print("5. pyproject.toml - 项目配置")


if __name__ == "__main__":
    main()