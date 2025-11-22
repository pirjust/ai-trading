-- AI量化交易系统数据库初始化脚本
-- 创建数据库表结构和初始数据

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 交易所表
CREATE TABLE IF NOT EXISTS exchanges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 账户表
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('spot', 'contract', 'option')),
    balance DECIMAL(20,8) DEFAULT 0.0,
    available_balance DECIMAL(20,8) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_user_exchange_account UNIQUE (user_id, exchange_id, account_type)
);

-- 策略表
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL CHECK (strategy_type IN ('technical', 'ml', 'rl', 'hybrid')),
    parameters JSONB,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 交易记录表
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    price DECIMAL(20,8) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) DEFAULT 0.0,
    profit_loss DECIMAL(20,8) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'cancelled', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 风险警报表
CREATE TABLE IF NOT EXISTS risk_alerts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(20,8) NOT NULL,
    period VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(10) NOT NULL CHECK (log_level IN ('debug', 'info', 'warning', 'error', 'critical')),
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    extra_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引以优化查询性能

-- 用户相关索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 账户相关索引
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_exchange_id ON accounts(exchange_id);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_accounts_created_at ON accounts(created_at);

-- 交易相关索引
CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_created_at ON trades(symbol, created_at);

-- 风险警报相关索引
CREATE INDEX IF NOT EXISTS idx_risk_alerts_account_id ON risk_alerts(account_id);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_severity ON risk_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_is_resolved ON risk_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_created_at ON risk_alerts(created_at);

-- 性能指标相关索引
CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_id ON performance_metrics(strategy_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(period);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_calculated_at ON performance_metrics(calculated_at);

-- 系统日志相关索引
CREATE INDEX IF NOT EXISTS idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- 创建分区表（可选，用于大数据量优化）
-- CREATE TABLE trades_2024 PARTITION OF trades FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 创建更新时间的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据
INSERT INTO users (username, email, hashed_password, is_superuser) VALUES
('admin', 'admin@ai-trading.com', 'hashed_password_placeholder', true),
('trader1', 'trader1@ai-trading.com', 'hashed_password_placeholder', false),
('trader2', 'trader2@ai-trading.com', 'hashed_password_placeholder', false)
ON CONFLICT (username) DO NOTHING;

INSERT INTO exchanges (name, api_key, api_secret) VALUES
('binance', 'your_binance_api_key', 'your_binance_secret'),
('okx', 'your_okx_api_key', 'your_okx_secret'),
('bybit', 'your_bybit_api_key', 'your_bybit_secret')
ON CONFLICT (name) DO NOTHING;

INSERT INTO strategies (name, description, strategy_type, parameters, is_active) VALUES
('MA_Crossover', '移动平均线交叉策略', 'technical', '{"fast_period": 10, "slow_period": 30}', true),
('RSI_Strategy', 'RSI超买超卖策略', 'technical', '{"rsi_period": 14, "overbought": 70, "oversold": 30}', true),
('ML_Predictor', '机器学习价格预测策略', 'ml', '{"model_type": "xgboost", "training_period": 1000}', false)
ON CONFLICT (name) DO NOTHING;

-- 创建数据库函数
CREATE OR REPLACE FUNCTION calculate_daily_profit_loss(account_id INTEGER, target_date DATE)
RETURNS DECIMAL(20,8) AS $$
DECLARE
    total_pl DECIMAL(20,8);
BEGIN
    SELECT COALESCE(SUM(profit_loss), 0)
    INTO total_pl
    FROM trades
    WHERE account_id = $1
    AND DATE(created_at) = $2
    AND status = 'completed';
    
    RETURN total_pl;
END;
$$ LANGUAGE plpgsql;

-- 创建视图以便于查询
CREATE OR REPLACE VIEW daily_trading_summary AS
SELECT 
    a.id as account_id,
    u.username,
    e.name as exchange_name,
    a.account_type,
    DATE(t.created_at) as trade_date,
    COUNT(t.id) as trade_count,
    SUM(t.amount * t.price) as trade_volume,
    SUM(t.profit_loss) as total_profit_loss
FROM accounts a
JOIN users u ON a.user_id = u.id
JOIN exchanges e ON a.exchange_id = e.id
LEFT JOIN trades t ON a.id = t.account_id AND t.status = 'completed'
GROUP BY a.id, u.username, e.name, a.account_type, DATE(t.created_at);

-- 输出创建结果
SELECT '数据库初始化完成' as result;