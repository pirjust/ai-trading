# 腾讯云宝塔面板完整部署指南

## 📋 目录
1. [环境准备](#环境准备)
2. [宝塔面板安装](#宝塔面板安装)
3. [系统依赖安装](#系统依赖安装)
4. [数据库配置](#数据库配置)
5. [Python环境配置](#python环境配置)
6. [AI量化交易系统部署](#ai量化交易系统部署)
7. [Web服务配置](#web服务配置)
8. [监控和日志配置](#监控和日志配置)
9. [安全配置](#安全配置)
10. [启动和测试](#启动和测试)

---

## 🚀 环境准备

### 1.1 服务器要求
- **操作系统**: Ubuntu 20.04/22.04 LTS (推荐)
- **CPU**: 最低2核，推荐4核
- **内存**: 最低4GB，推荐8GB
- **存储**: 最低50GB，推荐100GB SSD
- **网络**: 公网IP，开放必要端口

### 1.2 腾讯云服务器初始化

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 设置时区
sudo timedatectl set-timezone Asia/Shanghai

# 3. 配置主机名
sudo hostnamectl set-hostname ai-trading-server

# 4. 安装基础工具
sudo apt install -y curl wget git vim htop unzip software-properties-common

# 5. 配置防火墙（如果启用了UFW）
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8888/tcp  # 宝塔面板
sudo ufw allow 8000/tcp  # API服务
sudo ufw allow 5000/tcp  # 监控服务
sudo ufw enable
```

### 1.3 创建项目目录结构

```bash
# 创建主项目目录
sudo mkdir -p /www/wwwroot/ai-trading
sudo mkdir -p /www/wwwroot/ai-trading/{logs,backup,scripts,data}
sudo chown -R www-data:www-data /www/wwwroot/ai-trading

# 创建Python虚拟环境目录
sudo mkdir -p /www/envs
sudo chown -R www-data:www-data /www/envs
```

---

## 🛠️ 宝塔面板安装

### 2.1 安装宝塔面板

```bash
# 下载宝塔面板安装脚本
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh

# 执行安装
sudo bash install.sh ed8484bec

# 安装完成后会显示面板信息，请记录：
# 面板地址: http://your-server-ip:8888
# 用户名和密码: 会随机生成
```

### 2.2 宝塔面板首次配置

```bash
# 登录宝塔面板后，建议：
# 1. 修改默认端口（8888改为其他端口）
# 2. 绑定域名
# 3. 开启面板SSL
# 4. 修改默认用户名和密码
```

### 2.3 宝塔面板核心模块安装路径

```
/www/server/                    # 宝塔核心目录
├── nginx/                      # Nginx服务
│   ├── conf/                   # 配置文件
│   │   ├── nginx.conf         # 主配置文件
│   │   └── vhost/             # 虚拟主机配置
│   └── install/                # 安装目录
├── php/                        # PHP服务
│   ├── 74/                     # PHP 7.4版本
│   │   ├── etc/php-fpm.conf    # PHP-FPM配置
│   │   └── etc/php.ini         # PHP配置
│   └── 81/                     # PHP 8.1版本
├── mysql/                      # MySQL服务
│   ├── data/                   # 数据文件
│   ├── my.cnf                 # MySQL配置文件
│   └── bin/                    # 执行文件
├── postgresql/                  # PostgreSQL服务
│   ├── data/                   # 数据文件
│   ├── postgresql.conf         # 主配置文件
│   └── pg_hba.conf            # 访问控制配置
├── redis/                      # Redis服务
│   ├── redis.conf              # Redis配置文件
│   └── data/                   # 数据文件
├── panel/                      # 面板程序
└── bt-crond/                   # 计划任务
```

---

## 📦 系统依赖安装

### 3.1 安装基础系统依赖

```bash
# 在宝塔面板终端中执行

# 1. 安装Python相关依赖
sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip build-essential

# 2. 安装系统库依赖
sudo apt install -y \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    gfortran

# 3. 安装PostgreSQL客户端
sudo apt install -y postgresql-client

# 4. 安装Redis客户端
sudo apt install -y redis-tools

# 5. 安装系统监控工具
sudo apt install -y htop iotop nethogs
```

### 3.2 在宝塔面板中安装软件栈

1. **登录宝塔面板**
2. **软件商店 → 安装以下软件**：
   - **Nginx**: 1.20+
   - **PostgreSQL**: 13+ (不要安装MySQL，我们使用腾讯云PostgreSQL)
   - **Redis**: 6.0+
   - **Python项目管理器**: 用于管理Python项目
   - **PM2管理器**: 用于进程管理

---

## 🗄️ 数据库配置

### 4.1 腾讯云PostgreSQL配置

#### 4.1.1 创建腾讯云PostgreSQL实例

```bash
# 1. 登录腾讯云控制台
# 2. 云产品 → PostgreSQL → 新建实例
# 3. 配置参数：
#    - 实例规格: 4核8GB（根据需求选择）
#    - 存储空间: 100GB SSD
#    - 网络: 选择与服务器同一VPC
#    - 数据库版本: PostgreSQL 13
#    - 数据库名: ai_trading
#    - 用户名: ai_trader
#    - 密码: 设置强密码
```

#### 4.1.2 配置数据库访问权限

```sql
-- 连接到腾讯云PostgreSQL实例后执行

-- 1. 创建数据库
CREATE DATABASE ai_trading;

-- 2. 创建用户
CREATE USER ai_trader WITH PASSWORD 'your_secure_password_here';

-- 3. 授权
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;

-- 4. 授权schema
\c ai_trading;
GRANT ALL ON SCHEMA public TO ai_trader;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_trader;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_trader;

-- 5. 修改用户密码策略
ALTER USER ai_trader WITH PASSWORD 'your_secure_password_here' VALID UNTIL 'infinity';
```

#### 4.1.3 配置远程连接

```bash
# 1. 在腾讯云PostgreSQL控制台设置白名单
#    - 添加服务器公网IP到白名单
#    - 添加内网IP段（如172.16.0.0/16）

# 2. 配置pg_hba.conf（如果需要）
# 编辑文件位置：/www/server/postgresql/data/pg_hba.conf
sudo vim /www/server/postgresql/data/pg_hba.conf

# 添加以下行（在文件末尾）：
host    ai_trading    ai_trader    0.0.0.0/0    md5
```

### 4.2 腾讯云Redis配置

```bash
# 1. 在腾讯云控制台创建Redis实例
#    - 版本: Redis 6.2
#    - 规格: 4GB内存
#    - 网络: 与PostgreSQL同一VPC
#    - 密码: 设置强密码

# 2. 配置白名单
#    - 添加服务器IP到白名单

# 3. 测试连接
redis-cli -h your-redis-host -p 6379 -a your_redis_password
```

---

## 🐍 Python环境配置

### 5.1 创建Python虚拟环境

```bash
# 在宝塔面板终端中执行

# 1. 切换到项目目录
cd /www/wwwroot/ai-trading

# 2. 创建Python虚拟环境
sudo /usr/bin/python3.9 -m venv /www/envs/ai-trading

# 3. 激活虚拟环境
source /www/envs/ai-trading/bin/activate

# 4. 升级pip
pip install --upgrade pip setuptools wheel

# 5. 设置权限
sudo chown -R www-data:www-data /www/envs/ai-trading
```

### 5.2 安装Python依赖

```bash
# 激活虚拟环境后执行
source /www/envs/ai-trading/bin/activate

# 1. 安装系统依赖
pip install numpy==1.24.3 pandas==2.0.3 scipy==1.10.1

# 2. 安装机器学习依赖
pip install scikit-learn==1.3.0 tensorflow==2.13.0 torch==2.0.1

# 3. 安装交易相关依赖
pip install ccxt==4.0.85 websocket-client==1.6.1

# 4. 安装数据库依赖
pip install psycopg2-binary==2.9.7 redis==4.6.0 sqlalchemy==2.0.20

# 5. 安装Web框架依赖
pip install fastapi==0.103.1 uvicorn==0.23.2 python-multipart==0.0.6

# 6. 安装监控依赖
pip install prometheus-client==0.17.1 psutil==5.9.5

# 7. 安装项目依赖
pip install -r requirements.txt
```

---

## 🚀 AI量化交易系统部署

### 6.1 上传项目文件

```bash
# 1. 克隆或上传项目到服务器
cd /www/wwwroot/ai-trading
git clone https://github.com/your-repo/ai-trading.git .

# 或者使用SCP上传
# scp -r ./ai-trading/* root@your-server:/www/wwwroot/ai-trading/

# 2. 设置文件权限
sudo chown -R www-data:www-data /www/wwwroot/ai-trading
sudo chmod -R 755 /www/wwwroot/ai-trading

# 3. 创建必要目录
mkdir -p logs backup data models
```

### 6.2 配置环境变量

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑环境变量
vim .env
```

```env
# .env 文件配置内容
# ======================
# 腾讯云数据库配置
# ======================
DATABASE_URL=postgresql://ai_trader:your_secure_password_here@your-postgres-host:5432/ai_trading
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=ai_trading
DB_USER=ai_trader
DB_PASSWORD=your_secure_password_here
DB_SSL_MODE=require

# 腾讯云Redis配置
REDIS_URL=redis://:your_redis_password@your-redis-host:6379/0
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# PostgreSQL连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# ======================
# 应用配置
# ======================
SECRET_KEY=your_very_long_secret_key_here
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FILE=/www/wwwroot/ai-trading/logs/ai_trading.log

# ======================
# 交易配置
# ======================
DEFAULT_LEVERAGE=1
MAX_POSITION_SIZE=10000
RISK_LIMIT=0.02
CONFIDENCE_THRESHOLD=0.7
TRANSACTION_FEE=0.001

# ======================
# API配置
# ======================
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret_key
OKX_PASSPHRASE=your_okx_passphrase
OKX_SANDBOX=false

BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET_KEY=your_bybit_secret_key
BYBIT_SANDBOX=false

# ======================
# 监控配置
# ======================
PROMETHEUS_PORT=8000
GRAFANA_PORT=3000
METRICS_INTERVAL=60

# ======================
# AI模型配置
# ======================
MODEL_PATH=/www/wwwroot/ai-trading/models
TRAINING_INTERVAL=3600
RETRAIN_THRESHOLD=0.8
```

### 6.3 数据库初始化

```bash
# 1. 运行数据库迁移脚本
cd /www/wwwroot/ai-trading
source /www/envs/ai-trading/bin/activate

# 2. 运行数据库初始化
python scripts/init_database.py

# 3. 运行数据迁移
python scripts/database_migration.py

# 4. 测试数据库连接
python -c "
from core.database import test_connection
result = test_connection()
print('数据库连接成功!' if result else '数据库连接失败!')
"
```

### 6.4 创建系统服务

```bash
# 1. 创建systemd服务文件
sudo vim /etc/systemd/system/ai-trading.service
```

```ini
[Unit]
Description=AI Trading System
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/www/wwwroot/ai-trading
Environment=PATH=/www/envs/ai-trading/bin
ExecStart=/www/envs/ai-trading/bin/python app/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 2. 创建监控服务
sudo vim /etc/systemd/system/ai-trading-monitor.service
```

```ini
[Unit]
Description=AI Trading Monitor
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/www/wwwroot/ai-trading
Environment=PATH=/www/envs/ai-trading/bin
ExecStart=/www/envs/ai-trading/bin/python monitoring/system_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 3. 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable ai-trading ai-trading-monitor
sudo systemctl start ai-trading ai-trading-monitor

# 4. 检查服务状态
sudo systemctl status ai-trading
sudo systemctl status ai-trading-monitor
```

---

## 🌐 Web服务配置

### 7.1 Nginx配置

```bash
# 1. 创建Nginx配置文件
sudo vim /www/server/nginx/conf/vhost/ai-trading.conf
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 替换为你的域名
    
    # SSL证书配置（使用宝塔面板申请的SSL证书）
    ssl_certificate /www/server/panel/vhost/cert/your-domain.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    
    # 安全头部
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # 前端静态文件
    location / {
        root /www/wwwroot/ai-trading/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 监控接口
    location /metrics {
        proxy_pass http://127.0.0.1:8000/metrics;
        allow 127.0.0.1;
        allow your_monitoring_ip;  # 监控服务器IP
        deny all;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    # 日志配置
    access_log /www/wwwlogs/ai-trading_access.log;
    error_log /www/wwwlogs/ai-trading_error.log;
}
```

### 7.2 前端部署

```bash
# 1. 进入前端目录
cd /www/wwwroot/ai-trading/frontend

# 2. 安装依赖
npm install

# 3. 构建生产版本
npm run build

# 4. 设置权限
sudo chown -R www-data:www-data /www/wwwroot/ai-trading/frontend/dist
sudo chmod -R 755 /www/wwwroot/ai-trading/frontend/dist
```

### 7.3 重新加载Nginx配置

```bash
# 1. 测试配置文件
sudo nginx -t

# 2. 重新加载配置
sudo nginx -s reload

# 3. 重启Nginx
sudo systemctl restart nginx
```

---

## 📊 监控和日志配置

### 8.1 配置日志轮转

```bash
# 创建logrotate配置
sudo vim /etc/logrotate.d/ai-trading
```

```
/www/wwwroot/ai-trading/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload ai-trading
    endscript
}
```

### 8.2 配置Prometheus监控

```bash
# 1. 安装Prometheus（如果需要）
sudo apt install -y prometheus

# 2. 创建Prometheus配置
sudo vim /etc/prometheus/prometheus.yml
```

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-trading'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

rule_files:
  - "/etc/prometheus/rules/*.yml"
```

### 8.3 配置告警规则

```bash
# 1. 创建告警规则文件
sudo mkdir -p /etc/prometheus/rules
sudo vim /etc/prometheus/rules/ai-trading-alerts.yml
```

```yaml
groups:
  - name: ai-trading-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
```

---

## 🔒 安全配置

### 9.1 防火墙配置

```bash
# 配置UFW防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH（限制源IP）
sudo ufw allow from your_admin_ip to any port 22

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许宝塔面板（限制源IP）
sudo ufw allow from your_admin_ip to any port 8888

# 允许数据库连接（仅限内网）
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 10.0.0.0/8 to any port 6379

# 启用防火墙
sudo ufw enable
```

### 9.2 SSH安全配置

```bash
# 编辑SSH配置
sudo vim /etc/ssh/sshd_config
```

```ini
# SSH安全配置
Port 22                    # 可以改为其他端口
PermitRootLogin no
PasswordAuthentication no   # 使用密钥认证
PubkeyAuthentication yes
Protocol 2
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

```bash
# 重启SSH服务
sudo systemctl restart ssh
```

### 9.3 应用安全配置

```bash
# 1. 创建专门的运行用户
sudo adduser --system --no-create-home --group ai-trading

# 2. 设置文件权限
sudo chown -R ai-trading:ai-trading /www/wwwroot/ai-trading
sudo chmod -R 750 /www/wwwroot/ai-trading

# 3. 配置SELinux（如果启用）
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
```

---

## 🚀 启动和测试

### 10.1 系统启动检查

```bash
# 1. 检查所有服务状态
sudo systemctl status ai-trading
sudo systemctl status ai-trading-monitor
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# 2. 检查端口监听
sudo netstat -tlnp | grep -E ':(80|443|8000|5432|6379)'

# 3. 检查日志
sudo journalctl -u ai-trading -f
sudo tail -f /www/wwwroot/ai-trading/logs/ai_trading.log
```

### 10.2 数据库连接测试

```bash
# 1. 测试PostgreSQL连接
psql -h your-postgres-host -U ai_trader -d ai_trading -c "SELECT version();"

# 2. 测试Redis连接
redis-cli -h your-redis-host -p 6379 -a your_redis_password ping

# 3. 运行系统集成测试
cd /www/wwwroot/ai-trading
source /www/envs/ai-trading/bin/activate
python test_system_integration.py
```

### 10.3 API接口测试

```bash
# 1. 测试健康检查
curl -X GET https://your-domain.com/api/health

# 2. 测试API文档
curl -X GET https://your-domain.com/api/docs

# 3. 测试认证接口
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### 10.4 前端访问测试

```bash
# 1. 检查前端文件
ls -la /www/wwwroot/ai-trading/frontend/dist/

# 2. 访问网站
# 在浏览器中访问: https://your-domain.com

# 3. 检查静态资源
curl -I https://your-domain.com/
```

---

## 📋 关键配置文件路径汇总

### 系统配置文件
```
/etc/systemd/system/ai-trading.service          # 主服务配置
/etc/systemd/system/ai-trading-monitor.service   # 监控服务配置
/etc/logrotate.d/ai-trading                      # 日志轮转配置
/etc/ssh/sshd_config                             # SSH配置
/etc/ufw/user.rules                              # 防火墙规则
```

### 宝塔面板配置文件
```
/www/server/nginx/conf/nginx.conf                 # Nginx主配置
/www/server/nginx/conf/vhost/ai-trading.conf     # 站点配置
/www/server/postgresql/data/postgresql.conf      # PostgreSQL配置
/www/server/redis/redis.conf                     # Redis配置
```

### 应用配置文件
```
/www/wwwroot/ai-trading/.env                     # 环境变量
/www/wwwroot/ai-trading/config/                 # 应用配置目录
/www/wwwroot/ai-trading/logs/                    # 日志目录
/www/wwwroot/ai-trading/requirements.txt         # Python依赖
```

---

## ⚠️ 重要注意事项

### 11.1 安全注意事项
1. **定期更新**: 保持系统和依赖包的最新版本
2. **备份策略**: 配置自动备份，包括数据库和代码
3. **监控告警**: 设置关键指标的监控和告警
4. **访问控制**: 限制管理界面的访问IP
5. **密码安全**: 使用强密码并定期更换

### 11.2 性能优化建议
1. **数据库优化**: 配置连接池和索引优化
2. **缓存策略**: 使用Redis缓存频繁访问的数据
3. **静态资源**: 配置CDN加速静态文件访问
4. **负载均衡**: 在高并发时考虑负载均衡

### 11.3 故障排除

#### 常见问题及解决方案：

```bash
# 1. 服务无法启动
sudo journalctl -u ai-trading -n 50

# 2. 数据库连接失败
ping your-postgres-host
telnet your-postgres-host 5432

# 3. 前端无法访问
sudo nginx -t
sudo systemctl status nginx

# 4. 权限问题
sudo chown -R www-data:www-data /www/wwwroot/ai-trading
sudo chmod -R 755 /www/wwwroot/ai-trading
```

### 11.4 监控指标

需要重点监控的指标：
- CPU使用率 < 80%
- 内存使用率 < 85%
- 磁盘使用率 < 90%
- API响应时间 < 2秒
- 错误率 < 1%
- 数据库连接数 < 最大连接数的80%

---

## 📞 技术支持

如果在部署过程中遇到问题，可以：
1. 查看系统日志：`sudo journalctl -xe`
2. 查看应用日志：`tail -f /www/wwwroot/ai-trading/logs/ai_trading.log`
3. 检查服务状态：`sudo systemctl status ai-trading`
4. 联系腾讯云技术支持

---

*最后更新时间：2024年11月*
*文档版本：v1.0*