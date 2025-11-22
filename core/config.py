"""
系统配置管理模块
负责加载和管理所有环境变量和配置参数
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="ai_trading", env="DB_NAME")
    user: str = Field(default="ai_trader", env="DB_USER")
    password: str = Field(default="your_secure_password_123", env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        """获取数据库连接URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: str = Field(default="your_redis_password_123", env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    
    @property
    def url(self) -> str:
        """获取Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ExchangeSettings(BaseSettings):
    """交易所API配置"""
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", env="BINANCE_API_SECRET")
    binance_sandbox: bool = Field(default=False, env="BINANCE_SANDBOX")
    
    okx_api_key: str = Field(default="", env="OKX_API_KEY")
    okx_api_secret: str = Field(default="", env="OKX_API_SECRET")
    okx_passphrase: str = Field(default="", env="OKX_PASSPHRASE")
    okx_sandbox: bool = Field(default=False, env="OKX_SANDBOX")
    
    bybit_api_key: str = Field(default="", env="BYBIT_API_KEY")
    bybit_api_secret: str = Field(default="", env="BYBIT_API_SECRET")
    bybit_sandbox: bool = Field(default=False, env="BYBIT_SANDBOX")


class AccountSettings(BaseSettings):
    """账户隔离配置"""
    contract_enabled: bool = Field(default=True, env="CONTRACT_ACCOUNT_ENABLED")
    contract_leverage_limit: int = Field(default=10, env="CONTRACT_LEVERAGE_LIMIT")
    contract_margin_ratio: float = Field(default=0.1, env="CONTRACT_MARGIN_RATIO")
    
    spot_enabled: bool = Field(default=True, env="SPOT_ACCOUNT_ENABLED")
    spot_max_position_ratio: float = Field(default=0.8, env="SPOT_MAX_POSITION_RATIO")
    spot_stop_loss_ratio: float = Field(default=0.05, env="SPOT_STOP_LOSS_RATIO")
    
    option_enabled: bool = Field(default=True, env="OPTION_ACCOUNT_ENABLED")
    option_max_premium_ratio: float = Field(default=0.3, env="OPTION_MAX_PREMIUM_RATIO")
    option_greeks_risk_limit: float = Field(default=0.1, env="OPTION_GREEKS_RISK_LIMIT")
    
    sub_account_enabled: bool = Field(default=True, env="SUB_ACCOUNT_ENABLED")
    sub_account_max_count: int = Field(default=10, env="SUB_ACCOUNT_MAX_COUNT")
    sub_account_api_rate_limit: int = Field(default=1000, env="SUB_ACCOUNT_API_RATE_LIMIT")


class SecuritySettings(BaseSettings):
    """安全配置"""
    SECRET_KEY: str = Field(default="your_jwt_secret_key_32_chars_long", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")


class MonitoringSettings(BaseSettings):
    """监控配置"""
    prometheus_port: int = Field(default=8001, env="PROMETHEUS_PORT")
    grafana_password: str = Field(default="admin123", env="GRAFANA_PASSWORD")
    alert_webhook: str = Field(default="", env="ALERT_WEBHOOK")


class Settings(BaseSettings):
    """全局配置"""
    app_env: str = Field(default="production", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    web_port: int = Field(default=8000, env="WEB_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    exchange: ExchangeSettings = ExchangeSettings()
    account: AccountSettings = AccountSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


if __name__ == "__main__":
    # 配置验证脚本
    print("=== AI量化交易系统配置验证 ===")
    print(f"环境: {settings.app_env}")
    print(f"数据库: {settings.database.url}")
    print(f"Redis: {settings.redis.url}")
    print(f"交易所配置: {len(settings.exchange.binance_api_key) > 0}")
    print("配置验证完成!")