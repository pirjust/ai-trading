#!/bin/bash

# AI量化交易系统 - 服务启动脚本
# 宝塔面板专用

echo "🚀 启动AI量化交易系统服务"
echo "========================================"

# 检查是否为root用户
if [ "$(id -u)" != "0" ]; then
    echo "❌ 请使用root用户运行此脚本"
    exit 1
fi

# 项目目录
PROJECT_DIR="/www/wwwroot/ai-trading"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    echo "请先运行部署脚本或检查项目路径"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查Docker服务
if ! systemctl is-active --quiet docker; then
    echo "🐳 启动Docker服务..."
    systemctl start docker
    systemctl enable docker
    sleep 5
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 停止现有服务（如果存在）
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.prod.yml down

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
services=("web_app" "postgres" "redis" "influxdb" "prometheus" "grafana")

all_healthy=true
for service in "${services[@]}"; do
    if docker ps | grep "$service" > /dev/null; then
        echo "✅ $service 服务运行正常"
    else
        echo "❌ $service 服务启动失败"
        all_healthy=false
    fi
done

# 检查应用健康状态
echo "🏥 检查应用健康状态..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 应用健康检查通过"
else
    echo "❌ 应用健康检查失败"
    all_healthy=false
fi

# 启动PM2进程（如果使用）
if command -v pm2 &> /dev/null; then
    echo "🔄 启动PM2进程..."
    pm2 restart ecosystem.config.js 2>/dev/null || pm2 start ecosystem.config.js
    pm2 save
    echo "✅ PM2进程启动完成"
fi

# 启动系统服务
echo "🔧 启动系统服务..."
if systemctl is-enabled ai-trading.service > /dev/null 2>&1; then
    systemctl start ai-trading.service
    systemctl enable ai-trading.service
    echo "✅ 系统服务启动完成"
fi

# 重启Nginx
echo "🌐 重启Nginx服务..."
systemctl restart nginx

# 检查防火墙规则
echo "🔥 检查防火墙规则..."
ports=(80 443 8000 9090 3000)
for port in "${ports[@]}"; do
    if firewall-cmd --list-ports | grep -q "$port/tcp"; then
        echo "✅ 端口 $port 已开放"
    else
        echo "⚠️ 端口 $port 未开放，正在添加..."
        firewall-cmd --permanent --add-port=$port/tcp
    fi
done

if firewall-cmd --reload; then
    echo "✅ 防火墙规则更新完成"
fi

# 启动监控脚本
echo "📊 启动监控脚本..."
if [ -f "scripts/monitor.sh" ]; then
    chmod +x scripts/monitor.sh
    # 添加到crontab（如果不存在）
    if ! crontab -l | grep -q "monitor.sh"; then
        (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/scripts/monitor.sh") | crontab -
    fi
    echo "✅ 监控脚本配置完成"
fi

# 启动Python监控服务
echo "🐍 启动Python监控服务..."
if [ -f "scripts/system_monitor.py" ]; then
    # 使用nohup后台运行监控服务
    nohup python3 scripts/system_monitor.py > logs/system_monitor.log 2>&1 &
    echo "✅ Python监控服务启动完成"
fi

# 最终状态检查
echo ""
echo "🎉 AI量化交易系统启动完成！"
echo "========================================"

if [ "$all_healthy" = true ]; then
    echo "✅ 所有服务启动成功"
else
    echo "⚠️ 部分服务启动异常，请检查日志"
fi

echo ""
echo "📊 访问地址:"
echo "   主应用: http://你的服务器IP或域名"
echo "   Prometheus: http://你的服务器IP:9090"
echo "   Grafana: http://你的服务器IP:3000"
echo ""
echo "🔧 管理命令:"
echo "   查看服务状态: docker-compose -f docker-compose.prod.yml ps"
echo "   查看日志: docker-compose -f docker-compose.prod.yml logs"
echo "   重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "   停止服务: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "⚠️ 重要提醒:"
echo "   - 首次访问Grafana需要设置管理员密码"
echo "   - 请及时配置SSL证书和域名"
echo "   - 定期检查系统监控和日志"

# 显示服务状态
echo ""
echo "🔍 当前服务状态:"
docker-compose -f docker-compose.prod.yml ps