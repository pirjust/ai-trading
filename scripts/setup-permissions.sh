#!/bin/bash
# 权限设置脚本
# 设置AI量化交易系统的文件和目录权限

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "请使用root权限运行此脚本"
    fi
}

# 设置项目目录权限
setup_project_permissions() {
    local project_path="/www/wwwroot/ai-trading"
    
    log "设置项目目录权限..."
    
    # 创建项目目录（如果不存在）
    mkdir -p "$project_path"
    
    # 设置目录所有者
    chown -R www:www "$project_path"
    
    # 设置目录权限
    find "$project_path" -type d -exec chmod 755 {} \;
    
    # 设置文件权限
    find "$project_path" -type f -exec chmod 644 {} \;
    
    # 特殊权限设置
    
    # 日志目录 - 可写
    mkdir -p "$project_path/logs"
    chmod 777 "$project_path/logs"
    
    # 配置文件 - 只读
    if [ -d "$project_path/config" ]; then
        find "$project_path/config" -type f -name "*.py" -exec chmod 600 {} \;
        find "$project_path/config" -type f -name "*.yaml" -exec chmod 600 {} \;
        find "$project_path/config" -type f -name "*.json" -exec chmod 600 {} \;
    fi
    
    # 脚本文件 - 可执行
    if [ -d "$project_path/scripts" ]; then
        find "$project_path/scripts" -type f -name "*.sh" -exec chmod 755 {} \;
        find "$project_path/scripts" -type f -name "*.py" -exec chmod 755 {} \;
    fi
    
    # 前端静态文件
    if [ -d "$project_path/frontend/dist" ]; then
        chmod -R 755 "$project_path/frontend/dist"
    fi
    
    log "项目目录权限设置完成"
}

# 设置数据库权限
setup_database_permissions() {
    log "设置数据库权限..."
    
    # PostgreSQL数据目录
    if [ -d "/var/lib/postgresql" ]; then
        chown -R postgres:postgres /var/lib/postgresql
        chmod 700 /var/lib/postgresql/*/main
        log "PostgreSQL数据目录权限设置完成"
    fi
    
    # Redis数据目录
    if [ -d "/var/lib/redis" ]; then
        chown -R redis:redis /var/lib/redis
        chmod 750 /var/lib/redis
        log "Redis数据目录权限设置完成"
    fi
}

# 设置服务权限
setup_service_permissions() {
    log "设置服务权限..."
    
    # Nginx配置目录
    if [ -d "/etc/nginx" ]; then
        chown -R root:root /etc/nginx
        chmod 644 /etc/nginx/nginx.conf
        chmod 644 /etc/nginx/conf.d/*.conf 2>/dev/null || true
        log "Nginx配置权限设置完成"
    fi
    
    # Supervisor配置
    if [ -d "/etc/supervisor" ]; then
        chown -R root:root /etc/supervisor
        chmod 644 /etc/supervisor/supervisord.conf
        chmod 644 /etc/supervisor/conf.d/*.conf 2>/dev/null || true
        log "Supervisor配置权限设置完成"
    fi
    
    # 系统服务文件
    if [ -d "/etc/systemd/system" ]; then
        # 确保服务文件权限正确
        find /etc/systemd/system -name "*.service" -exec chmod 644 {} \; 2>/dev/null || true
        log "系统服务权限设置完成"
    fi
}

# 设置日志权限
setup_log_permissions() {
    log "设置日志权限..."
    
    # 应用日志
    local log_path="/www/wwwroot/ai-trading/logs"
    mkdir -p "$log_path"
    chown -R www:www "$log_path"
    chmod 755 "$log_path"
    
    # 确保日志文件可写
    touch "$log_path/api.log" "$log_path/api-error.log" \
          "$log_path/monitor.log" "$log_path/monitor-error.log"
    chown www:www "$log_path"/*.log
    chmod 666 "$log_path"/*.log
    
    # 系统日志目录
    if [ -d "/var/log" ]; then
        # Nginx日志
        if [ -d "/var/log/nginx" ]; then
            chown -R www:www /var/log/nginx
            chmod 755 /var/log/nginx
        fi
        
        # PostgreSQL日志
        if [ -d "/var/log/postgresql" ]; then
            chown -R postgres:postgres /var/log/postgresql
            chmod 755 /var/log/postgresql
        fi
        
        # Redis日志
        if [ -f "/var/log/redis/redis-server.log" ]; then
            chown redis:redis /var/log/redis/redis-server.log
            chmod 644 /var/log/redis/redis-server.log
        fi
    fi
    
    log "日志权限设置完成"
}

# 设置备份目录权限
setup_backup_permissions() {
    log "设置备份目录权限..."
    
    local backup_path="/backup"
    
    # 创建备份目录结构
    mkdir -p "$backup_path/{database,application,config}"
    
    # 设置备份目录权限
    chown -R root:root "$backup_path"
    chmod 755 "$backup_path"
    chmod 700 "$backup_path"/*
    
    # 数据库备份目录（PostgreSQL用户需要访问）
    chown postgres:postgres "$backup_path/database"
    chmod 750 "$backup_path/database"
    
    log "备份目录权限设置完成"
}

# 设置SSL证书权限
setup_ssl_permissions() {
    log "设置SSL证书权限..."
    
    # Nginx SSL证书目录
    if [ -d "/www/server/panel/vhost/ssl" ]; then
        chown -R root:root /www/server/panel/vhost/ssl
        chmod 600 /www/server/panel/vhost/ssl/*.key 2>/dev/null || true
        chmod 644 /www/server/panel/vhost/ssl/*.crt 2>/dev/null || true
        log "SSL证书权限设置完成"
    fi
    
    # Let's Encrypt证书目录
    if [ -d "/etc/letsencrypt" ]; then
        chown -R root:root /etc/letsencrypt
        chmod 755 /etc/letsencrypt/{live,archive}
        chmod 600 /etc/letsencrypt/live/*/privkey.pem 2>/dev/null || true
        chmod 644 /etc/letsencrypt/live/*/fullchain.pem 2>/dev/null || true
        log "Let's Encrypt证书权限设置完成"
    fi
}

# 设置安全配置
setup_security_config() {
    log "设置安全配置..."
    
    # 设置umask
    echo "umask 0022" >> /etc/profile
    
    # 禁用不必要的服务
    local services=("apache2" "httpd" "tomcat" "mysql" "mariadb")
    for service in "${services[@]}"; do
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            warn "禁用不必要的服务: $service"
            systemctl disable "$service" 2>/dev/null || true
        fi
    done
    
    # 设置文件属性（如果支持）
    if command_exists chattr; then
        # 保护关键系统文件
        chattr +i /etc/passwd /etc/shadow /etc/group /etc/gshadow 2>/dev/null || true
        
        # 保护配置文件
        chattr +i /www/server/panel/ssl/*.key 2>/dev/null || true
    fi
    
    log "安全配置设置完成"
}

# 验证权限设置
verify_permissions() {
    log "验证权限设置..."
    
    local project_path="/www/wwwroot/ai-trading"
    local errors=0
    
    # 检查项目目录权限
    if [ ! -d "$project_path" ]; then
        error "项目目录不存在: $project_path"
    fi
    
    local owner=$(stat -c %U "$project_path")
    if [ "$owner" != "www" ]; then
        warn "项目目录所有者不正确: $owner (应为: www)"
        ((errors++))
    fi
    
    # 检查日志目录权限
    if [ -d "$project_path/logs" ]; then
        local log_perm=$(stat -c %a "$project_path/logs")
        if [ "$log_perm" != "755" ]; then
            warn "日志目录权限不正确: $log_perm (应为: 755)"
            ((errors++))
        fi
    fi
    
    # 检查脚本文件权限
    if [ -d "$project_path/scripts" ]; then
        for script in "$project_path/scripts"/*.sh; do
            if [ -f "$script" ]; then
                local script_perm=$(stat -c %a "$script")
                if [ "$script_perm" != "755" ]; then
                    warn "脚本文件权限不正确: $script - $script_perm (应为: 755)"
                    ((errors++))
                fi
            fi
        done
    fi
    
    if [ $errors -eq 0 ]; then
        log "✅ 权限验证通过"
    else
        warn "权限验证发现 $errors 个问题"
    fi
}

# 显示权限摘要
show_permission_summary() {
    log "权限设置摘要:"
    
    local project_path="/www/wwwroot/ai-trading"
    
    echo ""
    echo "项目目录: $project_path"
    if [ -d "$project_path" ]; then
        echo "  所有者: $(stat -c %U:%G "$project_path")"
        echo "  权限: $(stat -c %a "$project_path")"
    fi
    
    echo ""
    echo "日志目录: $project_path/logs"
    if [ -d "$project_path/logs" ]; then
        echo "  所有者: $(stat -c %U:%G "$project_path/logs")"
        echo "  权限: $(stat -c %a "$project_path/logs")"
    fi
    
    echo ""
    echo "关键服务:"
    local services=("nginx" "postgresql" "redis" "supervisor")
    for service in "${services[@]}"; do
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            echo "  $service: $(systemctl is-active "$service")"
        fi
    done
}

# 主函数
main() {
    log "开始设置AI量化交易系统权限..."
    
    check_root
    
    setup_project_permissions
    setup_database_permissions
    setup_service_permissions
    setup_log_permissions
    setup_backup_permissions
    setup_ssl_permissions
    setup_security_config
    
    verify_permissions
    show_permission_summary
    
    log "权限设置完成！"
    log "建议重启相关服务使权限设置生效"
}

# 使用说明
usage() {
    echo "AI量化交易系统权限设置脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help    显示帮助信息"
    echo "  -v, --verify  仅验证权限，不进行设置"
    echo "  -s, --summary 显示权限摘要"
    echo ""
}

# 参数处理
case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
    -v|--verify)
        check_root
        verify_permissions
        exit 0
        ;;
    -s|--summary)
        show_permission_summary
        exit 0
        ;;
    *)
        main
        ;;
esac