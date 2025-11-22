# AI量化交易系统完整部署指南

## 🎯 概述

本文档提供AI量化交易系统从GitHub仓库到腾讯云Ubuntu宝塔面板的完整一键部署方案。包含自动化部署、监控、安全、维护等全方位指导。

## 📋 快速开始

### 1. 环境要求

#### 1.1 腾讯云服务器
- **操作系统**: Ubuntu 20.04/22.04 LTS
- **硬件配置**: 
  - CPU: 2核或以上
  - 内存: 4GB或以上  
  - 硬盘: 50GB或以上
- **网络**: 公网IP，开放80/443/22/8888端口

#### 1.2 GitHub仓库
- 代码已上传到GitHub
- 配置GitHub Actions secrets
- 设置分支保护规则

### 2. 一键部署流程

```bash
# 1. 登录腾讯云服务器
ssh root@your-server-ip

# 2. 下载自动配置脚本
wget -O baota_auto_setup.sh https://raw.githubusercontent.com/your-org/ai-trading/main/scripts/baota_auto_setup.sh
chmod +x baota_auto_setup.sh

# 3. 执行自动配置
./baota_auto_setup.sh

# 4. 配置GitHub Secrets（在GitHub仓库设置中）
TENCENT_CLOUD_HOST=123.123.123.123
TENCENT_CLOUD_PORT=22
TENCENT_CLOUD_SSH_KEY=-----BEGIN RSA PRIVATE KEY-----...
SLACK_WEBHOOK=https://hooks.slack.com/...

# 5. 推送代码触发部署
git add .
git commit -m "feat: 新功能"
git push origin main
```

## 🔧 详细部署说明

### 1. GitHub Actions自动化部署

#### 1.1 工作流配置
位置: `.github/workflows/deploy-to-baota.yml`

**触发条件**:
- 推送到main/master分支
- 推送v*标签
- 手动触发

**部署流程**:
1. **代码检查**: 拉取代码、运行测试
2. **前端构建**: 构建React/Vue前端应用  
3. **打包部署**: 创建部署包并上传到服务器
4. **服务部署**: 在服务器上解压、安装依赖、启动服务
5. **健康检查**: 验证服务是否正常运行
6. **通知发送**: 发送部署结果通知

#### 1.2 环境配置
支持多环境部署：
- **production**: 生产环境
- **staging**: 测试环境

### 2. 宝塔面板配置

#### 2.1 自动配置脚本
位置: `scripts/baota_auto_setup.sh`

**功能**:
- 自动安装宝塔面板
- 配置防火墙和安全设置
- 安装系统依赖和Python环境
- 配置数据库(PostgreSQL + Redis)
- 设置Nginx反向代理
- 配置Supervisor进程管理

#### 2.2 宝塔面板后续配置

**安全设置**:
```bash
# 修改默认端口
bt default

# 设置强密码
bt passwd

# 启用SSL
bt ssl
```

**软件安装**:
- Nginx 1.22+
- PostgreSQL 15+
- Redis 7.0+
- Python项目管理器

### 3. 应用部署配置

#### 3.1 项目结构
```
/www/wwwroot/ai-trading/
├── app/                 # FastAPI应用
├── config/              # 配置文件
├── core/                # 核心模块
├── data/                # 数据模块
├── ai_engine/           # AI引擎
├── strategies/          # 交易策略
├── frontend/dist/       # 前端构建文件
├── scripts/             # 部署脚本
└── logs/                # 日志文件
```

#### 3.2 环境配置
位置: `config/deployment_env.py`

生成配置文件：
- `.env.production` - 生产环境变量
- `config/nginx.conf` - Nginx配置
- `config/supervisor.conf` - Supervisor配置
- `requirements.txt` - Python依赖

#### 3.3 数据库配置

**PostgreSQL**:
```sql
CREATE USER ai_trader WITH PASSWORD 'your_secure_password_123';
CREATE DATABASE ai_trading OWNER ai_trader;
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
```

**Redis**:
```ini
# /etc/redis/redis.conf
requirepass your_redis_password_123
bind 0.0.0.0
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## 📊 监控和日志

### 1. 系统监控

#### 1.1 宝塔面板监控
- 系统资源监控(CPU/内存/磁盘)
- 服务状态监控
- 访问日志分析

#### 1.2 自定义监控
位置: `monitoring/`
- `trading_monitor.py` - 交易监控
- `system_monitor.py` - 系统监控
- `prometheus_client.py` - 指标收集

#### 1.3 健康检查
位置: `scripts/health_check.py`

```bash
# 运行健康检查
python scripts/health_check.py --verbose

# 定时检查（crontab）
*/5 * * * * cd /www/wwwroot/ai-trading && python scripts/health_check.py >> /var/log/ai-trading-health.log
```

### 2. 日志管理

#### 2.1 日志文件位置
```
# 应用日志
/www/wwwroot/ai-trading/logs/
├── api.log              # API服务日志
├── api-error.log        # API错误日志
├── monitor.log          # 监控服务日志
└── monitor-error.log    # 监控错误日志

# 系统日志
/var/log/
├── nginx/               # Nginx日志
├── postgresql/          # PostgreSQL日志
└── redis/               # Redis日志
```

#### 2.2 日志轮转配置
```bash
# 配置日志轮转
cat > /etc/logrotate.d/ai-trading << EOF
/www/wwwroot/ai-trading/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

## 🔒 安全配置

### 1. 服务器安全

#### 1.1 防火墙配置
```bash
# 只开放必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 19999/tcp # 宝塔面板
ufw --force enable
```

#### 1.2 SSH安全配置
```bash
# 修改SSH配置
vim /etc/ssh/sshd_config

# 重要安全设置
Port 2222                    # 修改默认端口
PermitRootLogin no          # 禁止root登录
PasswordAuthentication no   # 禁用密码认证
PubkeyAuthentication yes    # 启用密钥认证
MaxAuthTries 3              # 最大认证尝试次数
```

### 2. 应用安全

#### 2.1 API安全配置
```python
# FastAPI安全中间件
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
```

#### 2.2 安全检查
位置: `scripts/security_check.py`

```bash
# 运行安全检查
python scripts/security_check.py --verbose

# 检查内容
- 防火墙状态
- SSH安全配置
- SSL证书配置
- API安全头
- 数据库安全
- 文件权限
- 开放端口
```

## 🚨 故障排除

### 1. 常见问题

#### 1.1 部署失败

**问题**: GitHub Actions部署失败
**解决**:
```bash
# 检查服务器连接
ssh -p $PORT $USER@$HOST "echo '连接测试'"

# 检查服务器资源
df -h  # 磁盘空间
free -h # 内存使用
top     # CPU使用
```

**问题**: 服务启动失败
**解决**:
```bash
# 检查服务状态
systemctl status nginx
systemctl status postgresql
systemctl status redis

# 检查应用日志
tail -f /www/wwwroot/ai-trading/logs/api.log
```

#### 1.2 数据库连接问题

**问题**: 数据库连接失败
**解决**:
```bash
# 检查数据库服务
systemctl status postgresql

# 测试数据库连接
psql -h localhost -U ai_trader -d ai_trading

# 检查连接数
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 1.3 Nginx配置问题

**问题**: 网站无法访问
**解决**:
```bash
# 检查Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx

# 检查端口监听
netstat -tlnp | grep :80
```

### 2. 性能优化

#### 2.1 数据库优化
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_trades_timestamp ON trades(timestamp);
CREATE INDEX CONCURRENTLY idx_trades_symbol ON trades(symbol);

-- 定期维护
VACUUM ANALYZE trades;
```

#### 2.2 Nginx优化
```nginx
# 性能优化配置
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 连接池优化
worker_connections 1024;
keepalive_timeout 65;
```

## 📈 扩展功能

### 1. 多环境部署

支持production/staging环境分离部署：

```yaml
# GitHub Actions多环境配置
jobs:
  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    environment: staging
```

### 2. 自动回滚

配置自动回滚策略：

```yaml
# 回滚配置
- name: Rollback on failure
  if: failure()
  run: |
    # 恢复备份
    ssh $DEPLOY_USER@$DEPLOY_HOST "
    if [ -d \"$BACKUP_DIR\" ]; then
        rm -rf $DEPLOY_PATH
        cp -r $BACKUP_DIR $DEPLOY_PATH
        # 重启服务
    fi
    "
```

### 3. 监控告警

集成Prometheus + Grafana监控：

```yaml
# 监控配置
- name: Deploy monitoring stack
  run: |
    docker-compose -f deploy/docker-compose.monitoring.yml up -d
```

## 🔄 维护和更新

### 1. 定期维护任务

#### 1.1 数据库备份
```bash
# 每日备份脚本
#!/bin/bash
pg_dump -h localhost -U ai_trader ai_trading > /backup/ai_trading_$(date +%Y%m%d).sql
find /backup -name "ai_trading_*.sql" -mtime +7 -delete
```

#### 1.2 日志清理
```bash
# 每周清理日志
find /www/wwwroot/ai-trading/logs -name "*.log.*" -mtime +30 -delete
find /var/log/nginx -name "*.log.*" -mtime +30 -delete
```

### 2. 系统更新

#### 2.1 安全更新
```bash
# 定期系统更新
apt update && apt upgrade -y

# 重启服务
systemctl restart nginx postgresql redis
```

#### 2.2 应用更新
- 通过GitHub Actions自动部署
- 手动触发或代码推送触发
- 支持版本回滚

## 📞 技术支持

### 1. 获取帮助

- **GitHub Issues**: 报告问题和功能请求
- **文档**: 查看详细配置说明
- **日志**: 检查应用和系统日志

### 2. 紧急联系方式

- **服务器运维**: 腾讯云控制台
- **应用问题**: 查看监控告警
- **数据问题**: 检查数据库备份

## 🎯 部署检查清单

### 部署前检查
- [ ] 服务器资源充足
- [ ] 网络连接正常
- [ ] 域名解析正确
- [ ] GitHub仓库配置完成
- [ ] SSH密钥配置正确

### 部署中检查
- [ ] 宝塔面板安装成功
- [ ] 系统依赖安装完成
- [ ] 数据库配置正确
- [ ] 应用部署成功
- [ ] 服务启动正常

### 部署后检查
- [ ] 网站可正常访问
- [ ] API接口响应正常
- [ ] 数据库连接正常
- [ ] 监控系统运行正常
- [ ] 安全配置生效

## 📁 文件清单

### 核心配置文件
```
config/
├── deployment_checklist.yaml    # 部署检查清单
├── deployment_config.yaml        # 部署配置
├── deployment_env.py            # 环境配置
├── bt_panel_config.json        # 宝塔面板配置
└── baota_deploy_config.json    # 宝塔部署配置

scripts/
├── baota_auto_setup.sh          # 宝塔自动配置
├── quick-deploy.sh              # 快速部署脚本
├── health_check.py              # 健康检查
├── security_check.py            # 安全检查
├── deploy-utils.sh              # 部署工具
└── deployment_checklist.py      # 部署检查

.github/workflows/
├── deploy-to-baota.yml          # GitHub Actions部署
└── monitor.yml                  # 监控配置
```

### 文档文件
```
docs/
├── DEPLOYMENT_COMPLETE_GUIDE.md    # 完整部署指南（本文档）
├── GITHUB_TO_BAOTA_DEPLOYMENT_GUIDE.md  # GitHub到宝塔部署指南
├── 宝塔面板一键部署指南.md          # 宝塔面板部署指南
├── DEPLOYMENT_SUMMARY.md          # 部署总结
└── DEPLOYMENT_GUIDE.md           # 基础部署指南
```

---

*文档版本: v3.0*  
*最后更新: 2024年11月*  
*适用环境: GitHub + 腾讯云Ubuntu + 宝塔面板*  
*技术支持: GitHub Issues 或 项目文档*