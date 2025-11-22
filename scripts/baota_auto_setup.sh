#!/bin/bash
# 宝塔面板自动配置脚本
# 在腾讯云Ubuntu系统上自动配置宝塔面板和AI交易系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "请使用root权限运行此脚本"
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS_NAME=$NAME
        OS_VERSION=$VERSION_ID
    else
        OS_NAME=$(uname -s)
        OS_VERSION=$(uname -r)
    fi
    
    log "检测到操作系统: $OS_NAME $OS_VERSION"
    
    case $OS_NAME in
        *Ubuntu*)
            OS_TYPE="ubuntu"
            ;;
        *Debian*)
            OS_TYPE="debian"
            ;;
        *CentOS*|*RedHat*)
            OS_TYPE="centos"
            ;;
        *)
            error "不支持的操作系统: $OS_NAME"
            ;;
    esac
}

# 安装宝塔面板
install_baota() {
    log "开始安装宝塔面板..."
    
    # 检查是否已安装
    if [[ -f "/etc/init.d/bt" ]]; then
        log "宝塔面板已安装"
        return 0
    fi
    
    case $OS_TYPE in
        "ubuntu"|"debian")
            wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
            bash install.sh ed8484bec
            ;;
        "centos")
            yum install -y wget
            wget -O install.sh https://download.bt.cn/install/install_6.0.sh
            bash install.sh
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        log "宝塔面板安装成功"
        
        # 保存面板信息
        SERVER_IP=$(hostname -I | awk '{print $1}')
        cat > /root/baota_info.txt << EOF
==========================================
宝塔面板安装信息
==========================================
面板地址: http://$SERVER_IP:8888
用户名: 安装脚本输出的用户名
密码: 安装脚本输出的密码

重要提示:
1. 首次登录后请立即修改用户名和密码
2. 建议修改默认端口为19999
3. 启用SSL加密访问
4. 设置IP访问限制
EOF
        
        cat /root/baota_info.txt
    else
        error "宝塔面板安装失败"
    fi
}

# 配置防火墙
setup_firewall() {
    log "配置防火墙..."
    
    case $OS_TYPE in
        "ubuntu"|"debian")
            apt install -y ufw
            ufw --force enable
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 8888/tcp
            ufw allow 19999/tcp
            ufw allow 5432/tcp
            ufw allow 6379/tcp
            ufw allow 8000/tcp
            ;;
        "centos")
            systemctl start firewalld
            systemctl enable firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-port=8888/tcp
            firewall-cmd --permanent --add-port=19999/tcp
            firewall-cmd --permanent --add-port=5432/tcp
            firewall-cmd --permanent --add-port=6379/tcp
            firewall-cmd --permanent --add-port=8000/tcp
            firewall-cmd --reload
            ;;
    esac
    
    log "防火墙配置完成"
}

# 安装系统依赖
install_system_dependencies() {
    log "安装系统依赖..."
    
    case $OS_TYPE in
        "ubuntu"|"debian")
            apt update
            apt install -y curl wget git vim htop unzip \
                software-properties-common apt-transport-https \
                ca-certificates gnupg lsb-release \
                build-essential cmake gcc g++ make \
                python3-dev python3-pip python3-venv \
                libpq-dev libssl-dev libffi-dev \
                libxml2-dev libxslt1-dev libjpeg-dev \
                libpng-dev libfreetype6-dev zlib1g-dev \
                libhdf5-dev libblas-dev liblapack-dev gfortran \
                postgresql-client redis-tools mysql-client \
                ufw fail2ban supervisor
            ;;
        "centos")
            yum update -y
            yum install -y curl wget git vim htop unzip \
                epel-release yum-utils \
                gcc gcc-c++ make cmake \
                python3 python3-pip python3-devel \
                postgresql-devel openssl-devel libffi-devel \
                libxml2-devel libxslt-devel libjpeg-turbo-devel \
                libpng-devel freetype-devel zlib-devel \
                hdf5-devel blas-devel lapack-devel gcc-gfortran \
                postgresql redis mysql \
                firewalld fail2ban supervisor
            ;;
    esac
}

# 创建Python虚拟环境
setup_python_environment() {
    log "设置Python虚拟环境..."
    
    VENV_PATH="/opt/ai-trading"
    
    # 创建虚拟环境
    python3 -m venv $VENV_PATH
    
    # 激活虚拟环境
    source $VENV_PATH/bin/activate
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
    
    # 安装基础依赖
    pip install psycopg2-binary redis fastapi uvicorn gunicorn \
        requests websocket-client ccxt pandas numpy \
        scikit-learn torch torchvision tensorflow \
        prometheus-client psutil
    
    log "Python虚拟环境设置完成"
}

# 配置宝塔面板软件
setup_baota_software() {
    log "配置宝塔面板软件..."
    
    # 宝塔面板API配置（需要面板API密钥）
    BT_PANEL="http://127.0.0.1:8888"
    BT_KEY="your_baota_api_key"  # 需要在宝塔面板中获取
    
    # 安装Nginx
    curl -k -s "$BT_PANEL/install?action=InstallApp" -d "type=nginx&version=1.22&setup=1" \
        -H "Authorization: $BT_KEY"
    
    # 安装PostgreSQL
    curl -k -s "$BT_PANEL/install?action=InstallApp" -d "type=postgresql&version=15&setup=1" \
        -H "Authorization: $BT_KEY"
    
    # 安装Redis
    curl -k -s "$BT_PANEL/install?action=InstallApp" -d "type=redis&version=7.0&setup=1" \
        -H "Authorization: $BT_KEY"
    
    # 安装Python项目管理器
    curl -k -s "$BT_PANEL/install?action=InstallApp" -d "type=python&version=1.9&setup=1" \
        -H "Authorization: $BT_KEY"
    
    sleep 30  # 等待安装完成
}

# 配置数据库
setup_database() {
    log "配置数据库..."
    
    # 启动PostgreSQL服务
    systemctl start postgresql
    systemctl enable postgresql
    
    # 创建数据库和用户
    sudo -u postgres psql -c "CREATE USER ai_trader WITH PASSWORD 'your_secure_password_123';"
    sudo -u postgres psql -c "CREATE DATABASE ai_trading OWNER ai_trader;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;"
    
    # 配置PostgreSQL远程访问
    PG_CONF="/etc/postgresql/15/main/postgresql.conf"
    if [[ -f $PG_CONF ]]; then
        sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" $PG_CONF
    fi
    
    # 配置访问权限
    PG_HBA="/etc/postgresql/15/main/pg_hba.conf"
    if [[ -f $PG_HBA ]]; then
        echo "host    all             all             0.0.0.0/0               md5" >> $PG_HBA
    fi
    
    # 重启PostgreSQL
    systemctl restart postgresql
    
    # 配置Redis
    REDIS_CONF="/etc/redis/redis.conf"
    if [[ -f $REDIS_CONF ]]; then
        sed -i "s/# requirepass foobared/requirepass your_redis_password_123/" $REDIS_CONF
        sed -i "s/bind 127.0.0.1/bind 0.0.0.0/" $REDIS_CONF
        systemctl restart redis
    fi
}

# 创建项目目录结构
create_project_structure() {
    log "创建项目目录结构..."
    
    PROJECT_PATH="/www/wwwroot/ai-trading"
    
    # 创建目录
    mkdir -p $PROJECT_PATH/{app,config,core,data,ai_engine,strategies,scripts,logs,frontend/dist}
    
    # 设置权限
    chown -R www:www $PROJECT_PATH
    chmod -R 755 $PROJECT_PATH
    
    # 创建日志目录
    mkdir -p $PROJECT_PATH/logs
    chmod 777 $PROJECT_PATH/logs
}

# 配置Nginx
setup_nginx() {
    log "配置Nginx..."
    
    NGINX_CONF="/www/server/panel/vhost/nginx/ai-trading.conf"
    
    cat > $NGINX_CONF << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root /www/wwwroot/ai-trading/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
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
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        root /www/wwwroot/ai-trading/frontend/dist;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    # 安全设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
NGINXEOF
    
    # 测试并重启Nginx
    nginx -t && nginx -s reload
}

# 配置Python项目管理器
setup_python_project() {
    log "配置Python项目管理器..."
    
    PROJECT_JSON="/www/server/panel/plugin/python/config.json"
    
    cat > /tmp/python_project.json << 'PYEOF'
{
    "name": "ai-trading-api",
    "path": "/www/wwwroot/ai-trading",
    "project_dir": "/www/wwwroot/ai-trading",
    "python_version": "3.9",
    "framework": "fastapi",
    "app_path": "app/main:app",
    "port": 8000,
    "host": "127.0.0.1",
    "workers": 4,
    "threads": 2,
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "timeout": 120,
    "preload_app": true,
    "environment": {
        "DATABASE_URL": "postgresql://ai_trader:your_secure_password_123@localhost:5432/ai_trading",
        "REDIS_URL": "redis://:your_redis_password_123@localhost:6379/0",
        "DEBUG": "False",
        "LOG_LEVEL": "INFO"
    }
}
PYEOF
    
    # 使用宝塔API创建项目
    BT_PANEL="http://127.0.0.1:8888"
    BT_KEY="your_baota_api_key"
    
    curl -k -s "$BT_PANEL/plugin?action=python&name=add_project" \
        -H "Content-Type: application/json" \
        -H "Authorization: $BT_KEY" \
        -d @/tmp/python_project.json
}

# 配置监控和日志
setup_monitoring() {
    log "配置监控和日志..."
    
    # 配置Supervisor
    cat > /etc/supervisor/conf.d/ai-trading.conf << 'SUPEOF'
[program:ai-trading-api]
command=/opt/ai-trading/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
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
SUPEOF
    
    # 重启Supervisor
    systemctl restart supervisor
    supervisorctl update
}

# 生成部署报告
generate_deployment_report() {
    log "生成部署报告..."
    
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > /root/deployment_report.txt << EOF
==========================================
AI量化交易系统部署报告
==========================================
部署时间: $(date)
服务器IP: $SERVER_IP
操作系统: $OS_NAME $OS_VERSION

✅ 已完成的配置：
- 宝塔面板安装和配置
- 防火墙配置
- 系统依赖安装
- Python虚拟环境
- 数据库配置 (PostgreSQL + Redis)
- Nginx反向代理
- 项目目录结构
- 监控和日志系统

📊 服务状态：
- 宝塔面板: http://$SERVER_IP:8888
- Web应用: http://$SERVER_IP
- API服务: http://$SERVER_IP:8000
- 数据库: PostgreSQL(5432), Redis(6379)

🔧 技术栈：
- 后端: Python 3.9 + FastAPI
- 数据库: PostgreSQL 15 + Redis 7
- Web服务器: Nginx 1.22
- 监控: Supervisor + 自定义监控

📋 下一步操作：
1. 登录宝塔面板完成最终配置
2. 上传AI交易系统代码到 /www/wwwroot/ai-trading
3. 配置API密钥和交易所认证
4. 测试系统功能
5. 配置SSL证书

🔐 安全建议：
1. 修改宝塔面板默认端口和密码
2. 配置SSL加密访问
3. 设置IP访问限制
4. 定期备份数据
5. 监控系统日志

📞 技术支持：
- 系统日志: /var/log/
- 应用日志: /www/wwwroot/ai-trading/logs/
- 宝塔日志: /www/server/panel/logs/
- 重启服务: systemctl restart service_name

EOF
    
    cat /root/deployment_report.txt
}

# 主函数
main() {
    log "开始AI量化交易系统宝塔面板自动配置..."
    
    check_root
    detect_os
    setup_firewall
    install_system_dependencies
    install_baota
    setup_python_environment
    setup_database
    create_project_structure
    setup_nginx
    setup_python_project
    setup_monitoring
    generate_deployment_report
    
    log "宝塔面板自动配置完成！"
    log "请查看 /root/deployment_report.txt 获取详细信息"
    
    SERVER_IP=$(hostname -I | awk '{print $1}')
    info "宝塔面板地址: http://$SERVER_IP:8888"
    info "Web应用地址: http://$SERVER_IP"
    info "API服务地址: http://$SERVER_IP:8000"
}

# 执行主函数
main "$@"