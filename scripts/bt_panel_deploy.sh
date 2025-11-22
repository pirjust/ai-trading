#!/bin/bash

# AI量化交易系统 - 宝塔面板一键部署脚本
# 适用环境：CentOS 7+/Ubuntu 18.04+，宝塔面板7.9.0+

echo "🚀 AI量化交易系统 - 宝塔面板部署脚本"
echo "========================================"

# 检查是否为root用户
if [ "$(id -u)" != "0" ]; then
    echo "❌ 请使用root用户运行此脚本"
    exit 1
fi

# 检查宝塔面板
if [ ! -d "/www/server/panel" ]; then
    echo "❌ 未检测到宝塔面板，请先安装宝塔面板"
    echo "安装命令："
    echo "CentOS: yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh"
    echo "Ubuntu: wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh"
    exit 1
fi

echo "✅ 检测到宝塔面板"

# 创建项目目录
PROJECT_DIR="/www/wwwroot/ai-trading"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo "✅ 创建项目目录: $PROJECT_DIR"
else
    echo "⚠️ 项目目录已存在，将进行覆盖部署"
fi

# 复制项目文件
echo "📂 复制项目文件..."
cp -r ./* "$PROJECT_DIR/"
echo "✅ 项目文件复制完成"

# 设置文件权限
chown -R www:www "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
echo "✅ 文件权限设置完成"

# 创建环境变量文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "⚠️ 请编辑 $PROJECT_DIR/.env 文件配置实际参数"
fi

# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "🐳 安装Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
    echo "✅ Docker安装完成"
else
    echo "✅ Docker已安装"
fi

# 安装Docker Compose（如果未安装）
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "✅ Docker Compose已安装"
fi

# 构建Docker镜像
echo "🔨 构建Docker镜像..."
cd "$PROJECT_DIR"
docker build -t ai-trading:latest .
echo "✅ Docker镜像构建完成"

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d
echo "✅ 服务启动完成"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
if docker ps | grep ai-trading > /dev/null; then
    echo "✅ 所有服务运行正常"
else
    echo "❌ 部分服务启动失败，请检查日志"
    docker-compose -f docker-compose.prod.yml logs
fi

# 创建Nginx配置
echo "🌐 配置Nginx反向代理..."
NGINX_CONF="/www/server/panel/vhost/nginx/ai-trading.conf"
cat > "$NGINX_CONF" << 'EOF'
server {
    listen 80;
    server_name _;
    
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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location / {
        root /www/wwwroot/ai-trading/web_app/static;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 重启Nginx
systemctl restart nginx
echo "✅ Nginx配置完成"

# 创建PM2配置
echo "🔄 配置PM2进程管理..."
PM2_CONFIG="$PROJECT_DIR/ecosystem.config.js"
cat > "$PM2_CONFIG" << 'EOF'
module.exports = {
  apps: [{
    name: 'ai-trading-web',
    script: 'python',
    args: 'web_app/main.py',
    cwd: '/www/wwwroot/ai-trading',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }, {
    name: 'ai-trading-data',
    script: 'python',
    args: 'scripts/start_data_collection.py',
    cwd: '/www/wwwroot/ai-trading',
    instances: 1,
    autorestart: true,
    watch: false
  }]
}
EOF

# 安装PM2
if ! command -v pm2 &> /dev/null; then
    npm install pm2 -g
fi

# 启动PM2
pm2 start "$PM2_CONFIG"
pm2 save
pm2 startup
echo "✅ PM2配置完成"

# 创建系统服务
echo "🔧 创建系统服务..."
SERVICE_FILE="/etc/systemd/system/ai-trading.service"
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=AI量化交易系统
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www
Group=www
WorkingDirectory=/www/wwwroot/ai-trading
ExecStart=/usr/bin/pm2 start ecosystem.config.js
ExecReload=/usr/bin/pm2 reload ecosystem.config.js
ExecStop=/usr/bin/pm2 stop ecosystem.config.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-trading.service
systemctl start ai-trading.service
echo "✅ 系统服务配置完成"

# 配置防火墙
echo "🔥 配置防火墙规则..."
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=9090/tcp
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --reload
echo "✅ 防火墙规则配置完成"

# 创建监控脚本
echo "📊 配置监控脚本..."
MONITOR_SCRIPT="$PROJECT_DIR/scripts/monitor.sh"
cat > "$MONITOR_SCRIPT" << 'EOF'
#!/bin/bash

# AI量化交易系统监控脚本

LOG_FILE="/www/wwwroot/ai-trading/logs/monitor.log"

# 创建日志目录
mkdir -p /www/wwwroot/ai-trading/logs

# 监控函数
monitor_system() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始系统监控检查..." >> "$LOG_FILE"
    
    # 检查Docker服务
    if ! systemctl is-active --quiet docker; then
        echo "❌ Docker服务异常，尝试重启..." >> "$LOG_FILE"
        systemctl restart docker
    fi
    
    # 检查应用服务
    if ! docker ps | grep ai-trading > /dev/null; then
        echo "❌ 交易系统服务异常，尝试重启..." >> "$LOG_FILE"
        cd /www/wwwroot/ai-trading
        docker-compose -f docker-compose.prod.yml restart
    fi
    
    # 检查PM2服务
    if ! pm2 list | grep ai-trading > /dev/null; then
        echo "❌ PM2服务异常，尝试重启..." >> "$LOG_FILE"
        cd /www/wwwroot/ai-trading
        pm2 restart ecosystem.config.js
    fi
    
    # 检查系统资源
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$CPU_USAGE" -gt 80 ]; then
        echo "⚠️ CPU使用率过高: ${CPU_USAGE}%" >> "$LOG_FILE"
    fi
    
    if [ "$(echo "$MEM_USAGE > 85" | bc)" -eq 1 ]; then
        echo "⚠️ 内存使用率过高: ${MEM_USAGE}%" >> "$LOG_FILE"
    fi
    
    if [ "$DISK_USAGE" -gt 90 ]; then
        echo "⚠️ 磁盘使用率过高: ${DISK_USAGE}%" >> "$LOG_FILE"
    fi
    
    echo "✅ 系统监控检查完成" >> "$LOG_FILE"
}

# 执行监控
monitor_system

# 清理旧日志（保留最近7天）
find /www/wwwroot/ai-trading/logs -name "*.log" -mtime +7 -delete
EOF

chmod +x "$MONITOR_SCRIPT"

# 添加定时任务
(crontab -l 2>/dev/null; echo "*/5 * * * * $MONITOR_SCRIPT") | crontab -
echo "✅ 监控脚本配置完成"

# 部署完成信息
echo ""
echo "🎉 AI量化交易系统部署完成！"
echo "========================================"
echo "📊 访问地址: http://你的服务器IP或域名"
echo "🔧 管理地址: http://你的服务器IP:9090 (Prometheus)"
echo "📈 监控地址: http://你的服务器IP:3000 (Grafana)"
echo ""
echo "📋 后续配置步骤："
echo "1. 通过宝塔面板配置SSL证书"
echo "2. 配置域名解析指向服务器IP"
echo "3. 编辑 $PROJECT_DIR/.env 文件配置API密钥"
echo "4. 通过宝塔面板重启Nginx服务"
echo ""
echo "⚠️ 重要提醒："
echo "- 加密货币交易具有高风险，请谨慎使用"
echo "- 建议先在模拟环境中充分测试"
echo "- 定期备份数据和配置文件"

# 健康检查
echo ""
echo "🔍 运行健康检查..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 系统健康检查通过"
else
    echo "❌ 健康检查失败，请检查服务状态"
fi