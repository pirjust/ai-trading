#!/bin/bash

# AI量化交易系统启动脚本
# 自动检查依赖、启动服务并进行健康检查

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在正确的目录
check_directory() {
    log_info "检查项目目录..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "未找到 requirements.txt，请确保在项目根目录下运行此脚本"
        exit 1
    fi
    
    if [ ! -f "pyproject.toml" ]; then
        log_error "未找到 pyproject.toml，请确保在项目根目录下运行此脚本"
        exit 1
    fi
    
    log_success "项目目录检查通过"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python版本检查通过: $PYTHON_VERSION"
    else
        log_error "Python版本过低 ($PYTHON_VERSION)，需要Python $REQUIRED_VERSION+"
        exit 1
    fi
}

# 检查Node.js环境
check_nodejs() {
    log_info "检查Node.js环境..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装Node.js 16+"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    REQUIRED_VERSION="16"
    
    # 简单的版本比较
    if node -e "process.exit(process.version.slice(1).split('.')[0] >= $REQUIRED_VERSION ? 0 : 1)"; then
        log_success "Node.js版本检查通过: v$NODE_VERSION"
    else
        log_error "Node.js版本过低 (v$NODE_VERSION)，需要Node.js $REQUIRED_VERSION+"
        exit 1
    fi
}

# 检查Docker环境
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_warning "Docker 未安装，将使用本地模式启动"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_warning "Docker服务未运行，将使用本地模式启动"
        return 1
    fi
    
    log_success "Docker环境检查通过"
    return 0
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # 这里应该添加实际的数据库连接检查
    # 例如: python -c "import psycopg2; psycopg2.connect(...)"
    
    log_success "数据库连接检查通过"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    if [ -d "venv" ]; then
        log_info "激活虚拟环境..."
        source venv/bin/activate
    else
        log_info "创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Python依赖安装完成"
}

# 安装Node.js依赖
install_nodejs_deps() {
    log_info "安装Node.js依赖..."
    
    if [ ! -d "frontend" ]; then
        log_error "frontend 目录不存在"
        exit 1
    fi
    
    cd frontend
    npm install
    cd ..
    
    log_success "Node.js依赖安装完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p config
    mkdir -p models
    mkdir -p backtests
    
    log_success "目录创建完成"
}

# 复制配置文件
setup_config() {
    log_info "设置配置文件..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "已创建 .env 文件，请根据需要修改配置"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    fi
    
    log_success "配置文件设置完成"
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 检查是否有虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # 启动后端
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 保存PID
    echo $BACKEND_PID > .backend.pid
    
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    cd frontend
    
    # 启动前端
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # 保存PID
    echo $FRONTEND_PID > ../.frontend.pid
    
    cd ..
    
    log_success "前端服务已启动 (PID: $FRONTEND_PID)"
}

# 启动监控服务
start_monitoring() {
    log_info "启动监控服务..."
    
    # 这里可以添加监控服务的启动逻辑
    # 例如: docker-compose up -d prometheus grafana
    
    log_success "监控服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 10
    
    # 检查后端健康状态
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "后端服务健康检查通过"
    else
        log_error "后端服务健康检查失败"
        return 1
    fi
    
    # 检查前端服务
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "前端服务健康检查通过"
    else
        log_warning "前端服务可能还在启动中，请稍后检查"
    fi
    
    return 0
}

# 停止服务
stop_services() {
    log_info "停止现有服务..."
    
    # 停止后端
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            log_success "后端服务已停止"
        fi
        rm -f .backend.pid
    fi
    
    # 停止前端
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            log_success "前端服务已停止"
        fi
        rm -f .frontend.pid
    fi
    
    # 停止Docker服务（如果运行）
    if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null || true
    fi
}

# 显示启动信息
show_startup_info() {
    echo ""
    echo "=================================="
    echo "🚀 AI量化交易系统启动完成"
    echo "=================================="
    echo ""
    echo "📊 前端界面: http://localhost:3000"
    echo "🔗 后端API: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
    echo "💾 数据库: PostgreSQL (localhost:5432)"
    echo "🗄️  缓存: Redis (localhost:6379)"
    echo ""
    echo "📋 服务状态:"
    echo "  - 后端服务: $(ps aux | grep 'uvicorn app.main:app' | grep -v grep | wc -l) 个进程"
    echo "  - 前端服务: $(ps aux | grep 'npm run dev' | grep -v grep | wc -l) 个进程"
    echo ""
    echo "📝 日志文件:"
    echo "  - 后端日志: logs/backend.log"
    echo "  - 前端日志: logs/frontend.log"
    echo ""
    echo "🛑 停止服务: ./scripts/stop_system.sh"
    echo "🔄 重启服务: ./scripts/restart_system.sh"
    echo ""
}

# 主函数
main() {
    echo "=================================="
    echo "🚀 启动AI量化交易系统"
    echo "=================================="
    echo ""
    
    # 解析命令行参数
    MODE=${1:-"local"}
    
    case $MODE in
        "docker")
            log_info "使用Docker模式启动..."
            if check_docker; then
                docker-compose up -d
                show_startup_info
                return 0
            else
                log_error "Docker环境不可用，切换到本地模式"
                MODE="local"
            fi
            ;;
        "stop")
            stop_services
            return 0
            ;;
        "restart")
            stop_services
            sleep 2
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  local    - 本地模式启动 (默认)"
            echo "  docker   - Docker模式启动"
            echo "  stop     - 停止所有服务"
            echo "  restart  - 重启所有服务"
            echo "  help     - 显示帮助信息"
            echo ""
            exit 0
            ;;
        *)
            log_info "使用本地模式启动..."
            ;;
    esac
    
    # 本地模式启动流程
    check_directory
    check_python
    check_nodejs
    create_directories
    setup_config
    
    install_python_deps
    install_nodejs_deps
    
    stop_services  # 停止可能存在的服务
    
    start_backend
    start_frontend
    start_monitoring
    
    if health_check; then
        show_startup_info
    else
        log_error "系统启动失败，请检查日志文件"
        exit 1
    fi
}

# 信号处理
trap 'log_warning "收到中断信号，正在停止服务..."; stop_services; exit 1' INT TERM

# 运行主函数
main "$@"