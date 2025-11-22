-- Exchange configuration tables
-- Version: 20240101000001
-- Description: 创建交易所配置和交易对表

-- 交易所配置表
CREATE TABLE IF NOT EXISTS exchanges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    api_key VARCHAR(255),
    secret_key VARCHAR(255),
    sandbox BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'testing')),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 交易对表
CREATE TABLE IF NOT EXISTS trading_pairs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    base_currency VARCHAR(10) NOT NULL,
    quote_currency VARCHAR(10) NOT NULL,
    exchange_id UUID REFERENCES exchanges(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'delisted')),
    min_amount DECIMAL(20,10) DEFAULT 0,
    max_amount DECIMAL(20,10),
    price_precision INTEGER DEFAULT 8,
    amount_precision INTEGER DEFAULT 8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_exchanges_user_id ON exchanges(user_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_code ON exchanges(code);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_symbol ON trading_pairs(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_exchange_id ON trading_pairs(exchange_id);

-- 为交易所表创建更新时间触发器
CREATE TRIGGER update_exchanges_updated_at 
    BEFORE UPDATE ON exchanges 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为交易对表创建更新时间触发器
CREATE TRIGGER update_trading_pairs_updated_at 
    BEFORE UPDATE ON trading_pairs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 插入支持的交易所配置
INSERT INTO exchanges (name, code, sandbox, status) VALUES
('币安', 'binance', TRUE, 'active'),
('欧易', 'okex', TRUE, 'active'),
('火币', 'huobi', TRUE, 'active'),
('Coinbase', 'coinbase', TRUE, 'active')
ON CONFLICT (code) DO NOTHING;

-- 插入常见交易对
WITH exchange_ids AS (
    SELECT id, code FROM exchanges
)
INSERT INTO trading_pairs (symbol, base_currency, quote_currency, exchange_id, min_amount, price_precision, amount_precision) VALUES
('BTC/USDT', 'BTC', 'USDT', (SELECT id FROM exchange_ids WHERE code = 'binance'), 0.0001, 2, 6),
('ETH/USDT', 'ETH', 'USDT', (SELECT id FROM exchange_ids WHERE code = 'binance'), 0.001, 2, 5),
('BNB/USDT', 'BNB', 'USDT', (SELECT id FROM exchange_ids WHERE code = 'binance'), 0.1, 4, 2),
('ADA/USDT', 'ADA', 'USDT', (SELECT id FROM exchange_ids WHERE code = 'binance'), 1, 5, 1),
('DOT/USDT', 'DOT', 'USDT', (SELECT id FROM exchange_ids WHERE code = 'binance'), 0.1, 3, 2)
ON CONFLICT (symbol, exchange_id) DO NOTHING;