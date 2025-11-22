"""
API配置管理
负责管理和验证所有交易所API配置
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, validator


class ExchangeAPIConfig(BaseSettings):
    """交易所API配置"""
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None  # 用于欧意等需要passphrase的交易所
    sandbox: bool = False
    testnet: bool = False
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError('API Key不能为空且长度必须大于10')
        return v
    
    @validator('api_secret')
    def validate_api_secret(cls, v):
        if not v or len(v) < 10:
            raise ValueError('API Secret不能为空且长度必须大于10')
        return v


class SubAccountConfig(BaseSettings):
    """子账号配置"""
    account_id: str
    exchange_api_config: ExchangeAPIConfig
    enabled: bool = True
    rate_limit: int = 1000  # 每分钟请求限制


class API_CONFIG:
    """API配置管理器"""
    
    # 主账号配置
    exchanges: Dict[str, ExchangeAPIConfig] = {
        "binance": ExchangeAPIConfig(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            sandbox=os.getenv("BINANCE_SANDBOX", "false").lower() == "true",
            testnet=os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        ),
        "okx": ExchangeAPIConfig(
            api_key=os.getenv("OKX_API_KEY", ""),
            api_secret=os.getenv("OKX_API_SECRET", ""),
            passphrase=os.getenv("OKX_PASSPHRASE", ""),
            sandbox=os.getenv("OKX_SANDBOX", "false").lower() == "true"
        ),
        "bybit": ExchangeAPIConfig(
            api_key=os.getenv("BYBIT_API_KEY", ""),
            api_secret=os.getenv("BYBIT_API_SECRET", ""),
            sandbox=os.getenv("BYBIT_SANDBOX", "false").lower() == "true"
        )
    }
    
    # 子账号配置
    sub_accounts: Dict[str, SubAccountConfig] = {}
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证API配置"""
        errors = []
        
        for exchange_name, config in cls.exchanges.items():
            if not config.api_key or not config.api_secret:
                errors.append(f"{exchange_name} API配置不完整")
        
        if errors:
            raise ValueError(f"API配置验证失败: {'; '.join(errors)}")
        
        return True
    
    @classmethod
    def get_exchange_config(cls, exchange_name: str) -> ExchangeAPIConfig:
        """获取指定交易所配置"""
        if exchange_name not in cls.exchanges:
            raise ValueError(f"不支持的交易所: {exchange_name}")
        return cls.exchanges[exchange_name]
    
    @classmethod
    def add_sub_account(cls, account_id: str, config: SubAccountConfig):
        """添加子账号配置"""
        if account_id in cls.sub_accounts:
            raise ValueError(f"子账号 {account_id} 已存在")
        cls.sub_accounts[account_id] = config
    
    @classmethod
    def remove_sub_account(cls, account_id: str):
        """移除子账号配置"""
        if account_id in cls.sub_accounts:
            del cls.sub_accounts[account_id]
    
    @classmethod
    def get_sub_account_config(cls, account_id: str) -> SubAccountConfig:
        """获取子账号配置"""
        if account_id not in cls.sub_accounts:
            raise ValueError(f"子账号 {account_id} 不存在")
        return cls.sub_accounts[account_id]


# 配置验证
if __name__ == "__main__":
    try:
        API_CONFIG.validate_config()
        print("API配置验证通过")
    except ValueError as e:
        print(f"API配置验证失败: {e}")