# AI量化交易系统部署指南

本文档提供AI量化交易系统的完整部署指南，包括本地开发环境、Docker容器化部署和云服务器部署。

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [本地部署](#本地部署)
- [Docker部署](#docker部署)
- [云服务器部署](#云服务器部署)
- [宝塔面板部署](#宝塔面板部署)
- [配置说明](#配置说明)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 环境要求

### 基础要求

- **操作系统**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+
- **Python**: 3.8+
- **Node.js**: 16+
- **内存**: 最低4GB，推荐8GB+
- **存储**: 最低10GB可用空间

### 数据库要求

- **PostgreSQL**: 12+
- **Redis**: 6+

### 可选组件

- **Docker**: 20+ (容器化部署)
- **Docker Compose**: 1.29+
- **Git**: 2.0+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/ai-trading.git
cd ai-trading
```

### 2. 一键启动

```bash
# 给启动脚本执行权限
chmod +x scripts/start_system.sh

# 启动系统（本地模式）
./scripts/start_system.sh

# 或使用Docker模式
./scripts/start_system.sh docker
```

### 3. 访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 本地部署

### 1. 环境准备

```bash
# 安装Python 3.8+
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# 安装Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs -y

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 安装Redis
sudo apt install redis-server -y
```

### 2. 数据库设置

```bash
# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE ai_trading;
CREATE USER ai_trader WITH PASSWORD 'your_secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
\q

# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

关键配置项：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_trading
DB_USER=ai_trader
DB_PASSWORD=your_secure_password_123

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_123

# 交易所API密钥
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
OKX_API_KEY=your_okx_api_key
OKX_API_SECRET=your_okx_api_secret
OKX_PASSPHRASE=your_okx_passphrase

# 应用配置
SECRET_KEY=your_jwt_secret_key_32_chars_long
DEBUG=false
APP_ENV=production
```

### 4. 安装依赖

```bash
# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装Node.js依赖
cd frontend
npm install
cd ..
```

### 5. 初始化数据库

```bash
# 运行数据库迁移
python -m alembic upgrade head

# 插入初始数据
python scripts/init_data.py
```

### 6. 启动服务

```bash
# 使用启动脚本
./scripts/start_system.sh

# 或手动启动
# 后端
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev
```

## Docker部署

### 1. 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置Docker环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑Docker配置
nano docker-compose.yml
```

### 3. 启动Docker服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. Docker Compose配置示例

```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:13
    container_name: ai_trading_postgres
    environment:
      POSTGRES_DB: ai_trading
      POSTGRES_USER: ai_trader
      POSTGRES_PASSWORD: your_secure_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:6-alpine
    container_name: ai_trading_redis
    command: redis-server --requirepass your_redis_password_123
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  # 后端API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai_trading_backend
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # 前端应用
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ai_trading_frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  # Prometheus监控
  prometheus:
    image: prom/prometheus:latest
    container_name: ai_trading_prometheus
    volumes:
      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  # Grafana仪表板
  grafana:
    image: grafana/grafana:latest
    container_name: ai_trading_grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./deploy/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

## 云服务器部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础软件
sudo apt install git curl wget -y

# 配置防火墙
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
sudo ufw allow 3000
sudo ufw --force enable
```

### 2. 安装运行环境

```bash
# 安装Docker（推荐方式）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重启以应用用户组更改
sudo reboot
```

### 3. 部署应用

```bash
# 克隆项目
git clone https://github.com/your-repo/ai-trading.git
cd ai-trading

# 配置环境变量
cp .env.example .env
nano .env

# 启动服务
docker-compose up -d

# 设置Nginx反向代理（可选）
sudo apt install nginx -y
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ai-trading
sudo ln -s /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 配置SSL证书

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 宝塔面板部署

### 1. 安装宝塔面板

```bash
# CentOS
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh

# Ubuntu/Debian
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
```

### 2. 配置环境

在宝塔面板中：

1. **软件商店** -> 安装：
   - Nginx 1.20+
   - PostgreSQL 13+
   - Redis 6+
   - Python 3.8+

2. **网站** -> 添加站点：
   - 域名：yourdomain.com
   - 根目录：/www/wwwroot/ai-trading/frontend/dist
   - PHP版本：纯静态

3. **数据库** -> 创建数据库：
   - 数据库名：ai_trading
   - 用户名：ai_trader
   - 密码：your_secure_password_123

### 3. 部署应用

```bash
# 上传项目文件到服务器
scp -r ./ai-trading root@yourserver:/www/wwwroot/

# 进入项目目录
cd /www/wwwroot/ai-trading

# 创建Python虚拟环境
/opt/python3.8/bin/python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行宝塔面板部署脚本
./scripts/bt_panel_deploy.sh
```

### 4. 配置反向代理

在宝塔面板 -> 网站 -> 设置 -> 反向代理：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## 配置说明

### 核心配置文件

1. **.env** - 环境变量配置
2. **core/config.py** - 系统配置类
3. **docker-compose.yml** - Docker服务配置
4. **deploy/nginx.conf** - Nginx配置
5. **deploy/prometheus.yml** - 监控配置

### 安全配置

1. **API密钥管理**
   - 使用强密码
   - 定期轮换密钥
   - 使用环境变量存储敏感信息

2. **网络安全**
   - 配置防火墙规则
   - 使用HTTPS
   - 限制数据库访问

3. **应用安全**
   - 启用CSRF保护
   - 配置CORS策略
   - 实施速率限制

### 性能优化

1. **数据库优化**
   ```sql
   -- PostgreSQL配置优化
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET work_mem = '4MB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   SELECT pg_reload_conf();
   ```

2. **Redis优化**
   ```conf
   # redis.conf
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   save 900 1
   save 300 10
   save 60 10000
   ```

3. **应用优化**
   - 启用Gzip压缩
   - 配置缓存策略
   - 使用连接池

## 监控和维护

### 1. 系统监控

访问监控面板：
- **Prometheus**: http://yourserver:9090
- **Grafana**: http://yourserver:3001 (admin/admin123)

### 2. 日志管理

```bash
# 查看应用日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 查看系统日志
sudo journalctl -u ai-trading -f
```

### 3. 备份策略

```bash
# 数据库备份
pg_dump ai_trading > backup_$(date +%Y%m%d).sql

# 配置文件备份
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env deploy/

# 自动备份脚本
crontab -e
# 添加：0 2 * * * /path/to/backup.sh
```

### 4. 更新部署

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
cd frontend && npm update && cd ..

# 重新构建
docker-compose build
docker-compose up -d
```

## 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep :8000
   sudo netstat -tlnp | grep :3000
   
   # 检查服务状态
   systemctl status postgresql
   systemctl status redis-server
   ```

2. **数据库连接失败**
   ```bash
   # 测试数据库连接
   psql -h localhost -U ai_trader -d ai_trading
   
   # 检查配置
   cat /var/lib/postgresql/data/postgresql.conf
   ```

3. **前端构建失败**
   ```bash
   # 清理缓存
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **内存不足**
   ```bash
   # 查看内存使用
   free -h
   htop
   
   # 调整Docker内存限制
   docker system prune -a
   ```

### 日志分析

1. **应用错误**
   - 检查 logs/error.log
   - 查看特定时间段日志
   - 使用grep过滤关键信息

2. **性能问题**
   - 分析慢查询日志
   - 监控CPU和内存使用
   - 检查网络延迟

3. **安全问题**
   - 监控登录失败尝试
   - 检查异常API调用
   - 分析访问日志模式

### 支持和帮助

- **文档**: https://docs.yourdomain.com
- **GitHub Issues**: https://github.com/your-repo/ai-trading/issues
- **邮件支持**: support@yourdomain.com
- **社区论坛**: https://community.yourdomain.com

---

**注意**: 本部署指南会随着系统更新而持续完善，建议定期查看最新版本的文档。