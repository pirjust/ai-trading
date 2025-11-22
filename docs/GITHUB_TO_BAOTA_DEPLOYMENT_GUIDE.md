# GitHub到腾讯云宝塔面板一键部署指南

## 📋 概述

本指南提供完整的AI量化交易系统从GitHub仓库一键部署到腾讯云Ubuntu系统宝塔面板的完整方案。支持自动化部署、监控、回滚等功能。

## 🚀 快速开始

### 1. 准备工作

#### 1.1 腾讯云服务器要求
- **操作系统**: Ubuntu 20.04/22.04 LTS
- **硬件配置**: 
  - CPU: 2核或以上
  - 内存: 4GB或以上
  - 硬盘: 50GB或以上
- **网络**: 公网IP，开放80/443/22/8888端口

#### 1.2 GitHub仓库配置
- 确保代码已上传到GitHub
- 配置GitHub Actions secrets
- 设置分支保护规则

### 2. 一键部署步骤

#### 2.1 腾讯云服务器初始化

```bash
# 登录腾讯云服务器
ssh root@your-server-ip

# 下载并执行宝塔面板自动配置脚本
wget -O baota_auto_setup.sh https://raw.githubusercontent.com/your-org/ai-trading/main/scripts/baota_auto_setup.sh
chmod +x baota_auto_setup.sh
./baota_auto_setup.sh
```

#### 2.2 配置GitHub Actions Secrets

在GitHub仓库中配置以下Secrets：

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `TENCENT_CLOUD_HOST` | 腾讯云服务器IP | `123.123.123.123` |
| `TENCENT_CLOUD_PORT` | SSH端口 | `22` |
| `TENCENT_CLOUD_SSH_KEY` | SSH私钥 | `-----BEGIN RSA PRIVATE KEY-----...` |
| `SLACK_WEBHOOK` | 部署通知(可选) | `https://hooks.slack.com/...` |

#### 2.3 触发自动部署

**方式一：推送代码触发**
```bash
# 推送代码到main分支触发部署
git add .
git commit -m "feat: 新功能"
git push origin main
```

**方式二：手动触发部署**
1. 进入GitHub Actions页面
2. 选择"Deploy to Tencent Cloud Baota Panel"
3. 点击"Run workflow"
4. 选择环境（production/staging）

## 🔧 详细配置说明

### 1. GitHub Actions配置

#### 1.1 工作流文件 (.github/workflows/deploy-to-baota.yml)

```yaml
name: Deploy to Tencent Cloud Baota Panel

on:
  push:
    branches: [main, master]
    tags: ['v*']
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging
```

#### 1.2 部署流程
1. **代码检查**: 拉取代码、运行测试
2. **前端构建**: 构建React/Vue前端应用
3. **打包部署**: 创建部署包并上传到服务器
4. **服务部署**: 在服务器上解压、安装依赖、启动服务
5. **健康检查**: 验证服务是否正常运行
6. **通知发送**: 发送部署结果通知

### 2. 宝塔面板配置

#### 2.1 自动配置脚本 (scripts/baota_auto_setup.sh)

脚本功能：
- 自动安装宝塔面板
- 配置防火墙和安全设置
- 安装系统依赖和Python环境
- 配置数据库(PostgreSQL + Redis)
- 设置Nginx反向代理
- 配置Supervisor进程管理

#### 2.2 宝塔面板后续配置

登录宝塔面板后需要手动配置：

1. **修改面板安全设置**
   - 修改默认端口(8888 → 19999)
   - 设置强密码
   - 启用SSL加密

2. **安装必要软件**
   - Nginx 1.22+
   - PostgreSQL 15+
   - Redis 7.0+
   - Python项目管理器

3. **配置Python项目**
   - 项目路径: `/www/wwwroot/ai-trading`
   - Python版本: 3.9
   - 启动文件: `app/main:app`
   - 端口: 8000

### 3. 环境配置管理

#### 3.1 环境变量配置 (config/deployment_env.py)

```python
# 生成环境配置文件
python config/deployment_env.py
```

生成的文件：
- `.env.production` - 生产环境变量
- `config/nginx.conf` - Nginx配置
- `config/supervisor.conf` - Supervisor配置
- `requirements.txt` - Python依赖
- `pyproject.toml` - 项目配置

#### 3.2 数据库配置

**PostgreSQL配置**:
```sql
-- 创建数据库和用户
CREATE USER ai_trader WITH PASSWORD 'your_secure_password_123';
CREATE DATABASE ai_trading OWNER ai_trader;
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trader;
```

**Redis配置**:
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

#### 1.2 应用监控
- API服务健康检查
- 数据库连接监控
- 交易数据监控

#### 1.3 自定义监控
```python
# 监控脚本位置
monitoring/trading_monitor.py
monitoring/system_monitor.py
monitoring/prometheus_client.py
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

# 宝塔面板日志
/www/server/panel/logs/
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

#### 2.2 数据库安全
```sql
-- 创建只读用户用于监控
CREATE USER ai_monitor WITH PASSWORD 'monitor_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_monitor;
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

---

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

---

*文档版本: v2.0*  
*最后更新: 2024年11月*  
*适用环境: GitHub + 腾讯云Ubuntu + 宝塔面板*