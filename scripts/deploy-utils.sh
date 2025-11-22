#!/bin/bash
# 部署工具脚本
# 提供各种部署相关的实用函数

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if command_exists netstat; then
        netstat -tuln | grep ":$port " >/dev/null 2>&1
    elif command_exists ss; then
        ss -tuln | grep ":$port " >/dev/null 2>&1
    else
        # 使用/proc/net/tcp作为备选方案
        grep ":$(printf '%04X' $port)" /proc/net/tcp >/dev/null 2>&1
    fi
}

# 等待端口可用
wait_for_port() {
    local host=$1
    local port=$2
    local timeout=${3:-30}
    local counter=0
    
    while ! nc -z "$host" "$port" >/dev/null 2>&1; do
        sleep 1
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            error "端口 $host:$port 在 $timeout 秒内未就绪"
        fi
    done
    
    log "端口 $host:$port 已就绪"
}

# 检查服务状态
check_service_status() {
    local service_name=$1
    
    if systemctl is-active "$service_name" >/dev/null 2>&1; then
        echo "active"
    else
        echo "inactive"
    fi
}

# 启动服务
start_service() {
    local service_name=$1
    
    if [ "$(check_service_status "$service_name")" = "inactive" ]; then
        log "启动服务: $service_name"
        systemctl start "$service_name"
        systemctl enable "$service_name" 2>/dev/null || true
    else
        log "服务 $service_name 已在运行"
    fi
}

# 停止服务
stop_service() {
    local service_name=$1
    
    if [ "$(check_service_status "$service_name")" = "active" ]; then
        log "停止服务: $service_name"
        systemctl stop "$service_name"
    else
        log "服务 $service_name 未运行"
    fi
}

# 重启服务
restart_service() {
    local service_name=$1
    
    log "重启服务: $service_name"
    systemctl restart "$service_name"
}

# 备份文件或目录
backup_file() {
    local source_path=$1
    local backup_dir=${2:-/tmp/backups}
    
    if [ ! -e "$source_path" ]; then
        warn "备份源不存在: $source_path"
        return 1
    fi
    
    mkdir -p "$backup_dir"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="$(basename "$source_path")_${timestamp}"
    local backup_path="$backup_dir/$backup_name"
    
    if [ -d "$source_path" ]; then
        cp -r "$source_path" "$backup_path"
    else
        cp "$source_path" "$backup_path"
    fi
    
    log "备份完成: $source_path -> $backup_path"
    echo "$backup_path"
}

# 恢复备份
restore_backup() {
    local backup_path=$1
    local target_path=$2
    
    if [ ! -e "$backup_path" ]; then
        error "备份文件不存在: $backup_path"
    fi
    
    # 备份目标路径
    if [ -e "$target_path" ]; then
        backup_file "$target_path" "/tmp/restore_backup"
    fi
    
    if [ -d "$backup_path" ]; then
        rm -rf "$target_path"
        cp -r "$backup_path" "$target_path"
    else
        cp "$backup_path" "$target_path"
    fi
    
    log "恢复完成: $backup_path -> $target_path"
}

# 检查磁盘空间
check_disk_space() {
    local path=$1
    local threshold=${2:-10}  # 默认10%阈值
    
    local available=$(df "$path" | awk 'NR==2 {print $4}')
    local total=$(df "$path" | awk 'NR==2 {print $2}')
    local percent=$((available * 100 / total))
    
    if [ $percent -lt $threshold ]; then
        error "磁盘空间不足: $path 可用空间 ${percent}% < ${threshold}%"
    fi
    
    log "磁盘空间检查通过: $path 可用空间 ${percent}%"
}

# 检查内存使用
check_memory() {
    local threshold=${1:-85}  # 默认85%阈值
    
    local total=$(free | awk 'NR==2 {print $2}')
    local used=$(free | awk 'NR==2 {print $3}')
    local percent=$((used * 100 / total))
    
    if [ $percent -gt $threshold ]; then
        warn "内存使用率高: ${percent}% > ${threshold}%"
        return 1
    fi
    
    log "内存检查通过: 使用率 ${percent}%"
    return 0
}

# 检查CPU负载
check_cpu_load() {
    local threshold=${1:-80}  # 默认80%阈值
    
    local load=$(cat /proc/loadavg | awk '{print $1}')
    local cores=$(nproc)
    local percent=$(echo "scale=0; $load * 100 / $cores" | bc)
    
    if [ $percent -gt $threshold ]; then
        warn "CPU负载高: ${percent}% > ${threshold}%"
        return 1
    fi
    
    log "CPU负载检查通过: ${percent}%"
    return 0
}

# 发送部署通知
send_deployment_notification() {
    local status=$1
    local environment=$2
    local version=$3
    local message=$4
    
    # Slack通知
    if [ -n "$SLACK_WEBHOOK" ]; then
        local payload=$(cat <<EOF
{
    "text": "AI量化交易系统部署通知",
    "attachments": [
        {
            "color": "$([ "$status" = "success" ] && echo "good" || echo "danger")",
            "fields": [
                {
                    "title": "环境",
                    "value": "$environment",
                    "short": true
                },
                {
                    "title": "状态",
                    "value": "$status",
                    "short": true
                },
                {
                    "title": "版本",
                    "value": "$version",
                    "short": true
                },
                {
                    "title": "消息",
                    "value": "$message",
                    "short": false
                }
            ]
        }
    ]
}
EOF
        )
        
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK" || true
    fi
    
    # 邮件通知（需要配置邮件服务器）
    if [ -n "$EMAIL_RECIPIENTS" ] && command_exists mail; then
        local subject="AI量化交易系统部署 - $environment - $status"
        echo "$message" | mail -s "$subject" "$EMAIL_RECIPIENTS" || true
    fi
    
    log "部署通知已发送: $status"
}

# 生成随机密码
generate_random_password() {
    local length=${1:-16}
    tr -dc 'A-Za-z0-9!@#$%^&*()' < /dev/urandom | head -c "$length"
}

# 创建目录并设置权限
create_directory() {
    local path=$1
    local owner=${2:-www}
    local permissions=${3:-755}
    
    mkdir -p "$path"
    chown "$owner:$owner" "$path"
    chmod "$permissions" "$path"
    
    log "创建目录: $path (所有者: $owner, 权限: $permissions)"
}

# 设置文件权限
set_file_permissions() {
    local path=$1
    local owner=${2:-www}
    local permissions=${3:-644}
    
    if [ -e "$path" ]; then
        chown "$owner:$owner" "$path"
        chmod "$permissions" "$path"
        log "设置权限: $path (所有者: $owner, 权限: $permissions)"
    else
        warn "文件不存在: $path"
    fi
}

# 验证配置文件
validate_config_file() {
    local config_file=$1
    
    if [ ! -f "$config_file" ]; then
        error "配置文件不存在: $config_file"
    fi
    
    # 检查文件语法（根据文件类型）
    case "$config_file" in
        *.yaml|*.yml)
            if command_exists python3; then
                python3 -c "import yaml; yaml.safe_load(open('$config_file'))" || error "YAML配置文件语法错误: $config_file"
            fi
            ;;
        *.json)
            if command_exists python3; then
                python3 -c "import json; json.load(open('$config_file'))" || error "JSON配置文件语法错误: $config_file"
            elif command_exists jq; then
                jq . "$config_file" >/dev/null || error "JSON配置文件语法错误: $config_file"
            fi
            ;;
        *.conf|*.ini)
            # 基础语法检查
            if grep -q "\[\|=\|^#" "$config_file"; then
                : # 配置文件看起来正常
            else
                warn "配置文件可能格式错误: $config_file"
            fi
            ;;
    esac
    
    log "配置文件验证通过: $config_file"
}

# 检查依赖命令
check_dependencies() {
    local dependencies=("$@")
    local missing=()
    
    for dep in "${dependencies[@]}"; do
        if ! command_exists "$dep"; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "缺少依赖命令: ${missing[*]}"
    fi
    
    log "依赖检查通过: ${dependencies[*]}"
}

# 获取系统信息
get_system_info() {
    local info=()
    
    # 操作系统信息
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        info+=("OS: $NAME $VERSION")
    fi
    
    # 内核版本
    info+=("Kernel: $(uname -r)")
    
    # CPU信息
    info+=("CPU: $(nproc) cores")
    
    # 内存信息
    local mem_total=$(free -h | awk 'NR==2 {print $2}')
    info+=("Memory: $mem_total")
    
    # 磁盘信息
    local disk_total=$(df -h / | awk 'NR==2 {print $2}')
    local disk_used=$(df -h / | awk 'NR==2 {print $3}')
    local disk_percent=$(df -h / | awk 'NR==2 {print $5}')
    info+=("Disk: $disk_used/$disk_total ($disk_percent)")
    
    # 输出系统信息
    for line in "${info[@]}"; do
        log "$line"
    done
}

# 主函数（演示使用）
main() {
    log "部署工具脚本已加载"
    
    # 检查系统依赖
    check_dependencies "curl" "tar" "gzip" "ssh" "scp"
    
    # 获取系统信息
    get_system_info
    
    # 检查磁盘空间
    check_disk_space "/" 10
    
    # 检查内存和CPU
    check_memory 85
    check_cpu_load 80
}

# 如果直接运行脚本，执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi