#!/bin/bash

# AI量化交易系统停止脚本

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

# 停止服务
stop_services() {
    log_info "正在停止AI量化交易系统..."
    
    # 停止后端服务
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            log_info "停止后端服务 (PID: $BACKEND_PID)"
            kill $BACKEND_PID
            
            # 等待进程结束
            sleep 3
            if ps -p $BACKEND_PID > /dev/null 2>&1; then
                log_warning "强制停止后端服务"
                kill -9 $BACKEND_PID
            fi
        else
            log_warning "后端服务未运行"
        fi
        rm -f .backend.pid
    else
        log_info "未找到后端服务PID文件"
    fi
    
    # 停止前端服务
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            log_info "停止前端服务 (PID: $FRONTEND_PID)"
            kill $FRONTEND_PID
            
            # 等待进程结束
            sleep 3
            if ps -p $FRONTEND_PID > /dev/null 2>&1; then
                log_warning "强制停止前端服务"
                kill -9 $FRONTEND_PID
            fi
        else
            log_warning "前端服务未运行"
        fi
        rm -f .frontend.pid
    else
        log_info "未找到前端服务PID文件"
    fi
    
    # 停止Docker服务
    if [ -f "docker-compose.yml" ]; then
        log_info "停止Docker服务..."
        docker-compose down 2>/dev/null || log_warning "Docker服务未运行"
    fi
    
    # 停止其他可能的服务
    log_info "停止其他相关进程..."
    
    # 停止可能的Python进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "node.*dev" 2>/dev/null || true
    
    log_success "所有服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理临时资源..."
    
    # 清理临时文件
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 清理可能的锁定文件
    rm -f ./*.lock 2>/dev/null || true
    
    log_success "资源清理完成"
}

# 显示停止信息
show_stop_info() {
    echo ""
    echo "=================================="
    echo "🛑 AI量化交易系统已停止"
    echo "=================================="
    echo ""
    echo "📋 服务状态:"
    echo "  - 后端服务: 已停止"
    echo "  - 前端服务: 已停止"
    echo "  - Docker服务: 已停止"
    echo ""
    echo "📝 日志文件保留在 logs/ 目录"
    echo "🔄 重启服务: ./scripts/start_system.sh"
    echo ""
}

# 主函数
main() {
    echo "=================================="
    echo "🛑 停止AI量化交易系统"
    echo "=================================="
    echo ""
    
    stop_services
    cleanup
    show_stop_info
}

# 运行主函数
main "$@"