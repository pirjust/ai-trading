-- AI量化交易系统数据库初始化脚本
-- 创建数据库表结构和初始数据

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_trading;

-- 切换到ai_trading数据库
\c ai_trading;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE,
    secret_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易所配置表
CREATE TABLE IF NOT EXISTS exchange_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    exchange_name VARCHAR(50) NOT NULL,
    api_key VARCHAR(255),
    secret_key VARCHAR(255),
    passphrase VARCHAR(255),
    sandbox BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易策略表
CREATE TABLE IF NOT EXISTS trading_strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建交易对配置表
CREATE TABLE IF NOT EXISTS trading_pairs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    min_notional DECIMAL(20,10),
    min_price DECIMAL(20,10),
    max_price DECIMAL(20,10),
    tick_size DECIMAL(20,10),
    step_size DECIMAL(20,10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol)
);

-- 创建交易记录表
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_id INTEGER REFERENCES trading_strategies(id),
    exchange_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    price DECIMAL(20,10) NOT NULL,
    quantity DECIMAL(20,10) NOT NULL,
    total DECIMAL(20,10) NOT NULL,
    fee DECIMAL(20,10) DEFAULT 0,
    fee_currency VARCHAR(10),
    status VARCHAR(20) DEFAULT 'filled',
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建价格数据表
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20,10) NOT NULL,
    high DECIMAL(20,10) NOT NULL,
    low DECIMAL(20,10) NOT NULL,
    close DECIMAL(20,10) NOT NULL,
    volume DECIMAL(20,10) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建风险评估表
CREATE TABLE IF NOT EXISTS risk_assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    assessment_date DATE NOT NULL,
    risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    assessment_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建系统监控表
CREATE TABLE IF NOT EXISTS system_monitoring (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(20,10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);

CREATE INDEX IF NOT EXISTS idx_price_data_symbol ON price_data(symbol);
CREATE INDEX IF NOT EXISTS idx_price_data_timestamp ON price_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_price_data_interval ON price_data(interval);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_user_id ON risk_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_date ON risk_assessments(assessment_date);

CREATE INDEX IF NOT EXISTS idx_system_monitoring_metric ON system_monitoring(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_monitoring_timestamp ON system_monitoring(timestamp);

-- 插入初始数据
-- 默认管理员用户
INSERT INTO users (username, email, password_hash, is_active) VALUES 
('admin', 'admin@ai-trading.com', '$2b$12$examplehash', TRUE)
ON CONFLICT (username) DO NOTHING;

-- 常用交易对
INSERT INTO trading_pairs (symbol, base_currency, quote_currency, is_active) VALUES 
('BTC/USDT', 'BTC', 'USDT', TRUE),
('ETH/USDT', 'ETH', 'USDT', TRUE),
('BNB/USDT', 'BNB', 'USDT', TRUE),
('ADA/USDT', 'ADA', 'USDT', TRUE),
('DOT/USDT', 'DOT', 'USDT', TRUE),
('LINK/USDT', 'LINK', 'USDT', TRUE),
('LTC/USDT', 'LTC', 'USDT', TRUE),
('BCH/USDT', 'BCH', 'USDT', TRUE),
('XRP/USDT', 'XRP', 'USDT', TRUE),
('EOS/USDT', 'EOS', 'USDT', TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- 创建视图用于报表
CREATE OR REPLACE VIEW daily_trading_summary AS
SELECT 
    DATE(created_at) as trade_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0 END) as buy_volume,
    SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0 END) as sell_volume,
    AVG(price) as avg_price,
    SUM(total) as total_volume
FROM trades 
WHERE status = 'filled'
GROUP BY DATE(created_at);

-- 创建函数更新更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要更新时间戳的表创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exchange_configs_updated_at BEFORE UPDATE ON exchange_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_strategies_updated_at BEFORE UPDATE ON trading_strategies FOR Each ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建分区表用于价格数据（按月份分区）
CREATE TABLE IF NOT EXISTS price_data_partitioned (
    LIKE price_data INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- 创建默认分区
CREATE TABLE IF NOT EXISTS price_data_default PARTITION OF price_data_partitioned 
DEFAULT;

-- 授予权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_trader;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_trader;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ai_trader;

-- 创建只读用户用于监控
CREATE USER IF NOT EXISTS ai_monitor WITH PASSWORD 'monitor_password_123';
GRANT CONNECT ON DATABASE ai_trading TO ai_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_monitor;

-- 设置搜索路径
ALTER DATABASE ai_trading SET search_path TO public;

-- 输出完成信息
\echo '✅ 数据库初始化完成'
\echo '📊 已创建的表结构:'
\dt
\echo '🔑 用户权限已设置:'
\echo '   - ai_trader: 读写权限'
\echo '   - ai_monitor: 只读权限'
\echo '🚀 数据库初始化脚本执行完毕'