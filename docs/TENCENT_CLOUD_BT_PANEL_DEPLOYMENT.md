# 腾讯云宝塔面板AI量化交易系统完整部署指南

## 目录
- [1. 环境准备和服务器配置](#1-环境准备和服务器配置)
- [2. 宝塔面板安装和基础配置](#2-宝塔面板安装和基础配置)
- [3. 核心软件安装和配置](#3-核心软件安装和配置)
- [4. 项目部署和文件配置](#4-项目部署和文件配置)
- [5. 数据库配置和初始化](#5-数据库配置和初始化)
- [6. 应用服务配置和启动](#6-应用服务配置和启动)
- [7. Nginx反向代理和SSL配置](#7-nginx反向代理和ssl配置)
- [8. 监控系统配置](#8-监控系统配置)
- [9. 安全加固和性能优化](#9-安全加固和性能优化)
- [10. 测试验证和故障排除](#10-测试验证和故障排除)

---

## 1. 环境准备和服务器配置

### 1.1 腾讯云服务器购买和配置

**推荐配置：**
- **实例规格**: S5 (2核4GB起步，建议4核8GB+)
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 7.9+
- **系统盘**: 50GB SSD
- **数据盘**: 100GB+ SSD
- **带宽**: 5Mbps起步，建议10Mbps+

**腾讯云购买步骤：**
1. 登录腾讯云控制台
2. 选择产品 → 云服务器 → CVM
3. 点击"新建实例"
4. 选择地域（建议选择延迟较低的地域）
5. 选择实例规格：`计算型 S5`
6. 选择镜像：`Ubuntu Server 20.04 LTS 64位`
7. 选择系统盘：`高性能云硬盘 50GB`
8. 配置网络：`默认VPC`，`默认子网`
9. 配置带宽：`按带宽计费`，`5Mbps`
10. 设置安全组：放行端口（22, 80, 443, 8000, 3000）
11. 设置登录方式：`SSH密钥` 或 `设置密码`

### 1.2 服务器基础环境配置

**通过SSH连接服务器：**
```bash
# 使用密钥连接
ssh -i your-key.pem root@YOUR_SERVER_IP

# 或使用密码连接
ssh root@YOUR_SERVER_IP
```

**更新系统和基础软件：**
```bash
# Ubuntu/Debian
apt update && apt upgrade -y
apt install -y curl wget git vim htop unzip

# CentOS/RHEL
yum update -y
yum install -y curl wget git vim htop unzip

# 设置时区为东八区
timedatectl set-timezone Asia/Shanghai

# 配置主机名
hostnamectl set-hostname ai-trading-server
echo "127.0.0.1 ai-trading-server" >> /etc/hosts
```

**配置防火墙（Ubuntu）：**
```bash
# 安装ufw
apt install ufw -y

# 重置防火墙规则
ufw --force reset

# 默认策略
ufw default deny incoming
ufw default allow outgoing

# 开放必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8888/tcp  # 宝塔面板
ufw allow 8000/tcp  # 后端API
ufw allow 3000/tcp  # 前端开发端口
ufw allow 3306/tcp  # MySQL（可选）
ufw allow 5432/tcp  # PostgreSQL（可选）
ufw allow 6379/tcp  # Redis（可选）

# 启用防火墙
ufw --force enable

# 查看状态
ufw status verbose
```

**配置防火墙（CentOS）：**
```bash
# 安装firewalld
yum install firewalld -y
systemctl enable firewalld
systemctl start firewalld

# 开放端口
firewall-cmd --permanent --add-port=22/tcp
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-port=8888/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=3000/tcp

# 重载配置
firewall-cmd --reload

# 查看开放端口
firewall-cmd --list-ports
```

**配置交换空间（内存不足时）：**
```bash
# 创建4GB交换文件
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 优化交换空间使用
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p

# 查看交换空间
free -h
swapon --show
```

---

## 2. 宝塔面板安装和基础配置

### 2.1 安装宝塔面板

**Ubuntu/Debian系统安装：**
```bash
# 下载安装脚本
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh

# 执行安装（可能需要5-30分钟）
sudo bash install.sh

# 安装完成后会显示面板信息
# 外网面板地址: http://YOUR_SERVER_IP:8888/xxxx
# 内网面板地址: http://内网IP:8888/xxxx
# username: admin
# password: 随机密码
```

**CentOS/RHEL系统安装：**
```bash
# 下载安装脚本
yum install -y wget
wget -O install.sh http://download.bt.cn/install/install_6.0.sh

# 执行安装
sh install.sh

# 安装完成后记录面板信息
```

### 2.2 宝塔面板基础配置

**首次登录配置：**
1. 访问面板地址：`http://YOUR_SERVER_IP:8888/xxxx`
2. 输入初始用户名和密码登录
3. 绑定宝塔账号（可选）
4. 推荐安装套件：`LNMP` 或 `LAMP`

**修改面板配置：**
```bash
# 修改面板端口（可选）
bt default

# 修改面板用户名和密码
bt 14  # 修改面板用户
bt 15  # 修改面板密码

# 查看面板信息
bt default

# 面板SSL配置（推荐）
bt 16  # 开启面板SSL
```

**宝塔面板常用命令：**
```bash
bt      # 面板管理主菜单
bt 1    # 停止面板
bt 2    # 启动面板
bt 3    # 重启面板
bt 4    # 查看面板默认信息
bt 5    # 修改面板端口
bt 6    # 修改面板密码
bt 7    # 修改面板用户名
bt 8    # 清理面板缓存
bt 9    # 清理面板垃圾文件
```

### 2.3 宝塔面板安全配置

**配置安全组（腾讯云）：**
1. 登录腾讯云控制台
2. 进入 CVM 实例管理
3. 点击目标实例 → 安全组 → 配置规则
4. 添加入站规则：
   - 端口：8888，协议：TCP，来源：0.0.0.0/0（或限制特定IP）
   - 端口：22，协议：TCP，来源：你的IP地址
   - 端口：80，协议：TCP，来源：0.0.0.0/0
   - 端口：443，协议：TCP，来源：0.0.0.0/0

**面板内安全设置：**
1. 进入宝塔面板 → 面板设置 → 安全设置
2. 开启：`面板SSL`、`基础验证`、`域名绑定`
3. 设置：`面板端口`、`授权IP`（限制访问IP）
4. 修改默认的用户名和密码

---

## 3. 核心软件安装和配置

### 3.1 在宝塔面板中安装软件

**通过宝塔面板软件商店安装：**

1. **登录宝塔面板**
2. **进入软件商店**
3. **搜索并安装以下软件：**

#### 必需软件列表：
- **Nginx**: 版本 1.20+（用于Web服务）
- **PostgreSQL**: 版本 13+（主数据库）
- **Redis**: 版本 6+（缓存和会话）
- **Python项目管理器**: 版本 2.0+（管理Python应用）
- **PM2管理器**: 版本 2.0+（进程管理，可选）
- **Docker管理器**: 版本 3.0+（容器化部署，推荐）

#### 安装步骤详解：
1. 在软件商店搜索"Nginx"
2. 点击安装 → 选择版本1.20
3. 等待安装完成（约2-5分钟）
4. 重复步骤安装其他软件

### 3.2 软件配置详解

#### PostgreSQL数据库配置：
```bash
# 查看PostgreSQL服务状态
systemctl status postgresql

# 启动PostgreSQL服务
systemctl start postgresql
systemctl enable postgresql

# 进入PostgreSQL命令行
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE ai_trading;
CREATE USER ai_trader WITH PASSWORD 'dxKYn2cDb6N6EC22';
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
ALTER USER ai_trader CREATEDB;

# 退出PostgreSQL
\q

# 配置PostgreSQL允许远程连接（如需要）
vim /etc/postgresql/13/main/postgresql.conf
# 修改：listen_addresses = 'localhost' → listen_addresses = '*'

vim /etc/postgresql/13/main/pg_hba.conf
# 在文件末尾添加：
host    all             all             0.0.0.0/0               md5

# 重启PostgreSQL服务
systemctl restart postgresql
```

#### Redis配置：
```bash
# 查看Redis服务状态
systemctl status redis-server

# 启动Redis服务
systemctl start redis-server
systemctl enable redis-server

# 配置Redis密码
vim /etc/redis/redis.conf
# 修改或添加：
requirepass U2839jkanj329xmJOP
bind 127.0.0.1

# 重启Redis服务
systemctl restart redis-server

# 测试Redis连接
redis-cli -a your_redis_password_123 ping
# 应该返回：PONG
```

#### Nginx基础配置：
```bash
# 查看Nginx状态
systemctl status nginx

# 启动Nginx服务
systemctl start nginx
systemctl enable nginx

# 测试Nginx配置
nginx -t

# 重载配置
nginx -s reload
```

### 3.3 Python环境配置

#### 安装Python 3.9+：
```bash
# 安装Python构建依赖
apt install -y build-essential libssl-dev libffi-dev python3-dev

# 下载并安装Python 3.9
wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
tar -xzf Python-3.9.16.tgz
cd Python-3.9.16
./configure --enable-optimizations
make -j$(nproc)
make altinstall

# 创建软链接
ln -sf /usr/local/bin/python3.9 /usr/bin/python3.9
ln -sf /usr/local/bin/pip3.9 /usr/bin/pip3.9

# 验证安装
python3.9 --version
pip3.9 --version
```

#### 配置虚拟环境：
```bash
# 安装virtualenv
pip3.9 install virtualenv

# 创建项目虚拟环境
mkdir -p /www/wwwroot/ai-trading
cd /www/wwwroot/ai-trading
python3.9 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装基础包
pip install wheel setuptools
```

---

## 4. 项目部署和文件配置

### 4.1 项目文件上传和目录结构

#### 创建项目目录：
```bash
# 创建主项目目录
mkdir -p /www/wwwroot/ai-trading
cd /www/wwwroot/ai-trading

# 创建必要的子目录
mkdir -p {logs,data,config,models,static,uploads,backups}

# 设置目录权限
chown -R www:www /www/wwwroot/ai-trading
chmod -R 755 /www/wwwroot/ai-trading
```

#### 上传项目文件：
**方式1：使用Git克隆（推荐）：**
```bash
# 克隆项目
cd /www/wwwroot/ai-trading
git clone https://github.com/your-repo/ai-trading.git .

# 检查文件结构
ls -la
```

**方式2：使用SCP上传：**
```bash
# 在本地执行，上传整个项目
scp -r ./ai-trading root@YOUR_SERVER_IP:/www/wwwroot/

# 压缩后上传（更快）
tar -czf ai-trading.tar.gz ./ai-trading
scp ai-trading.tar.gz root@YOUR_SERVER_IP:/www/wwwroot/
ssh root@YOUR_SERVER_IP "cd /www/wwwroot && tar -xzf ai-trading.tar.gz && rm ai-trading.tar.gz"
```

**方式3：使用宝塔面板文件管理器：**
1. 登录宝塔面板
2. 进入文件管理
3. 导航到 `/www/wwwroot/`
4. 上传项目压缩包
5. 解压缩并重命名为 `ai-trading`

#### 项目目录结构验证：
```bash
# 验证项目结构
cd /www/wwwroot/ai-trading
find . -type f -name "*.py" | head -20
find . -type f -name "*.js" | head -10
find . -name "*.json" | head -10

# 检查关键文件
ls -la requirements.txt
ls -la package.json
ls -la docker-compose.yml
ls -la .env.example
```

### 4.2 环境变量配置

#### 创建和配置.env文件：
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env
```

**完整的.env配置示例：**
```env
# ==================== 数据库配置 ====================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_trading
DB_USER=ai_trader
DB_PASSWORD=your_secure_password_123
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# ==================== Redis配置 ====================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_123
REDIS_DB=0
REDIS_POOL_SIZE=10

# ==================== 应用基础配置 ====================
APP_NAME=AI量化交易系统
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false
SECRET_KEY=your_32_character_long_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP,yourdomain.com
CORS_ORIGINS=http://localhost:3000,http://YOUR_SERVER_IP:3000,https://yourdomain.com

# ==================== Web服务配置 ====================
WEB_HOST=0.0.0.0
WEB_PORT=8000
WORKERS=4
RELOAD=false
LOG_LEVEL=INFO

# ==================== 交易所API配置 ====================
# 币安交易所
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BINANCE_TESTNET=false

# 欧意交易所
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here
OKX_SANDBOX=false

# ==================== 风控配置 ====================
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
MAX_DRAWDOWN=0.15
RISK_CHECK_INTERVAL=60

# ==================== 监控配置 ====================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
METRICS_ENABLED=true
LOG_EXPORT_ENABLED=true

# ==================== 邮件通知配置 ====================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password
SMTP_TLS=true

# ==================== 文件存储配置 ====================
UPLOAD_DIR=/www/wwwroot/ai-trading/uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=csv,json,png,jpg

# ==================== JWT配置 ====================
JWT_SECRET_KEY=your_jwt_secret_key_32_chars_long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ==================== 缓存配置 ====================
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# ==================== 日志配置 ====================
LOG_DIR=/www/wwwroot/ai-trading/logs
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
LOG_ROTATION=daily
```

### 4.3 依赖安装和项目初始化

#### 安装Python依赖：
```bash
# 激活虚拟环境
cd /www/wwwroot/ai-trading
source venv/bin/activate

# 升级pip和基础工具
pip install --upgrade pip setuptools wheel

# 安装项目依赖
pip install -r requirements.txt

# 如果安装失败，尝试逐个安装关键依赖
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis pandas numpy torch scikit-learn

# 验证安装
pip list | grep -E "(fastapi|sqlalchemy|redis|pandas|numpy)"
```

#### 安装前端依赖（如需要）：
```bash
# 安装Node.js（如果未安装）
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
apt-get install -y nodejs

# 进入前端目录
cd /www/wwwroot/ai-trading/frontend

# 安装前端依赖
npm install

# 构建生产版本
npm run build

# 返回项目根目录
cd ..
```

#### 创建日志目录和权限设置：
```bash
# 创建日志目录
mkdir -p /www/wwwroot/ai-trading/logs/{app,nginx,system}

# 设置权限
chown -R www:www /www/wwwroot/ai-trading/logs
chmod -R 755 /www/wwwroot/ai-trading/logs
chmod -R 777 /www/wwwroot/ai-trading/uploads

# 创建日志文件
touch /www/wwwroot/ai-trading/logs/app/backend.log
touch /www/wwwroot/ai-trading/logs/app/frontend.log
touch /www/wwwroot/ai-trading/logs/app/trading.log
touch /www/wwwroot/ai-trading/logs/system/error.log
```

---

## 5. 数据库配置和初始化

### 5.1 PostgreSQL数据库详细配置

#### 数据库用户和权限配置：
```bash
# 登录PostgreSQL
sudo -u postgres psql

# 创建专用数据库用户
CREATE USER ai_trader WITH PASSWORD 'your_secure_password_123';
ALTER USER ai_trader CREATEDB;
ALTER USER ai_trader CREATEROLE;

# 创建主数据库
CREATE DATABASE ai_trading OWNER ai_trader;
CREATE DATABASE ai_trading_test OWNER ai_trader;

# 赋予权限
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
GRANT ALL PRIVILEGES ON DATABASE ai_trading_test TO ai_trader;

# 连接到主数据库
\c ai_trading

# 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# 查看数据库列表
\l

# 退出
\q
```

#### PostgreSQL性能优化配置：
```bash
# 编辑PostgreSQL配置文件
vim /etc/postgresql/13/main/postgresql.conf
```

**添加或修改以下配置：**
```ini
# 内存配置（根据服务器内存调整）
shared_buffers = 1GB                    # 系统内存的25%
effective_cache_size = 3GB              # 系统内存的75%
work_mem = 64MB                         # 单个查询内存
maintenance_work_mem = 512MB             # 维护操作内存

# 连接配置
max_connections = 200                    # 最大连接数
listen_addresses = '*'                   # 允许远程连接
port = 5432

# 日志配置
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'                    # 记录所有SQL（开发环境）
log_min_duration_statement = 1000        # 记录慢查询（1秒以上）

# 性能监控
shared_preload_libraries = 'pg_stat_statements'
track_activity_query_size = 2048
pg_stat_statements.track = all

# 自动清理配置
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
```

```bash
# 编辑访问控制配置
vim /etc/postgresql/13/main/pg_hba.conf
```

**添加访问规则：**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 本地连接
local   all             postgres                                peer
local   all             all                                     md5

# IPv4本地连接
host    all             all             127.0.0.1/32            md5

# IPv6本地连接
host    all             all             ::1/128                 md5

# 允许应用服务器连接（替换IP为你的应用服务器IP）
host    ai_trading      ai_trader       10.0.0.0/8             md5
host    ai_trading      ai_trader       172.16.0.0/12           md5
host    ai_trading      ai_trader       192.168.0.0/16          md5
```

```bash
# 重启PostgreSQL服务
systemctl restart postgresql

# 验证配置
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW max_connections;"
```

### 5.2 数据库初始化脚本

#### 创建数据库初始化脚本：
```bash
# 创建初始化脚本
cat > /www/wwwroot/ai-trading/scripts/init_database.sql << 'EOF'
-- AI量化交易系统数据库初始化脚本

-- 创建数据库schema
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS strategies;
CREATE SCHEMA IF NOT EXISTS risk_management;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- 设置schema权限
GRANT ALL ON SCHEMA trading TO ai_trader;
GRANT ALL ON SCHEMA strategies TO ai_trader;
GRANT ALL ON SCHEMA risk_management TO ai_trader;
GRANT ALL ON SCHEMA monitoring TO ai_trader;

-- 创建枚举类型
CREATE TYPE order_status AS ENUM ('pending', 'filled', 'cancelled', 'rejected');
CREATE TYPE order_side AS ENUM ('buy', 'sell');
CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');
CREATE TYPE time_frame AS ENUM ('1m', '5m', '15m', '1h', '4h', '1d');
CREATE TYPE strategy_status AS ENUM ('active', 'inactive', 'testing', 'archived');
CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易所配置表
CREATE TABLE IF NOT EXISTS exchanges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(255),
    ws_endpoint VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建账户表
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange_id INTEGER REFERENCES exchanges(id),
    account_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    passphrase VARCHAR(255), -- OKX需要
    is_sandbox BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    balance DECIMAL(20,8) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易对表
CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    base_asset VARCHAR(10) NOT NULL,
    quote_asset VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    min_qty DECIMAL(20,8) DEFAULT 0.001,
    max_qty DECIMAL(20,8) DEFAULT 1000000.0,
    price_precision INTEGER DEFAULT 8,
    qty_precision INTEGER DEFAULT 8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建K线数据表
CREATE TABLE IF NOT EXISTS klines (
    id BIGSERIAL PRIMARY KEY,
    symbol_id INTEGER REFERENCES symbols(id),
    time_frame time_frame NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    quote_volume DECIMAL(20,8) NOT NULL,
    trades_count INTEGER DEFAULT 0,
    UNIQUE(symbol_id, time_frame, open_time)
);

-- 创建策略表
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL, -- technical, ml, rl, custom
    parameters JSONB,
    status strategy_status DEFAULT 'inactive',
    symbols INTEGER[] DEFAULT '{}',
    time_frames time_frame[] DEFAULT '{1h}',
    risk_level risk_level DEFAULT 'medium',
    max_position_size DECIMAL(10,4) DEFAULT 0.1,
    stop_loss DECIMAL(10,4) DEFAULT 0.02,
    take_profit DECIMAL(10,4) DEFAULT 0.05,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    symbol_id INTEGER REFERENCES symbols(id),
    order_id VARCHAR(100) UNIQUE, -- 交易所订单ID
    client_order_id VARCHAR(100) UNIQUE, -- 客户端订单ID
    side order_side NOT NULL,
    type order_type NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8), -- 市价单为空
    filled_quantity DECIMAL(20,8) DEFAULT 0.0,
    average_price DECIMAL(20,8),
    status order_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易表
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id) ON DELETE CASCADE,
    trade_id VARCHAR(100) UNIQUE, -- 交易所成交ID
    symbol_id INTEGER REFERENCES symbols(id),
    side order_side NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) DEFAULT 0.0,
    fee_asset VARCHAR(10) DEFAULT 'USDT',
    realized_pnl DECIMAL(20,8) DEFAULT 0.0,
    trade_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建风控警报表
CREATE TABLE IF NOT EXISTS risk_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL, -- position_size, daily_loss, drawdown, etc.
    severity risk_level NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    module VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_return DECIMAL(10,4), -- 总收益率
    daily_return DECIMAL(10,4), -- 日收益率
    max_drawdown DECIMAL(10,4), -- 最大回撤
    sharpe_ratio DECIMAL(10,4), -- 夏普比率
    win_rate DECIMAL(10,4), -- 胜率
    profit_factor DECIMAL(10,4), -- 盈亏比
    total_trades INTEGER, -- 总交易次数
    winning_trades INTEGER, -- 盈利交易次数
    losing_trades INTEGER, -- 亏损交易次数
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_id, date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_exchange_id ON accounts(exchange_id);
CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol);
CREATE INDEX IF NOT EXISTS idx_klines_symbol_time ON klines(symbol_id, open_time);
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_strategy_id ON orders(strategy_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol_id, trade_time);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_user_id ON risk_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_created_at ON risk_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_date ON performance_metrics(strategy_id, date);

-- 插入基础数据
INSERT INTO exchanges (name, display_name, api_endpoint, ws_endpoint) VALUES
('binance', 'Binance', 'https://api.binance.com', 'wss://stream.binance.com:9443'),
('okx', 'OKX', 'https://www.okx.com', 'wss://ws.okx.com:8443'),
('huobi', 'Huobi', 'https://api.huobi.com', 'wss://api.huobi.com'),
('bybit', 'Bybit', 'https://api.bybit.com', 'wss://stream.bybit.com');

INSERT INTO symbols (symbol, base_asset, quote_asset) VALUES
('BTCUSDT', 'BTC', 'USDT'),
('ETHUSDT', 'ETH', 'USDT'),
('BNBUSDT', 'BNB', 'USDT'),
('ADAUSDT', 'ADA', 'USDT'),
('SOLUSDT', 'SOL', 'USDT'),
('DOTUSDT', 'DOT', 'USDT');

-- 创建管理员用户（密码：admin123）
INSERT INTO users (username, email, password_hash, is_admin) VALUES
('admin', 'admin@aitrading.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm', true);

-- 授权用户访问schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_trader;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_trader;

EOF

# 执行初始化脚本
sudo -u postgres psql -d ai_trading -f /www/wwwroot/ai-trading/scripts/init_database.sql

# 验证表创建
sudo -u postgres psql -d ai_trading -c "\dt"
```

### 5.3 数据库连接测试

#### 创建数据库连接测试脚本：
```bash
# 创建测试脚本
cat > /www/wwwroot/ai-trading/scripts/test_db_connection.py << 'EOF'
#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import psycopg2
import sys
from psycopg2.extensions import connection as pg_connection

def test_database_connection():
    """测试数据库连接"""
    try:
        # 数据库连接参数
        db_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'ai_trading',
            'user': 'ai_trader',
            'password': 'your_secure_password_123'
        }
        
        # 连接数据库
        print("🔌 连接数据库...")
        conn: pg_connection = psycopg2.connect(**db_params)
        print("✅ 数据库连接成功!")
        
        # 创建游标
        cursor = conn.cursor()
        
        # 执行测试查询
        print("🔍 执行测试查询...")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 PostgreSQL版本: {version[0]}")
        
        # 检查表结构
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"📋 数据库表数量: {len(tables)}")
        
        # 检查用户表
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"👥 用户数量: {user_count}")
        
        # 检查交易所表
        cursor.execute("SELECT COUNT(*) FROM exchanges;")
        exchange_count = cursor.fetchone()[0]
        print(f"🏦 交易所数量: {exchange_count}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        print("✅ 数据库连接测试完成!")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
EOF

# 运行测试
cd /www/wwwroot/ai-trading
source venv/bin/activate
python scripts/test_db_connection.py
```

---

## 6. 应用服务配置和启动

### 6.1 PM2进程管理配置

#### 创建PM2配置文件：
```bash
# 创建PM2配置文件
cat > /www/wwwroot/ai-trading/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    // 后端API服务
    {
      name: 'ai-trading-api',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000 --workers 4',
      cwd: '/www/wwwroot/ai-trading',
      interpreter: '/www/wwwroot/ai-trading/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONPATH: '/www/wwwroot/ai-trading',
        ENVIRONMENT: 'production'
      },
      error_file: '/www/wwwroot/ai-trading/logs/app/api-error.log',
      out_file: '/www/wwwroot/ai-trading/logs/app/api-out.log',
      log_file: '/www/wwwroot/ai-trading/logs/app/api-combined.log',
      time: true
    },
    
    // 数据收集服务
    {
      name: 'ai-trading-data-collector',
      script: 'python',
      args: 'scripts/start_data_collection.py',
      cwd: '/www/wwwroot/ai-trading',
      interpreter: '/www/wwwroot/ai-trading/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PYTHONPATH: '/www/wwwroot/ai-trading'
      },
      error_file: '/www/wwwroot/ai-trading/logs/app/collector-error.log',
      out_file: '/www/wwwroot/ai-trading/logs/app/collector-out.log',
      log_file: '/www/wwwroot/ai-trading/logs/app/collector-combined.log',
      time: true
    },
    
    // 策略执行服务
    {
      name: 'ai-trading-strategy-runner',
      script: 'python',
      args: 'execution/trading_engine.py',
      cwd: '/www/wwwroot/ai-trading',
      interpreter: '/www/wwwroot/ai-trading/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONPATH: '/www/wwwroot/ai-trading'
      },
      error_file: '/www/wwwroot/ai-trading/logs/app/strategy-error.log',
      out_file: '/www/wwwroot/ai-trading/logs/app/strategy-out.log',
      log_file: '/www/wwwroot/ai-trading/logs/app/strategy-combined.log',
      time: true
    },
    
    // 风控监控服务
    {
      name: 'ai-trading-risk-monitor',
      script: 'python',
      args: 'risk_management/risk_monitor.py',
      cwd: '/www/wwwroot/ai-trading',
      interpreter: '/www/wwwroot/ai-trading/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PYTHONPATH: '/www/wwwroot/ai-trading'
      },
      error_file: '/www/wwwroot/ai-trading/logs/app/risk-error.log',
      out_file: '/www/wwwroot/ai-trading/logs/app/risk-out.log',
      log_file: '/www/wwwroot/ai-trading/logs/app/risk-combined.log',
      time: true
    }
  ]
};
EOF

# 安装PM2（如果未安装）
npm install -g pm2

# 启动PM2应用
cd /www/wwwroot/ai-trading
pm2 start ecosystem.config.js

# 保存PM2配置
pm2 save

# 设置PM2开机自启
pm2 startup
# 按照提示执行输出的命令（需要root权限）
```

#### PM2常用管理命令：
```bash
# 查看所有应用状态
pm2 status

# 查看特定应用日志
pm2 logs ai-trading-api

# 重启应用
pm2 restart ai-trading-api

# 停止应用
pm2 stop ai-trading-api

# 删除应用
pm2 delete ai-trading-api

# 重启所有应用
pm2 restart all

# 监控应用
pm2 monit

# 查看应用详细信息
pm2 show ai-trading-api
```

### 6.2 系统服务配置

#### 创建systemd服务文件：
```bash
# 创建AI交易系统服务文件
cat > /etc/systemd/system/ai-trading.service << 'EOF'
[Unit]
Description=AI Trading System
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=forking
User=www
Group=www
WorkingDirectory=/www/wwwroot/ai-trading
Environment=PYTHONPATH=/www/wwwroot/ai-trading
EnvironmentFile=/www/wwwroot/ai-trading/.env
ExecStart=/usr/bin/pm2 start ecosystem.config.js
ExecReload=/usr/bin/pm2 reload ecosystem.config.js
ExecStop=/usr/bin/pm2 stop ecosystem.config.js
PIDFile=/run/ai-trading.pid
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=ai-trading

[Install]
WantedBy=multi-user.target
EOF

# 创建PID目录
mkdir -p /run/ai-trading
chown www:www /run/ai-trading

# 启用并启动服务
systemctl daemon-reload
systemctl enable ai-trading.service
systemctl start ai-trading.service

# 检查服务状态
systemctl status ai-trading.service
```

### 6.3 应用启动脚本

#### 创建应用启动脚本：
```bash
# 创建启动脚本
cat > /www/wwwroot/ai-trading/scripts/start_app.sh << 'EOF'
#!/bin/bash
# AI交易系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3.9 &> /dev/null; then
        log_error "Python 3.9 未安装"
        exit 1
    fi
    
    # 检查PostgreSQL
    if ! systemctl is-active --quiet postgresql; then
        log_error "PostgreSQL 服务未运行"
        exit 1
    fi
    
    # 检查Redis
    if ! systemctl is-active --quiet redis-server; then
        log_error "Redis 服务未运行"
        exit 1
    fi
    
    log_info "✅ 所有依赖检查通过"
}

# 启动应用
start_app() {
    log_info "启动AI交易系统..."
    
    cd /www/wwwroot/ai-trading
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 运行数据库迁移（如果需要）
    if [ -f "scripts/migrate_db.py" ]; then
        log_info "运行数据库迁移..."
        python scripts/migrate_db.py
    fi
    
    # 启动PM2服务
    log_info "启动PM2服务..."
    pm2 start ecosystem.config.js
    
    # 保存PM2配置
    pm2 save
    
    log_info "✅ AI交易系统启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查API服务
    if curl -s http://localhost:8000/health > /dev/null; then
        log_info "✅ API服务健康"
    else
        log_warn "⚠️ API服务可能未完全启动"
    fi
    
    # 检查PM2进程
    pm2_status=$(pm2 jlist | jq length)
    log_info "📊 PM2进程数量: $pm2_status"
    
    if [ "$pm2_status" -eq 4 ]; then
        log_info "✅ 所有服务进程正常运行"
    else
        log_warn "⚠️ 部分服务进程可能异常"
    fi
}

# 主函数
main() {
    log_info "=== AI交易系统启动脚本 ==="
    
    check_dependencies
    start_app
    sleep 5
    health_check
    
    log_info "=== 启动完成 ==="
    log_info "API访问地址: http://$(hostname -I | awk '{print $1}'):8000"
    log_info "查看服务状态: pm2 status"
    log_info "查看日志: pm2 logs"
}

# 执行主函数
main "$@"
EOF

# 设置脚本权限
chmod +x /www/wwwroot/ai-trading/scripts/start_app.sh

# 创建停止脚本
cat > /www/wwwroot/ai-trading/scripts/stop_app.sh << 'EOF'
#!/bin/bash
# AI交易系统停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

main() {
    log_info "=== 停止AI交易系统 ==="
    
    cd /www/wwwroot/ai-trading
    
    # 停止PM2服务
    log_info "停止PM2服务..."
    pm2 stop ecosystem.config.js
    
    # 等待进程完全停止
    sleep 3
    
    log_info "✅ AI交易系统已停止"
}

main "$@"
EOF

# 设置脚本权限
chmod +x /www/wwwroot/ai-trading/scripts/stop_app.sh
```

---

## 7. Nginx反向代理和SSL配置

### 7.1 在宝塔面板中创建网站

#### 创建网站步骤：
1. **登录宝塔面板**
2. **点击"网站"**
3. **点击"添加站点"**
4. **填写站点信息：**
   - 域名：`yourdomain.com`（或使用IP地址：`YOUR_SERVER_IP`）
   - 根目录：`/www/wwwroot/ai-trading/frontend/dist`（如果前端已构建）
   - PHP版本：纯静态
   - 数据库：不创建（已单独配置）
5. **点击"提交"创建站点**

#### 配置网站设置：
1. **点击网站名称进入设置**
2. **配置文件修改**（重要步骤）
3. **SSL设置**（后续配置）

### 7.2 Nginx反向代理配置

#### 通过宝塔面板配置反向代理：

**方法1：使用宝塔面板界面**
1. 进入网站设置
2. 点击"反向代理"
3. 添加反向代理：
   - 代理名称：`ai-trading-api`
   - 目标URL：`http://127.0.0.1:8000`
   - 发送域名：`$host`
   - 缓存：关闭（API不需要缓存）

**方法2：直接编辑Nginx配置文件**
```bash
# 编辑Nginx配置文件
vim /www/server/panel/vhost/nginx/yourdomain.com.conf
```

**完整的Nginx配置示例：**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com YOUR_SERVER_IP;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com YOUR_SERVER_IP;
    
    # SSL证书配置（稍后配置）
    ssl_certificate /www/server/panel/vhost/cert/yourdomain.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/yourdomain.com/privkey.pem;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 日志配置
    access_log /www/wwwlogs/yourdomain.com.log;
    error_log /www/wwwlogs/yourdomain.com.error.log;
    
    # 静态文件服务
    location / {
        root /www/wwwroot/ai-trading/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
    
    # API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 缓冲配置
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # WebSocket代理
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket特殊配置
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
    }
    
    # 监控面板代理（可选）
    location /prometheus/ {
        proxy_pass http://127.0.0.1:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 认证保护（建议）
        auth_basic "Prometheus Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
    
    location /grafana/ {
        proxy_pass http://127.0.0.1:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
```

### 7.3 SSL证书配置

#### 通过宝塔面板申请Let's Encrypt免费SSL证书：

1. **进入网站设置**
2. **点击"SSL"选项卡**
3. **选择"Let's Encrypt"**
4. **勾选：**
   - 强制HTTPS
   - 默认站点（可选）
5. **点击"申请"**

证书申请成功后，宝塔会自动配置SSL并设置自动续期。

#### 手动配置SSL证书（可选）：

**使用Certbot申请证书：**
```bash
# 安装Certbot
apt install certbot python3-certbot-nginx -y

# 申请证书
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

**配置HTTP基本认证（保护监控面板）：**
```bash
# 安装htpasswd工具
apt install apache2-utils -y

# 创建认证用户
htpasswd -c /etc/nginx/.htpasswd admin
# 输入密码

# 重载Nginx配置
nginx -s reload
```

### 7.4 Nginx配置验证和重载

```bash
# 测试Nginx配置语法
nginx -t

# 如果测试通过，重载配置
nginx -s reload

# 检查Nginx状态
systemctl status nginx

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log

# 查看网站访问日志
tail -f /www/wwwlogs/yourdomain.com.log
```

---

## 8. 监控系统配置

### 8.1 Prometheus配置

#### 安装Prometheus：
```bash
# 创建Prometheus目录
mkdir -p /www/wwwroot/ai-trading/monitoring/prometheus
cd /www/wwwroot/ai-trading/monitoring/prometheus

# 下载Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar -xzf prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64

# 复制可执行文件
cp prometheus promtool /usr/local/bin/
cp -r console_libraries consoles /www/wwwroot/ai-trading/monitoring/prometheus/

# 创建配置目录
mkdir -p /www/wwwroot/ai-trading/monitoring/prometheus/{data,config}
```

#### 创建Prometheus配置文件：
```bash
# 创建Prometheus配置
cat > /www/wwwroot/ai-trading/monitoring/prometheus/config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/www/wwwroot/ai-trading/deploy/alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  # Prometheus自监控
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # AI交易系统监控
  - job_name: 'ai-trading-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # 系统监控（需要安装node_exporter）
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  # PostgreSQL监控（需要安装postgres_exporter）
  - job_name: 'postgresql-exporter'
    static_configs:
      - targets: ['localhost:9187']

  # Redis监控（需要安装redis_exporter）
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['localhost:9121']

  # Nginx监控（需要安装nginx_exporter）
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['localhost:9113']
EOF

# 创建Prometheus系统服务
cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
User=www
Group=www
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file=/www/wwwroot/ai-trading/monitoring/prometheus/config/prometheus.yml \
  --storage.tsdb.path=/www/wwwroot/ai-trading/monitoring/prometheus/data \
  --web.console.libraries=/www/wwwroot/ai-trading/monitoring/prometheus/console_libraries \
  --web.console.templates=/www/wwwroot/ai-trading/monitoring/prometheus/consoles \
  --storage.tsdb.retention.time=30d \
  --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
chown -R www:www /www/wwwroot/ai-trading/monitoring/prometheus

# 启动Prometheus服务
systemctl daemon-reload
systemctl enable prometheus.service
systemctl start prometheus.service

# 检查Prometheus状态
systemctl status prometheus.service
```

### 8.2 Grafana配置

#### 安装Grafana：
```bash
# 添加Grafana APT仓库
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# 更新包列表并安装Grafana
apt update
apt install grafana -y

# 启动Grafana服务
systemctl enable grafana-server
systemctl start grafana-server

# 修改Grafana配置
vim /etc/grafana/grafana.ini
```

**Grafana配置修改：**
```ini
[server]
# 监听端口
http_port = 3001
domain = yourdomain.com
root_url = https://yourdomain.com/grafana/

[security]
# 管理员密码
admin_user = admin
admin_password = your_secure_password_123

[users]
# 禁用用户注册（生产环境）
allow_sign_up = false

[auth.anonymous]
# 允许匿名访问
enabled = true
org_role = Viewer

[database]
# 使用PostgreSQL作为Grafana数据库
type = postgres
host = localhost:5432
name = grafana
user = grafana
password = grafana_password

[session]
# 会话提供者
provider = postgres
```

#### 配置Grafana数据源：
```bash
# 创建Grafana数据库和用户
sudo -u postgres psql << 'EOF'
CREATE DATABASE grafana;
CREATE USER grafana WITH PASSWORD 'grafana_password';
GRANT ALL PRIVILEGES ON DATABASE grafana TO grafana;
EOF

# 重启Grafana服务
systemctl restart grafana-server

# 检查Grafana状态
systemctl status grafana-server
```

### 8.3 系统监控指标导出器

#### 安装Node Exporter（系统指标）：
```bash
# 下载Node Exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz
tar -xzf node_exporter-1.3.1.linux-amd64.tar.gz

# 复制到系统目录
sudo cp node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/

# 创建系统服务
cat > /etc/systemd/system/node-exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=root
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100

[Install]
WantedBy=multi-user.target
EOF

# 启动Node Exporter
systemctl daemon-reload
systemctl enable node-exporter.service
systemctl start node-exporter.service
```

#### 安装PostgreSQL Exporter：
```bash
# 下载PostgreSQL Exporter
cd /tmp
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.11.1/postgres_exporter-0.11.1.linux-amd64.tar.gz
tar -xzf postgres_exporter-0.11.1.linux-amd64.tar.gz

# 复制到系统目录
sudo cp postgres_exporter-0.11.1.linux-amd64/postgres_exporter /usr/local/bin/

# 创建PostgreSQL用户
sudo -u postgres psql << 'EOF'
CREATE USER prometheus WITH PASSWORD 'prometheus_password';
GRANT pg_monitor TO prometheus;
EOF

# 创建环境配置文件
cat > /etc/postgres_exporter.env << 'EOF'
DATA_SOURCE_NAME=postgresql://prometheus:prometheus_password@localhost:5432/ai_trading?sslmode=disable
EOF

# 创建系统服务
cat > /etc/systemd/system/postgres-exporter.service << 'EOF'
[Unit]
Description=PostgreSQL Exporter
After=network.target postgresql.service

[Service]
User=root
Type=simple
EnvironmentFile=/etc/postgres_exporter.env
ExecStart=/usr/local/bin/postgres_exporter --web.listen-address=:9187

[Install]
WantedBy=multi-user.target
EOF

# 启动PostgreSQL Exporter
systemctl daemon-reload
systemctl enable postgres-exporter.service
systemctl start postgres-exporter.service
```

---

## 9. 安全加固和性能优化

### 9.1 系统安全加固

#### SSH安全配置：
```bash
# 备份SSH配置
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# 编辑SSH配置
vim /etc/ssh/sshd_config
```

**SSH安全配置建议：**
```ini
# 修改SSH端口
Port 2222

# 禁用root登录
PermitRootLogin no

# 禁用密码认证，仅允许密钥认证
PasswordAuthentication no
PubkeyAuthentication yes

# 禁用空密码
PermitEmptyPasswords no

# 限制登录用户
AllowUsers www trader

# 设置登录超时
ClientAliveInterval 300
ClientAliveCountMax 2

# 禁用不安全的认证方式
ChallengeResponseAuthentication no
GSSAPIAuthentication no
UsePAM no
X11Forwarding no
```

```bash
# 重启SSH服务
systemctl restart sshd

# 更新防火墙规则，开放新的SSH端口
ufw allow 2222/tcp
ufw delete allow 22/tcp
ufw reload
```

#### 系统内核参数优化：
```bash
# 创建内核参数配置文件
cat > /etc/sysctl.d/99-ai-trading.conf << 'EOF'
# 网络安全参数
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# 防止SYN洪水攻击
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# 防止IP欺骗
net.ipv4.conf.all.arp_ignore = 1
net.ipv4.conf.all.arp_announce = 2

# 文件描述符限制
fs.file-max = 65536
net.core.somaxconn = 65535

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 网络连接优化
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
EOF

# 应用内核参数
sysctl -p /etc/sysctl.d/99-ai-trading.conf
```

#### 文件权限加固：
```bash
# 设置应用目录权限
chmod -R 755 /www/wwwroot/ai-trading
chmod -R 644 /www/wwwroot/ai-trading/*.py
chmod -R 644 /www/wwwroot/ai-trading/*.js
chmod -R 600 /www/wwwroot/ai-trading/.env
chmod -R 755 /www/wwwroot/ai-trading/scripts/*.sh

# 设置日志目录权限
mkdir -p /var/log/ai-trading
chown www:www /var/log/ai-trading
chmod 750 /var/log/ai-trading

# 创建用户限制配置
cat > /etc/security/limits.d/99-ai-trading.conf << 'EOF'
www soft nofile 65536
www hard nofile 65536
www soft nproc 32768
www hard nproc 32768
EOF
```

### 9.2 应用安全配置

#### 配置防火墙规则（更严格）：
```bash
# 清空现有规则
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# 设置默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许SSH（新端口）
iptables -A INPUT -p tcp --dport 2222 -j ACCEPT

# 允许HTTP和HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许宝塔面板（限制IP）
iptables -A INPUT -p tcp --dport 8888 -s YOUR_HOME_IP -j ACCEPT

# 允许应用服务（仅本地）
iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -s 127.0.0.1 -j ACCEPT

# 允许监控服务（仅本地）
iptables -A INPUT -p tcp --dport 9090 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3001 -s 127.0.0.1 -j ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4

# 安装iptables-persistent实现开机自动加载
apt install iptables-persistent -y
```

#### 配置fail2ban防止暴力破解：
```bash
# 安装fail2ban
apt install fail2ban -y

# 创建fail2ban配置
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
bantime = 600
EOF

# 启动fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 查看fail2ban状态
fail2ban-client status
```

### 9.3 性能优化配置

#### PostgreSQL性能调优：
```bash
# 编辑PostgreSQL配置
vim /etc/postgresql/13/main/postgresql.conf
```

**性能优化参数：**
```ini
# 内存配置（根据实际内存调整）
shared_buffers = 2GB                    # 25% of RAM
effective_cache_size = 6GB              # 75% of RAM
work_mem = 256MB                        # Per connection sort memory
maintenance_work_mem = 1GB              # Maintenance operations memory
autovacuum_work_mem = 256MB              # Autovacuum memory

# 连接配置
max_connections = 200
max_prepared_transactions = 200
shared_preload_libraries = 'pg_stat_statements'

# WAL配置
wal_buffers = 64MB
checkpoint_completion_target = 0.9
wal_writer_delay = 200ms

# 查询规划器
random_page_cost = 1.1                  # SSD优化
effective_io_concurrency = 200           # SSD并发

# 日志配置
log_min_duration_statement = 1000        # Log slow queries
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

#### Redis性能调优：
```bash
# 编辑Redis配置
vim /etc/redis/redis.conf
```

**性能优化参数：**
```ini
# 内存配置
maxmemory 2GB
maxmemory-policy allkeys-lru
maxmemory-samples 10

# 持久化配置
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes

# 网络配置
tcp-keepalive 300
timeout 0

# 客户端配置
maxclients 10000
tcp-backlog 511

# 安全配置
requirepass your_redis_password_123
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

#### Nginx性能调优：
```bash
# 编辑Nginx主配置
vim /etc/nginx/nginx.conf
```

**性能优化参数：**
```nginx
# 工作进程
worker_processes auto;
worker_rlimit_nofile 65535;

# 事件模块
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

# HTTP模块
http {
    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # 缓冲区配置
    client_body_buffer_size 128k;
    client_max_body_size 100m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # 超时配置
    client_body_timeout 60;
    client_header_timeout 60;
    send_timeout 60;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;
    
    # 文件缓存
    open_file_cache max=65536 inactive=60s;
    open_file_cache_valid 80s;
    open_file_cache_min_uses 1;
    open_file_cache_errors on;
}
```

---

## 10. 测试验证和故障排除

### 10.1 系统功能测试

#### 创建系统测试脚本：
```bash
# 创建综合测试脚本
cat > /www/wwwroot/ai-trading/scripts/system_test.sh << 'EOF'
#!/bin/bash
# AI交易系统综合测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试结果统计
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -e "${BLUE}[TEST]${NC} $test_name..."
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 详细测试函数
run_test_detail() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -e "${BLUE}[TEST]${NC} $test_name..."
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}=== AI交易系统综合测试 ===${NC}"

# 1. 基础服务测试
echo -e "\n${YELLOW}📦 基础服务测试${NC}"

run_test "PostgreSQL服务状态" "systemctl is-active postgresql"
run_test "Redis服务状态" "systemctl is-active redis-server"
run_test "Nginx服务状态" "systemctl is-active nginx"
run_test "Prometheus服务状态" "systemctl is-active prometheus"
run_test "Grafana服务状态" "systemctl is-active grafana-server"

# 2. 端口连通性测试
echo -e "\n${YELLOW}🔌 端口连通性测试${NC}"

run_test "PostgreSQL端口(5432)" "nc -z localhost 5432"
run_test "Redis端口(6379)" "nc -z localhost 6379"
run_test "HTTP端口(80)" "nc -z localhost 80"
run_test "HTTPS端口(443)" "nc -z localhost 443"
run_test "API端口(8000)" "nc -z localhost 8000"
run_test "Prometheus端口(9090)" "nc -z localhost 9090"
run_test "Grafana端口(3001)" "nc -z localhost 3001"

# 3. 数据库连接测试
echo -e "\n${YELLOW}🗄️ 数据库连接测试${NC}"

run_test_detail "PostgreSQL连接测试" "sudo -u postgres psql -d ai_trading -c 'SELECT 1;'"
run_test_detail "数据库表检查" "sudo -u postgres psql -d ai_trading -c 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \"public\";'"

# 4. 应用服务测试
echo -e "\n${YELLOW}🚀 应用服务测试${NC}"

run_test "PM2进程检查" "pm2 list | grep -q 'ai-trading'"
run_test_detail "API健康检查" "curl -s http://localhost:8000/health"

# 5. Web服务测试
echo -e "\n${YELLOW}🌐 Web服务测试${NC}"

run_test_detail "HTTP响应测试" "curl -I http://localhost/ -s -o /dev/null -w '%{http_code}' | grep -q '200'"
run_test_detail "HTTPS响应测试" "curl -I https://localhost/ -s -o /dev/null -w '%{http_code}' -k | grep -q '200'"

# 6. 监控服务测试
echo -e "\n${YELLOW}📊 监控服务测试${NC}"

run_test_detail "Prometheus指标检查" "curl -s http://localhost:9090/metrics | head -1"
run_test_detail "Grafana登录检查" "curl -s -X POST http://localhost:3001/login -H 'Content-Type: application/json' -d '{\"user\":\"admin\",\"password\":\"your_secure_password_123\"}' | grep -q 'grafana_session'"

# 7. 文件权限测试
echo -e "\n${YELLOW}🔒 文件权限测试${NC}"

run_test "应用目录权限" "test -r /www/wwwroot/ai-trading/.env"
run_test "日志目录权限" "test -w /www/wwwroot/ai-trading/logs"
run_test "上传目录权限" "test -w /www/wwwroot/ai-trading/uploads"

# 8. 系统资源测试
echo -e "\n${YELLOW}💻 系统资源测试${NC}"

MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | sed 's/%//')

run_test "内存使用检查" "[ $MEMORY_USAGE -lt 90 ]"
run_test "磁盘使用检查" "[ $DISK_USAGE -lt 90 ]"

# 测试结果汇总
echo -e "\n${BLUE}=== 测试结果汇总 ===${NC}"
echo -e "总测试数: ${YELLOW}$TESTS_TOTAL${NC}"
echo -e "通过: ${GREEN}$TESTS_PASSED${NC}"
echo -e "失败: ${RED}$TESTS_FAILED${NC}"

SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
echo -e "成功率: ${YELLOW}$SUCCESS_RATE%${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 所有测试通过！系统部署成功！${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️ 有 $TESTS_FAILED 个测试失败，请检查相关配置${NC}"
    exit 1
fi
EOF

# 设置执行权限
chmod +x /www/wwwroot/ai-trading/scripts/system_test.sh

# 运行系统测试
/www/wwwroot/ai-trading/scripts/system_test.sh
```

### 10.2 API功能测试

#### 创建API测试脚本：
```bash
# 创建API测试脚本
cat > /www/wwwroot/ai-trading/scripts/api_test.sh << 'EOF'
#!/bin/bash
# API接口测试脚本

API_BASE="http://localhost:8000/api/v1"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== API接口测试 ===${NC}"

# 1. 健康检查
echo -e "\n${YELLOW}🔍 健康检查${NC}"
response=$(curl -s -w "%{http_code}" "$API_BASE/../health")
http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅${NC} 健康检查 - $http_code"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
else
    echo -e "${RED}❌${NC} 健康检查失败 - $http_code"
fi

# 2. 获取交易所列表
echo -e "\n${YELLOW}🏦 交易所列表${NC}"
response=$(curl -s -w "%{http_code}" "$API_BASE/exchanges")
http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅${NC} 获取交易所列表 - $http_code"
    echo "$response_body" | jq '.' 2>/dev/null | head -10 || echo "$response_body"
else
    echo -e "${RED}❌${NC} 获取交易所列表失败 - $http_code"
fi

# 3. 获取交易对列表
echo -e "\n${YELLOW}📊 交易对列表${NC}"
response=$(curl -s -w "%{http_code}" "$API_BASE/symbols")
http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅${NC} 获取交易对列表 - $http_code"
    echo "$response_body" | jq '.data[:3]' 2>/dev/null || echo "$response_body"
else
    echo -e "${RED}❌${NC} 获取交易对列表失败 - $http_code"
fi

# 4. 获取策略列表
echo -e "\n${YELLOW}🧠 策略列表${NC}"
response=$(curl -s -w "%{http_code}" "$API_BASE/strategies")
http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅${NC} 获取策略列表 - $http_code"
    echo "$response_body" | jq '.' 2>/dev/null | head -10 || echo "$response_body"
else
    echo -e "${RED}❌${NC} 获取策略列表失败 - $http_code"
fi

# 5. 系统状态检查
echo -e "\n${YELLOW}📈 系统状态${NC}"
response=$(curl -s -w "%{http_code}" "$API_BASE/system/status")
http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅${NC} 系统状态 - $http_code"
    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
else
    echo -e "${RED}❌${NC} 系统状态检查失败 - $http_code"
fi

echo -e "\n${BLUE}=== API测试完成 ===${NC}"
EOF

# 设置执行权限
chmod +x /www/wwwroot/ai-trading/scripts/api_test.sh

# 运行API测试
/www/wwwroot/ai-trading/scripts/api_test.sh
```

### 10.3 故障排除指南

#### 常见问题和解决方案：

**问题1：服务无法启动**
```bash
# 查看服务状态
systemctl status postgresql redis-server nginx

# 查看详细错误日志
journalctl -u postgresql -f
journalctl -u redis-server -f
journalctl -u nginx -f

# 检查端口占用
netstat -tlnp | grep -E ':(80|443|5432|6379|8000)'
```

**问题2：数据库连接失败**
```bash
# 检查PostgreSQL配置
sudo -u postgres psql -c "SHOW listen_addresses;"
sudo -u postgres psql -c "SHOW port;"

# 检查连接权限
sudo -u postgres psql -c "SELECT usename, usecreatedb FROM pg_user WHERE usename = 'ai_trader';"

# 测试连接
psql -h localhost -U ai_trader -d ai_trading -c "SELECT 1;"
```

**问题3：Nginx配置错误**
```bash
# 测试Nginx配置
nginx -t

# 查看错误日志
tail -f /var/log/nginx/error.log

# 重载配置
nginx -s reload
```

**问题4：PM2进程异常**
```bash
# 查看PM2状态
pm2 status
pm2 logs

# 重启特定进程
pm2 restart ai-trading-api

# 删除并重新启动
pm2 delete ai-trading-api
pm2 start ecosystem.config.js
```

**问题5：SSL证书问题**
```bash
# 检查证书有效期
openssl x509 -in /www/server/panel/vhost/cert/yourdomain.com/cert.pem -text -noout | grep "Not After"

# 手动续期
certbot renew --dry-run
certbot renew

# 检查Nginx SSL配置
nginx -t | grep ssl
```

### 10.4 监控和日志配置

#### 配置日志轮转：
```bash
# 创建日志轮转配置
cat > /etc/logrotate.d/ai-trading << 'EOF'
/www/wwwroot/ai-trading/logs/app/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 www www
}

/var/log/ai-trading/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 www www
}
EOF

# 测试日志轮转
logrotate -f /etc/logrotate.d/ai-trading
```

#### 配置系统备份：
```bash
# 创建备份脚本
cat > /www/wwwroot/ai-trading/scripts/backup.sh << 'EOF'
#!/bin/bash
# 系统备份脚本

BACKUP_DIR="/backup/ai-trading"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "开始备份..."

# 数据库备份
echo "备份数据库..."
sudo -u postgres pg_dump ai_trading | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"

# 配置文件备份
echo "备份配置文件..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /www/wwwroot/ai-trading/.env \
    /www/wwwroot/ai-trading/ecosystem.config.js \
    /etc/nginx/sites-available/yourdomain.com \
    /www/wwwroot/ai-trading/deploy/

# 删除7天前的备份
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR"
EOF

# 设置执行权限
chmod +x /www/wwwroot/ai-trading/scripts/backup.sh

# 添加定时任务
crontab -e
# 添加：0 2 * * * /www/wwwroot/ai-trading/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🎉 部署完成总结

恭喜！您已经成功完成了AI量化交易系统在腾讯云宝塔面板上的完整部署。

### 📋 部署清单确认：

- ✅ **服务器环境配置** - 腾讯云CVM、防火墙、安全组
- ✅ **宝塔面板安装** - 面板配置、SSL、安全设置
- ✅ **基础软件安装** - Nginx、PostgreSQL、Redis、Python
- ✅ **项目部署** - 文件上传、环境配置、依赖安装
- ✅ **数据库配置** - 初始化、用户权限、性能优化
- ✅ **应用服务配置** - PM2、systemd、启动脚本
- ✅ **反向代理配置** - Nginx、SSL证书、WebSocket支持
- ✅ **监控系统配置** - Prometheus、Grafana、指标收集
- ✅ **安全加固** - SSH、防火墙、fail2ban、权限设置
- ✅ **性能优化** - 数据库、缓存、Web服务器优化
- ✅ **测试验证** - 功能测试、API测试、故障排除

### 🚀 系统访问地址：

- **主应用**: `https://yourdomain.com`
- **API文档**: `https://yourdomain.com/docs`
- **Grafana监控**: `https://yourdomain.com/grafana` (admin/your_secure_password_123)
- **Prometheus**: `https://yourdomain.com/prometheus` (需要认证)
- **宝塔面板**: `http://YOUR_SERVER_IP:8888`

### 🔧 重要文件路径：

- **应用根目录**: `/www/wwwroot/ai-trading`
- **环境配置**: `/www/wwwroot/ai-trading/.env`
- **PM2配置**: `/www/wwwroot/ai-trading/ecosystem.config.js`
- **Nginx配置**: `/etc/nginx/sites-available/yourdomain.com`
- **日志目录**: `/www/wwwroot/ai-trading/logs/`
- **备份目录**: `/backup/ai-trading/`

### 📞 常用管理命令：

```bash
# 查看服务状态
systemctl status ai-trading
pm2 status

# 重启应用
systemctl restart ai-trading
pm2 restart all

# 查看日志
pm2 logs
tail -f /www/wwwroot/ai-trading/logs/app/api-error.log

# 系统测试
/www/wwwroot/ai-trading/scripts/system_test.sh

# API测试
/www/wwwroot/ai-trading/scripts/api_test.sh
```

### ⚠️ 重要注意事项：

1. **定期备份** - 系统已配置自动备份，请定期检查备份文件
2. **监控告警** - 配置Grafana告警规则，及时收到系统异常通知
3. **安全更新** - 定期更新系统软件包和安全补丁
4. **证书续期** - SSL证书已配置自动续期，但仍需定期检查
5. **资源监控** - 注意CPU、内存、磁盘使用情况，必要时升级服务器配置

### 📞 技术支持：

如果在部署过程中遇到问题，可以：
1. 查看相关日志文件定位问题
2. 运行系统测试脚本检查配置
3. 查看本指南的故障排除部分
4. 联系技术支持获取帮助

祝您的AI量化交易系统运行顺利！🚀