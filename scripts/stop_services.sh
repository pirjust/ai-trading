#!/bin/bash

# AI量化交易系统停止脚本
# 适用于宝塔面板部署

echo "停止AI量化交易系统..."

# 检查PID文件目录
if [ ! -d "data/pids" ]; then
    echo "错误: PID文件目录不存在"
    exit 1
fi

# 停止后端服务
if [ -f "data/pids/backend.pid" ]; then
    BACKEND_PID=$(cat data/pids/backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "✓ 后端API服务已停止"
    else
        echo "后端API服务未运行"
    fi
    rm data/pids/backend.pid
fi

# 停止数据采集服务
if [ -f "data/pids/collector.pid" ]; then
    COLLECTOR_PID=$(cat data/pids/collector.pid)
    if ps -p $COLLECTOR_PID > /dev/null; then
        kill $COLLECTOR_PID
        echo "✓ 数据采集服务已停止"
    else
        echo "数据采集服务未运行"
    fi
    rm data/pids/collector.pid
fi

# 停止监控服务
if [ -f "data/pids/monitor.pid" ]; then
    MONITOR_PID=$(cat data/pids/monitor.pid)
    if ps -p $MONITOR_PID > /dev/null; then
        kill $MONITOR_PID
        echo "✓ 监控服务已停止"
    else
        echo "监控服务未运行"
    fi
    rm data/pids/monitor.pid
fi

echo "系统停止完成！"

# 清理临时文件
rm -f data/pids/*.pid