-- Initial database schema for AI Trading System
-- Version: 20240101000000
-- Description: 创建基础用户和系统配置表

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'trader' CHECK (role IN ('admin', 'trader', 'viewer')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    api_key VARCHAR(255) UNIQUE,
    secret_key VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建基本索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, config_type, description, is_encrypted) VALUES
('system.name', 'AI量化交易系统', 'string', '系统名称', FALSE),
('system.version', '1.0.0', 'string', '系统版本', FALSE),
('system.maintenance_mode', 'false', 'boolean', '维护模式', FALSE),
('security.jwt_secret', 'change_this_in_production', 'string', 'JWT密钥', TRUE),
('security.token_expire_hours', '24', 'number', 'Token过期时间(小时)', FALSE),
('logging.level', 'INFO', 'string', '日志级别', FALSE),
('api.rate_limit', '1000', 'number', 'API速率限制', FALSE),
('trading.demo_mode', 'true', 'boolean', '演示模式', FALSE)
ON CONFLICT (config_key) DO NOTHING;

-- 插入默认管理员用户（密码: admin123）
INSERT INTO users (username, email, password_hash, role, status) 
VALUES ('admin', 'admin@ai-trading.com', crypt('admin123', gen_salt('bf')), 'admin', 'active')
ON CONFLICT (username) DO NOTHING;

-- 创建更新时间的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表创建触发器
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为系统配置表创建触发器
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建用于获取配置的函数
CREATE OR REPLACE FUNCTION get_config(p_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    config_value TEXT;
BEGIN
    SELECT config_value INTO config_value
    FROM system_config 
    WHERE config_key = p_key;
    
    RETURN config_value;
END;
$$ LANGUAGE plpgsql;

-- 创建用于设置配置的函数
CREATE OR REPLACE FUNCTION set_config(p_key VARCHAR, p_value TEXT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO system_config (config_key, config_value)
    VALUES (p_key, p_value)
    ON CONFLICT (config_key) 
    DO UPDATE SET config_value = EXCLUDED.config_value, updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;