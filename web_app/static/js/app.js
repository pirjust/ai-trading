// AI量化交易系统前端JavaScript

class TradingApp {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.wsUrl = 'ws://localhost:8000/ws';
        this.websocket = null;
        this.charts = {};
        this.init();
    }

    async init() {
        console.log('AI量化交易系统初始化...');
        
        // 初始化WebSocket连接
        this.initWebSocket();
        
        // 初始化图表
        this.initCharts();
        
        // 加载初始数据
        await this.loadDashboardData();
        
        // 设置定时刷新
        this.setupAutoRefresh();
        
        console.log('系统初始化完成');
    }

    initWebSocket() {
        try {
            this.websocket = new WebSocket(this.wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                this.showNotification('实时连接已建立', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket连接已关闭');
                this.showNotification('实时连接已断开', 'warning');
                // 尝试重连
                setTimeout(() => this.initWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
            };
            
        } catch (error) {
            console.error('WebSocket初始化失败:', error);
        }
    }

    handleWebSocketMessage(data) {
        const { type, payload } = data;
        
        switch (type) {
            case 'price_update':
                this.updatePriceDisplay(payload);
                break;
            case 'trade_executed':
                this.showTradeNotification(payload);
                break;
            case 'strategy_update':
                this.updateStrategyStatus(payload);
                break;
            case 'risk_alert':
                this.showRiskAlert(payload);
                break;
            default:
                console.log('未知消息类型:', type);
        }
    }

    initCharts() {
        // 初始化资金曲线图
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '资金曲线',
                        data: [],
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#94a3b8'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
        }

        // 初始化资产分布图
        const distributionCtx = document.getElementById('distributionChart');
        if (distributionCtx) {
            this.charts.distribution = new Chart(distributionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['BTC', 'ETH', 'USDT', '其他'],
                    datasets: [{
                        data: [40, 25, 20, 15],
                        backgroundColor: [
                            '#f59e0b',
                            '#8b5cf6',
                            '#10b981',
                            '#6b7280'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
        }
    }

    async loadDashboardData() {
        try {
            // 加载资金数据
            const fundsResponse = await this.apiCall('/accounts/balance/1');
            this.updateFundsDisplay(fundsResponse);
            
            // 加载策略数据
            const strategiesResponse = await this.apiCall('/strategies/');
            this.updateStrategiesDisplay(strategiesResponse);
            
            // 加载风险数据
            const riskResponse = await this.apiCall('/risk/metrics');
            this.updateRiskDisplay(riskResponse);
            
        } catch (error) {
            console.error('加载数据失败:', error);
            this.showNotification('数据加载失败', 'error');
        }
    }

    updateFundsDisplay(data) {
        const totalElement = document.querySelector('.funds-overview .stat-value');
        const dailyElement = document.querySelector('.funds-overview .stat-value.positive');
        const monthlyElement = document.querySelector('.funds-overview .stat-value:nth-child(3)');
        
        if (totalElement) {
            totalElement.textContent = `$${data.total_balance?.toLocaleString() || '0'}`;
        }
        
        if (dailyElement) {
            dailyElement.textContent = `+$${data.daily_profit?.toLocaleString() || '0'}`;
        }
        
        if (monthlyElement) {
            monthlyElement.textContent = `+${data.monthly_return?.toFixed(2) || '0'}%`;
        }
    }

    updateStrategiesDisplay(strategies) {
        const strategyList = document.querySelector('.strategy-list');
        if (!strategyList) return;
        
        strategyList.innerHTML = '';
        
        strategies.forEach(strategy => {
            const strategyElement = document.createElement('div');
            strategyElement.className = `strategy-item ${strategy.status === 'active' ? 'active' : 'paused'}`;
            
            strategyElement.innerHTML = `
                <span class="strategy-name">${strategy.name}</span>
                <span class="strategy-status">${this.getStatusText(strategy.status)}</span>
                <span class="strategy-profit ${strategy.performance?.profit > 0 ? 'positive' : 'negative'}">
                    ${strategy.performance?.profit > 0 ? '+' : ''}${strategy.performance?.profit?.toFixed(2) || '0.00'}%
                </span>
            `;
            
            strategyList.appendChild(strategyElement);
        });
    }

    updateRiskDisplay(riskData) {
        const riskItems = document.querySelectorAll('.risk-item .risk-value');
        
        if (riskItems[0]) {
            riskItems[0].textContent = `$${riskData.var?.toLocaleString() || '0'}`;
        }
        
        if (riskItems[1]) {
            riskItems[1].textContent = `${riskData.max_drawdown?.toFixed(2) || '0.00'}%`;
        }
        
        if (riskItems[2]) {
            riskItems[2].textContent = riskData.sharpe_ratio?.toFixed(2) || '0.00';
            riskItems[2].className = `risk-value ${riskData.sharpe_ratio > 1 ? 'positive' : ''}`;
        }
    }

    updatePriceDisplay(priceData) {
        const priceItems = document.querySelectorAll('.price-item');
        
        priceItems.forEach(item => {
            const symbol = item.querySelector('.symbol').textContent;
            const priceElement = item.querySelector('.price');
            const changeElement = item.querySelector('.change');
            
            if (priceData[symbol]) {
                const { price, change } = priceData[symbol];
                
                priceElement.textContent = `$${price.toLocaleString()}`;
                changeElement.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
                changeElement.className = `change ${change > 0 ? 'positive' : 'negative'}`;
                
                // 添加价格变动动画
                item.classList.add('price-update');
                setTimeout(() => item.classList.remove('price-update'), 500);
            }
        });
    }

    showTradeNotification(trade) {
        this.showNotification(
            `交易执行: ${trade.symbol} ${trade.side.toUpperCase()} ${trade.quantity} @ $${trade.price}`,
            'info'
        );
    }

    showRiskAlert(alert) {
        this.showNotification(
            `风险警报: ${alert.message}`,
            'warning'
        );
    }

    getStatusText(status) {
        const statusMap = {
            'active': '运行中',
            'inactive': '已停止',
            'paused': '暂停'
        };
        return statusMap[status] || status;
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API调用失败:', error);
            throw error;
        }
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close">×</button>
        `;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 自动隐藏
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // 关闭按钮
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    setupAutoRefresh() {
        // 每30秒刷新一次数据
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.tradingApp = new TradingApp();
});

// 添加通知样式
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 1rem;
    min-width: 300px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    animation: slideInRight 0.3s ease-out;
}

.notification.success {
    border-left: 4px solid #10b981;
}

.notification.warning {
    border-left: 4px solid #f59e0b;
}

.notification.error {
    border-left: 4px solid #ef4444;
}

.notification.info {
    border-left: 4px solid #60a5fa;
}

.notification.fade-out {
    animation: fadeOutRight 0.3s ease-in;
}

.notification-message {
    color: #e2e8f0;
    margin-right: 1rem;
}

.notification-close {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.25rem;
    cursor: pointer;
    float: right;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes fadeOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.price-update {
    background-color: rgba(96, 165, 250, 0.2) !important;
    transition: background-color 0.5s ease;
}
`;

// 注入样式
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);