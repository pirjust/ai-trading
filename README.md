# AI量化加密货币交易系统

一个基于深度学习和强化学习的智能加密货币交易系统，支持多交易所API集成、实时风控、AI策略引擎和完整的监控体系。

## 🚀 核心功能

### 🤖 AI策略引擎
- **深度学习模型**: Transformer、CNN-LSTM、变分自编码器
- **机器学习**: 随机森林、梯度提升、LSTM预测
- **强化学习**: DQN智能体，支持自定义奖励函数
- **技术分析**: 移动平均、RSI、MACD、布林带等经典指标

### 🏢 多交易所集成
- **币安(Binance)**: 完整的现货和期货API支持
- **欧意(OKX)**: 支持现货、期货、期权交易
- **统一接口**: 抽象化的交易所客户端，便于扩展
- **实时数据**: WebSocket实时价格和深度数据

### 🛡️ 风险管理
- **实时风控**: VaR计算、最大回撤监控、夏普比率
- **智能止损**: 动态止损策略，基于波动率调整
- **仓位管理**: 自动化仓位分配和风险敞口控制
- **合规监控**: 多层级风险警报和合规检查

### 📊 监控运维
- **系统监控**: CPU、内存、磁盘、网络实时监控
- **交易监控**: 实时交易状态、盈亏统计、性能指标
- **告警系统**: 多渠道告警，支持邮件、Webhook、Slack
- **可视化**: Grafana仪表板，专业交易分析图表

### 🎯 智能回测
- **历史回测**: 支持多种数据源和复杂交易逻辑
- **参数优化**: 网格搜索、贝叶斯优化
- **性能评估**: 完整的风险调整后收益指标
- **Walk-Forward**: 避免过拟合的滚动窗口优化

## 📁 项目结构

```
ai-trading/
├── ai_engine/              # AI策略引擎
│   ├── deep_learning_models.py    # 深度学习模型
│   ├── model_trainer.py          # 模型训练器
│   ├── rl_environment.py         # 强化学习环境
│   ├── feature_engineering.py     # 特征工程
│   └── backtesting.py           # 回测引擎
├── strategies/             # 交易策略
│   ├── base_strategy.py          # 策略基类
│   ├── technical_strategies.py    # 技术分析策略
│   ├── ai_strategies.py          # AI策略
│   └── base_strategy.py          # 基础策略
├── data/                  # 数据采集
│   ├── exchange_client.py       # 交易所客户端
│   ├── binance_api.py          # 币安API
│   ├── okx_api.py              # 欧意API
│   ├── websocket_collector.py   # WebSocket数据采集
│   └── rest_collector.py       # REST API采集
├── risk_management/       # 风险管理
│   ├── risk_engine.py          # 风控引擎
│   ├── risk_monitor.py         # 风险监控
│   └── risk_reporter.py       # 风险报告
├── monitoring/            # 监控系统
│   ├── system_monitor.py       # 系统监控
│   ├── trading_monitor.py      # 交易监控
│   └── prometheus_client.py    # Prometheus客户端
├── agents/                # 智能代理
│   ├── strategy_manager.py     # 策略管理器
│   └── account_manager.py     # 账户管理器
├── app/                   # Web应用
│   ├── api/                 # API接口
│   ├── models/              # 数据模型
│   └── main.py              # 应用入口
├── frontend/               # 前端界面
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   └── hooks/          # React Hooks
│   └── package.json
├── config/                # 配置文件
│   ├── exchanges.py        # 交易所配置
│   ├── api_config.py       # API配置
│   └── trading_config.py   # 交易配置
├── deploy/                # 部署配置
│   ├── nginx.conf           # Nginx配置
│   ├── prometheus.yml      # Prometheus配置
│   └── grafana/            # Grafana配置
└── scripts/               # 脚本工具
    ├── deploy.py           # 部署脚本
    ├── backup.py           # 备份脚本
    └── start_services.sh    # 启动脚本
```

## 🛠️ 技术栈

### 后端技术
- **Python 3.9+**: 主要开发语言
- **FastAPI**: 高性能Web框架
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话存储
- **InfluxDB**: 时序数据存储
- **Celery**: 异步任务队列
- **Prometheus**: 监控数据收集
- **Grafana**: 数据可视化

### AI/ML技术
- **PyTorch**: 深度学习框架
- **scikit-learn**: 机器学习库
- **TensorFlow**: 备选深度学习框架
- **Gymnasium**: 强化学习环境
- **Stable Baselines3**: 强化学习算法
- **TA-Lib**: 技术分析库
- **pandas-ta**: 技术指标库

### 前端技术
- **React 18**: 前端框架
- **TypeScript**: 类型安全的JavaScript
- **Vite**: 构建工具
- **Tailwind CSS**: 样式框架
- **Shadcn/ui**: UI组件库
- **Recharts**: 图表库
- **WebSocket**: 实时通信

### 部署技术
- **Docker**: 容器化部署
- **Docker Compose**: 多容器编排
- **Nginx**: 反向代理和负载均衡
- **宝塔面板**: 服务器管理
- **Prometheus + Grafana**: 监控栈

## 📋 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL 13+
- Redis 6+

### 1. 克隆项目
```bash
git clone <repository-url>
cd ai-trading
```

### 2. 后端设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥等信息

# 初始化数据库
python scripts/init_database.py

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

### 4. Docker部署
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 宝塔面板部署
```bash
# 运行一键部署脚本
chmod +x scripts/bt_panel_deploy.sh
./scripts/bt_panel_deploy.sh
```

## 🔧 配置说明

### API密钥配置
在 `.env` 文件中配置交易所API密钥：

```env
# 币安API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# 欧意API
OKX_API_KEY=your_okx_api_key
OKX_API_SECRET=your_okx_api_secret
OKX_PASSPHRASE=your_okx_passphrase

# 其他配置
DB_PASSWORD=your_database_password
REDIS_PASSWORD=your_redis_password
```

### 策略配置
策略配置通过Web界面或API进行设置：

```python
# 示例：移动平均策略配置
strategy_config = {
    'symbol': 'BTCUSDT',
    'quantity': 0.001,
    'short_period': 10,
    'long_period': 30,
    'confidence_threshold': 0.7
}
```

### 风控配置
```python
# 风险管理配置
risk_config = {
    'max_position_size': 0.1,      # 最大仓位比例
    'max_daily_loss': 0.05,       # 最大日损失比例
    'max_drawdown': 0.15,         # 最大回撤比例
    'var_threshold': 0.03         # VaR阈值
}
```

## 📊 监控和运维

### 系统监控
- **Prometheus**: 指标收集 (http://localhost:9090)
- **Grafana**: 数据可视化 (http://localhost:3000)
- **健康检查**: API健康状态检查

### 日志管理
- **结构化日志**: 使用structlog进行日志记录
- **日志级别**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **日志轮转**: 自动轮转和压缩历史日志

### 告警系统
- **多级告警**: 低、中、高、严重四个级别
- **多渠道通知**: 邮件、Webhook、Slack集成
- **智能过滤**: 避免告警风暴

## 🧪 测试

### 运行系统测试
```bash
# 运行集成测试
python test_system_integration.py

# 运行单元测试
pytest tests/

# 生成测试覆盖率报告
pytest --cov=app tests/
```

### 性能测试
```bash
# API性能测试
python scripts/api_performance_test.py

# 回测性能测试
python scripts/backtest_performance_test.py
```

## 📖 API文档

### 交易API
- `GET /api/trading/market/{symbol}` - 获取市场数据
- `GET /api/trading/positions` - 获取持仓信息
- `POST /api/trading/orders` - 创建订单
- `GET /api/trading/balances` - 获取账户余额

### 策略API
- `GET /api/strategies` - 获取策略列表
- `POST /api/strategies` - 创建策略
- `POST /api/strategies/{id}/start` - 启动策略
- `GET /api/strategies/{id}/performance` - 获取策略性能

### 监控API
- `GET /api/monitoring/health` - 系统健康状态
- `GET /api/monitoring/alerts` - 获取风险警报
- `GET /api/monitoring/system-metrics` - 系统指标

## 🔒 安全考虑

### API安全
- **JWT认证**: 基于Token的身份验证
- **权限控制**: 细粒度的访问控制
- **速率限制**: API调用频率限制
- **输入验证**: 严格的输入数据验证

### 交易安全
- **仓位限制**: 单策略最大仓位限制
- **止损机制**: 强制性止损保护
- **资金安全**: 多重签名和资金隔离
- **审计日志**: 完整的交易和操作日志

### 数据安全
- **数据加密**: 敏感数据加密存储
- **备份恢复**: 自动化数据备份
- **访问控制**: 数据库访问权限控制
- **传输安全**: HTTPS/WSS加密传输

## 🚀 性能优化

### 系统性能
- **异步处理**: 基于asyncio的高并发处理
- **连接池**: 数据库连接池优化
- **缓存策略**: 多层缓存提升响应速度
- **负载均衡**: 支持多实例负载均衡

### 交易性能
- **智能路由**: 最优交易所选择
- **批量操作**: 批量下单和取消订单
- **本地缓存**: 实时数据本地缓存
- **预计算**: 常用指标预计算

## 📈 扩展开发

### 添加新交易所
1. 在 `data/` 目录下创建新的交易所API模块
2. 实现 `BaseExchangeClient` 接口
3. 在 `ExchangeClientFactory` 中注册新交易所
4. 添加相应的配置和测试

### 添加新策略
1. 继承 `BaseStrategy` 基类
2. 实现 `initialize()`, `generate_signal()`, `execute_strategy()` 方法
3. 在策略工厂中注册新策略类型
4. 添加策略配置模板

### 添加新指标
1. 在特征工程模块中添加指标计算函数
2. 更新模型训练器的特征创建逻辑
3. 在监控面板中添加指标可视化
4. 更新风险评估逻辑

## 🤝 贡献指南

### 开发规范
- **代码风格**: 遵循PEP 8和项目代码规范
- **提交规范**: 使用约定式提交信息格式
- **测试覆盖**: 新功能必须包含测试用例
- **文档更新**: 重要变更需更新相关文档

### 提交流程
1. Fork项目到个人仓库
2. 创建功能分支进行开发
3. 编写测试并确保通过
4. 提交Pull Request并描述变更
5. 代码审查通过后合并到主分支

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## ⚠️ 风险提示

**重要声明**: 
- 本项目仅供学习和研究使用
- 加密货币交易具有极高风险，可能导致资金损失
- 请在充分了解风险的情况下谨慎使用
- 建议先在模拟环境中充分测试
- 开发者不对任何交易损失承担责任

## 📞 支持

- **问题反馈**: 通过GitHub Issues提交问题
- **功能建议**: 欢迎提交Feature Request
- **技术支持**: 查看文档和Wiki获取更多信息
- **社区交流**: 加入开发者社区讨论

---

**免责声明**: 本软件仅供教育和研究目的使用。加密货币交易涉及高风险，可能导致资金损失。用户应充分了解相关风险，并在风险承受范围内谨慎使用。开发者不对使用本软件造成的任何损失承担责任。