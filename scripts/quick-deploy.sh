#!/bin/bash
# AI量化交易系统快速部署脚本
# 简化的部署流程，适用于紧急部署或测试环境

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

# 显示使用说明
usage() {
    echo "AI量化交易系统快速部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help           显示帮助信息"
    echo "  -e, --env ENV        部署环境 (production/staging)"
    echo "  -b, --branch BRANCH  部署分支 (默认: main)"
    echo "  -c, --config FILE    配置文件路径"
    echo ""
    echo "示例:"
    echo "  $0 --env production           # 部署生产环境"
    echo "  $0 --env staging --branch dev  # 部署测试环境dev分支"
    echo ""
}

# 检查必要工具
check_requirements() {
    log "检查部署环境要求..."
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        error "Git未安装"
    fi
    
    # 检查Docker（可选）
    if command -v docker &> /dev/null; then
        log "Docker已安装"
    else
        warn "Docker未安装，将使用传统部署方式"
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error "Python3未安装"
    fi
    
    log "环境检查完成"
}

# 拉取最新代码
pull_latest_code() {
    local branch=$1
    
    log "拉取最新代码..."
    
    # 检查当前目录是否是Git仓库
    if [ ! -d ".git" ]; then
        error "当前目录不是Git仓库"
    fi
    
    # 获取远程更新
    git fetch origin
    
    # 切换到指定分支
    git checkout $branch
    
    # 拉取最新代码
    git pull origin $branch
    
    log "代码更新完成，当前分支: $branch, 最新提交: $(git log -1 --pretty=%H)"
}

# 安装依赖
install_dependencies() {
    log "安装Python依赖..."
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 安装开发依赖（可选）
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
    
    log "依赖安装完成"
}

# 构建前端
build_frontend() {
    log "构建前端应用..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        # 检查是否安装了npm
        if command -v npm &> /dev/null; then
            npm install
            npm run build
            log "前端构建完成"
        else
            warn "npm未安装，跳过前端构建"
        fi
        
        cd ..
    else
        warn "前端目录不存在，跳过前端构建"
    fi
}

# 运行数据库迁移
run_migrations() {
    log "运行数据库迁移..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    if [ -f "scripts/database_migration.py" ]; then
        python scripts/database_migration.py migrate
        log "数据库迁移完成"
    else
        warn "数据库迁移脚本不存在，跳过迁移"
    fi
}

# 运行测试
run_tests() {
    local env=$1
    
    if [ "$env" = "production" ]; then
        log "生产环境跳过测试"
        return
    fi
    
    log "运行测试..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 运行单元测试
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short
        log "测试完成"
    else
        warn "pytest未安装，跳过测试"
    fi
}

# 启动服务
start_services() {
    local env=$1
    
    log "启动服务..."
    
    # 停止现有服务
    pkill -f "uvicorn" || true
    pkill -f "trading_monitor" || true
    
    sleep 2
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH=$(pwd)
    
    # 启动API服务
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > logs/api.log 2>&1 &
    
    # 启动监控服务
    nohup python -m monitoring.trading_monitor > logs/monitor.log 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if pgrep -f "uvicorn" > /dev/null; then
        log "API服务启动成功"
    else
        error "API服务启动失败"
    fi
    
    if pgrep -f "trading_monitor" > /dev/null; then
        log "监控服务启动成功"
    else
        warn "监控服务启动失败"
    fi
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://127.0.0.1:8000/health > /dev/null 2>&1; then
            log "健康检查通过"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "健康检查失败"
        fi
        
        warn "健康检查失败，第${attempt}次重试..."
        sleep 5
        ((attempt++))
    done
}

# 生成部署报告
generate_report() {
    local env=$1
    local branch=$2
    
    log "生成部署报告..."
    
    cat > deploy_report.txt << EOF
AI量化交易系统部署报告
========================

部署时间: $(date)
部署环境: $env
部署分支: $branch
最新提交: $(git log -1 --pretty=%H)

服务状态:
- API服务: $(pgrep -f "uvicorn" && echo "运行中" || echo "未运行")
- 监控服务: $(pgrep -f "trading_monitor" && echo "运行中" || echo "未运行")

访问地址:
- API接口: http://$(hostname -I | awk '{print $1}'):8000
- 健康检查: http://127.0.0.1:8000/health

日志文件:
- API日志: logs/api.log
- 监控日志: logs/monitor.log
- 部署日志: logs/deployment_check.log

下一步操作:
1. 检查服务状态: systemctl status nginx
2. 查看应用日志: tail -f logs/api.log
3. 运行完整检查: python scripts/deployment_checklist.py

EOF
    
    cat deploy_report.txt
    log "部署报告已保存到 deploy_report.txt"
}

# 主部署函数
deploy() {
    local env="production"
    local branch="main"
    local config_file=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -e|--env)
                env=$2
                shift 2
                ;;
            -b|--branch)
                branch=$2
                shift 2
                ;;
            -c|--config)
                config_file=$2
                shift 2
                ;;
            *)
                error "未知参数: $1"
                ;;
        esac
    done
    
    # 验证参数
    if [[ "$env" != "production" && "$env" != "staging" ]]; then
        error "环境参数必须是 production 或 staging"
    fi
    
    log "开始部署AI量化交易系统..."
    log "环境: $env, 分支: $branch"
    
    # 执行部署步骤
    check_requirements
    pull_latest_code $branch
    install_dependencies
    build_frontend
    run_migrations
    run_tests $env
    start_services $env
    health_check
    generate_report $env $branch
    
    log "🎉 AI量化交易系统部署完成！"
    log "请检查 deploy_report.txt 获取详细信息"
}

# 回滚函数
rollback() {
    local commit_hash=$1
    
    if [ -z "$commit_hash" ]; then
        # 如果没有指定提交，回滚到上一个版本
        commit_hash=$(git log --oneline -2 | tail -1 | awk '{print $1}')
    fi
    
    log "开始回滚到提交: $commit_hash"
    
    # 停止服务
    pkill -f "uvicorn" || true
    pkill -f "trading_monitor" || true
    
    # 回滚代码
    git reset --hard $commit_hash
    
    # 重新部署
    install_dependencies
    start_services "production"
    health_check
    
    log "回滚完成，当前版本: $(git log -1 --pretty=%H)"
}

# 主函数
main() {
    local command="deploy"
    
    if [ $# -gt 0 ]; then
        case $1 in
            deploy|rollback)
                command=$1
                shift
                ;;
            *)
                # 默认部署
                ;;
        esac
    fi
    
    case $command in
        deploy)
            deploy "$@"
            ;;
        rollback)
            rollback "$@"
            ;;
        *)
            usage
            ;;
    esac
}

# 执行主函数
main "$@"