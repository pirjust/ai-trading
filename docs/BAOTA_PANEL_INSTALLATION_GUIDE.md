# 宝塔面板完整安装文档

## 📋 目录
1. [服务器准备](#服务器准备)
2. [宝塔面板安装](#宝塔面板安装)
3. [运行环境安装](#运行环境安装)
4. [数据库环境安装](#数据库环境安装)
5. [Python环境配置](#python环境配置)
6. [系统依赖安装](#系统依赖安装)
7. [安全配置](#安全配置)
8. [验证安装](#验证安装)

---

## 🚀 服务器准备

### 1.1 服务器要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 存储 | 50GB SSD | 100GB SSD |
| 带宽 | 5Mbps | 10Mbps |

### 1.2 初始化服务器

```bash
# 1. 更新系统包
sudo apt update && sudo apt upgrade -y

# 2. 设置时区
sudo timedatectl set-timezone Asia/Shanghai

# 3. 配置主机名
sudo hostnamectl set-hostname ai-trading-server

# 4. 安装基础工具
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 5. 清理系统
sudo apt autoremove -y
sudo apt autoclean
```

### 1.3 配置防火墙

```bash
# 1. 安装UFW
sudo apt install -y ufw

# 2. 配置默认规则
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 3. 允许必要端口
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 8888/tcp   # 宝塔面板（安装后可修改）
sudo ufw allow 3306/tcp   # MySQL（如需要）
sudo ufw allow 5432/tcp   # PostgreSQL
sudo ufw allow 6379/tcp   # Redis
sudo ufw allow 8000/tcp   # API服务
sudo ufw allow 5000/tcp   # 监控服务

# 4. 启用防火墙
sudo ufw enable

# 5. 检查状态
sudo ufw status verbose
```

---

## 🛠️ 宝塔面板安装

### 2.1 安装宝塔面板

```bash
# 1. 下载宝塔面板安装脚本
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh

# 2. 设置执行权限
sudo chmod +x install.sh

# 3. 执行安装（使用Ubuntu官方源）
sudo bash install.sh ed8484bec

# 4. 安装完成后会显示：
#面板地址: http://your-server-ip:8888
#用户名: random_username
#密码: random_password

# 5. 记录登录信息（重要！）
echo "宝塔面板信息:" > ~/baota_info.txt
echo "面板地址: http://your-server-ip:8888" >> ~/baota_info.txt
echo "用户名: your_username" >> ~/baota_info.txt
echo "密码: your_password" >> ~/baota_info.txt
```

### 2.2 首次登录配置

```bash
# 1. 访问宝塔面板
# 浏览器打开: http://your-server-ip:8888

# 2. 绑定腾讯云账号（可选）
# 3. 推荐安装套件：LNMP（Linux + Nginx + MySQL + PHP）

# 4. 建议安装的软件版本：
# - Nginx: 1.20+
# - MySQL: 8.0+
# - PHP: 7.4/8.1
# - phpMyAdmin: 最新版本
# - Pure-Ftpd: 最新版本
```

### 2.3 宝塔面板安全配置

```bash
# 1. 修改默认端口（在面板设置中）
# 面板 → 面板设置 → 修改面板端口（如：9999）

# 2. 修改用户名和密码
# 面板 → 面板设置 → 修改面板用户和密码

# 3. 绑定域名
# 面板 → 面板设置 → 绑定域名

# 4. 开启SSL
# 面板 → 面板设置 → 面板SSL → 开启

# 5. 启用基本认证
# 面板 → 面板设置 → 认证访问 → 开启

# 6. 更新防火墙规则（如果修改了端口）
sudo ufw delete allow 8888/tcp
sudo ufw allow 9999/tcp  # 新的宝塔端口
```

---

## 🔧 运行环境安装

### 3.1 在宝塔面板中安装软件

1. **登录宝塔面板**
2. **进入软件商店**
3. **安装以下软件**：

#### 3.1.1 Web服务器
- **Nginx**: 版本 1.20+
- **Apache**: 版本 2.4+（可选）

#### 3.1.2 数据库
- **MySQL**: 版本 8.0+
- **PostgreSQL**: 版本 13+
- **Redis**: 版本 6.0+
- **MongoDB**: 版本 5.0+（可选）

#### 3.1.3 编程语言
- **PHP**: 版本 7.4 和 8.1
- **Python项目管理器**: 最新版本
- **Node.js版本管理器**: 最新版本

#### 3.1.4 工具软件
- **PM2管理器**: 最新版本
- **Docker管理器**: 最新版本
- **文件管理器**: 最新版本
- **Supervisor管理器**: 最新版本

### 3.2 编译安装部分组件（如需要）

```bash
# 1. 安装编译工具
sudo apt install -y build-essential cmake

# 2. 安装Python开发环境
sudo apt install -y python3-dev python3-pip python3-venv

# 3. 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 4. 验证安装
node --version
npm --version
```

---

## 🗄️ 数据库环境安装

### 4.1 PostgreSQL安装和配置

#### 4.1.1 通过宝塔面板安装

1. **软件商店 → 搜索 "PostgreSQL"**
2. **选择版本 13+ → 安装**
3. **等待安装完成**

#### 4.1.2 手动安装（如需要）

```bash
# 1. 添加PostgreSQL官方源
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# 2. 安装PostgreSQL
sudo apt update
sudo apt install -y postgresql-13 postgresql-contrib

# 3. 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. 修改默认密码
sudo -u postgres psql
\password postgres  # 设置新密码
\q

# 5. 配置远程连接（如需要）
sudo vim /etc/postgresql/13/main/postgresql.conf
# 修改: listen_addresses = '*'

sudo vim /etc/postgresql/13/main/pg_hba.conf
# 添加: host all all 0.0.0.0/0 md5

# 6. 重启服务
sudo systemctl restart postgresql
```

### 4.2 Redis安装和配置

#### 4.2.1 通过宝塔面板安装

1. **软件商店 → 搜索 "Redis"**
2. **选择版本 6.0+ → 安装**
3. **配置内存限制和密码**

#### 4.2.2 手动安装（如需要）

```bash
# 1. 安装Redis
sudo apt install -y redis-server

# 2. 配置Redis
sudo vim /etc/redis/redis.conf

# 关键配置项：
# bind 127.0.0.1 0.0.0.0
# requirepass your_redis_password
# maxmemory 2gb
# maxmemory-policy allkeys-lru

# 3. 重启Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 4. 测试连接
redis-cli
AUTH your_redis_password
PING
```

### 4.3 MySQL安装（可选，如使用腾讯云RDS可跳过）

#### 4.3.1 通过宝塔面板安装

1. **软件商店 → 搜索 "MySQL"**
2. **选择版本 8.0+ → 安装**
3. **设置root密码**

#### 4.3.2 配置MySQL

```bash
# 1. 安全配置
sudo mysql_secure_installation

# 2. 创建数据库和用户
mysql -u root -p
CREATE DATABASE ai_trading;
CREATE USER 'ai_trader'@'%' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON ai_trading.* TO 'ai_trader'@'%';
FLUSH PRIVILEGES;
EXIT;
```

---

## 🐍 Python环境配置

### 5.1 安装Python版本

```bash
# 1. 安装Python 3.9
sudo apt install -y python3.9 python3.9-dev python3.9-venv python3.9-distutils

# 2. 安装Python包管理工具
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.9 get-pip.py

# 3. 安装pip3
sudo apt install -y python3-pip

# 4. 验证安装
python3.9 --version
pip3 --version
```

### 5.2 配置虚拟环境

```bash
# 1. 创建虚拟环境目录
sudo mkdir -p /www/envs
sudo chown -R www-data:www-data /www/envs

# 2. 创建AI交易系统虚拟环境
sudo /usr/bin/python3.9 -m venv /www/envs/ai-trading

# 3. 设置权限
sudo chown -R www-data:www-data /www/envs/ai-trading

# 4. 激活虚拟环境并升级pip
sudo -u www-data bash -c "source /www/envs/ai-trading/bin/activate && pip install --upgrade pip setuptools wheel"

# 5. 测试虚拟环境
sudo -u www-data bash -c "source /www/envs/ai-trading/bin/activate && python --version && pip --version"
```

### 5.3 安装Python系统依赖

```bash
# 1. 安装系统开发库
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
    gfortran \
    libsndfile1-dev

# 2. 安装数据库客户端
sudo apt install -y postgresql-client redis-tools

# 3. 安装其他工具
sudo apt install -y htop iotop nethogs tree jq
```

### 5.4 安装常用Python包

```bash
# 1. 激活虚拟环境
source /www/envs/ai-trading/bin/activate

# 2. 安装基础包
pip install numpy pandas scipy matplotlib seaborn

# 3. 安装机器学习包
pip install scikit-learn tensorflow torch torchvision

# 4. 安装Web框架
pip install fastapi uvicorn gunicorn python-multipart

# 5. 安装数据库包
pip install psycopg2-binary redis sqlalchemy alembic

# 6. 安装数据采集包
pip install requests websocket-client ccxt beautifulsoup4

# 7. 安装监控包
pip install prometheus-client psutil

# 8. 安装其他工具包
pip install python-dotenv click tqdm rich
```

---

## 📦 系统依赖安装

### 6.1 安装编译环境

```bash
# 1. 安装编译工具链
sudo apt install -y build-essential cmake gcc g++ make

# 2. 安装版本控制
sudo apt install -y git subversion mercurial

# 3. 安装压缩工具
sudo apt install -y zip unzip p7zip-full rar unrar

# 4. 安装文本编辑器
sudo apt install -y vim nano emacs
```

### 6.2 安装网络工具

```bash
# 1. 网络诊断工具
sudo apt install -y net-tools iproute2 traceroute mtr

# 2. DNS工具
sudo apt install -y dig dnsutils nslookup

# 3. 网络监控工具
sudo apt install -y nethogs iftop iptraf-ng

# 4. 下载工具
sudo apt install -y wget curl axel
```

### 6.3 安装系统监控工具

```bash
# 1. 系统监控
sudo apt install -y htop iotop glances

# 2. 进程管理
sudo apt install -y supervisor

# 3. 日志管理
sudo apt install -y logrotate rsyslog

# 4. 性能分析
sudo apt install -y sysstat powertop
```

### 6.4 安装安全工具

```bash
# 1. 防火墙增强
sudo apt install -y fail2ban ufw

# 2. 扫描工具
sudo apt install -y nmap zenmap

# 3. 入侵检测
sudo apt install -y rkhunter chkrootkit
```

---

## 🔒 安全配置

### 7.1 SSH安全配置

```bash
# 1. 备份SSH配置
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# 2. 编辑SSH配置
sudo vim /etc/ssh/sshd_config

# 修改以下配置：
Port 2222                    # 修改默认端口
PermitRootLogin no           # 禁止root登录
PasswordAuthentication no     # 禁用密码登录
PubkeyAuthentication yes      # 启用密钥登录
MaxAuthTries 3               # 最大尝试次数
ClientAliveInterval 300      # 客户端存活间隔
ClientAliveCountMax 2        # 最大存活次数

# 3. 重启SSH服务
sudo systemctl restart ssh

# 4. 更新防火墙规则
sudo ufw delete allow 22/tcp
sudo ufw allow 2222/tcp
```

### 7.2 生成SSH密钥

```bash
# 1. 生成密钥对（在本地机器）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 2. 复制公钥到服务器
ssh-copy-id -p 2222 user@your-server-ip

# 3. 测试密钥登录
ssh -p 2222 user@your-server-ip
```

### 7.3 系统安全加固

```bash
# 1. 创建普通用户
sudo adduser ai_trader
sudo usermod -aG sudo ai_trader

# 2. 配置sudo免密码（可选）
sudo visudo
# 添加: ai_trader ALL=(ALL) NOPASSWD:ALL

# 3. 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon

# 4. 安装fail2ban
sudo apt install -y fail2ban

# 5. 配置fail2ban
sudo vim /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
# 6. 启动fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## ✅ 验证安装

### 8.1 验证宝塔面板

```bash
# 1. 检查宝塔面板状态
sudo systemctl status bt

# 2. 检查面板端口
sudo netstat -tlnp | grep 8888

# 3. 访问面板
# 浏览器打开: http://your-server-ip:8888
```

### 8.2 验证Web服务

```bash
# 1. 检查Nginx状态
sudo systemctl status nginx
sudo nginx -t

# 2. 检查PHP状态
sudo systemctl status php7.4-fpm
sudo systemctl status php8.1-fpm

# 3. 创建测试页面
echo "<?php phpinfo(); ?>" | sudo tee /www/wwwroot/default/info.php

# 4. 访问测试页面
# 浏览器打开: http://your-server-ip/info.php
```

### 8.3 验证数据库服务

```bash
# 1. 检查PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# 2. 检查Redis
sudo systemctl status redis-server
redis-cli ping

# 3. 检查MySQL（如安装）
sudo systemctl status mysql
mysql -u root -p -e "SELECT version();"
```

### 8.4 验证Python环境

```bash
# 1. 检查Python版本
python3.9 --version

# 2. 检查虚拟环境
source /www/envs/ai-trading/bin/activate
python --version
pip --version

# 3. 测试包导入
python -c "import numpy, pandas, fastapi; print('All packages imported successfully')"

# 4. 检查系统依赖
python -c "import psycopg2, redis; print('Database drivers installed')"
```

### 8.5 系统整体检查

```bash
# 1. 检查系统资源
free -h
df -h
htop

# 2. 检查网络连接
ping 8.8.8.8
curl -I https://www.baidu.com

# 3. 检查防火墙状态
sudo ufw status verbose

# 4. 检查监听端口
sudo netstat -tlnp

# 5. 检查系统日志
sudo journalctl -xe --no-pager
```

---

## 📋 安装完成后检查清单

### 9.1 基础环境检查

- [ ] 服务器时间同步正确
- [ ] 防火墙规则配置完成
- [ ] SSH密钥登录配置完成
- [ ] 系统更新到最新版本

### 9.2 宝塔面板检查

- [ ] 宝塔面板正常访问
- [ ] 面板端口和密码已修改
- [ ] 必要软件已安装
- [ ] SSL证书已配置

### 9.3 运行环境检查

- [ ] Nginx/Apache正常运行
- [ ] PHP环境配置完成
- [ ] 数据库服务正常
- [ ] Python虚拟环境创建完成

### 9.4 安全配置检查

- [ ] Fail2ban已启用
- [ ] SSH安全配置完成
- [ ] 用户权限配置正确
- [ ] 系统日志正常记录

---

## 🚨 常见问题和解决方案

### 10.1 宝塔面板无法访问

```bash
# 1. 检查防火墙
sudo ufw status

# 2. 检查端口监听
sudo netstat -tlnp | grep 8888

# 3. 重启宝塔面板
sudo /etc/init.d/bt restart

# 4. 检查面板日志
sudo tail -f /www/server/panel/logs/error.log
```

### 10.2 数据库连接失败

```bash
# 1. 检查数据库状态
sudo systemctl status postgresql

# 2. 检查配置文件
sudo vim /etc/postgresql/13/main/postgresql.conf

# 3. 测试连接
psql -h localhost -U postgres -d postgres
```

### 10.3 Python包安装失败

```bash
# 1. 更新pip
pip install --upgrade pip

# 2. 安装编译依赖
sudo apt install -y build-essential

# 3. 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

---

## 📞 技术支持

如果在安装过程中遇到问题：

1. **查看日志文件**
   - 宝塔面板日志: `/www/server/panel/logs/`
   - 系统日志: `/var/log/`
   - 应用日志: `/var/log/syslog`

2. **重启相关服务**
   ```bash
   sudo systemctl restart bt          # 重启宝塔面板
   sudo systemctl restart nginx      # 重启Nginx
   sudo systemctl restart postgresql # 重启PostgreSQL
   ```

3. **检查系统状态**
   ```bash
   sudo systemctl status service_name
   sudo journalctl -xe --no-pager
   ```

---

*最后更新时间：2024年11月*
*文档版本：v1.0*