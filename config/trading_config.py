"""
交易配置管理
定义交易参数、策略配置和风险控制参数
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, validator


class AccountType(Enum):
    """账户类型枚举"""
    SPOT = "spot"
    CONTRACT = "contract"
    OPTION = "option"


class StrategyType(Enum):
    """策略类型枚举"""
    TECHNICAL = "technical"  # 技术指标策略
    ML = "ml"               # 机器学习策略
    RL = "rl"               # 强化学习策略
    HYBRID = "hybrid"       # 混合策略


class TradingConfig(BaseModel):
    """交易配置"""
    # 基础配置
    account_type: AccountType
    max_position_ratio: float = 0.8  # 最大持仓比例
    max_daily_loss_ratio: float = 0.05  # 单日最大亏损比例
    
    # 合约配置
    leverage: int = 1
    margin_mode: str = "isolated"  # isolated or crossed
    
    # 订单配置
    use_market_order: bool = False
    slippage_tolerance: float = 0.001  # 滑点容忍度
    
    # 风险配置
    stop_loss_ratio: float = 0.02  # 止损比例
    take_profit_ratio: float = 0.04  # 止盈比例
    trailing_stop_ratio: float = 0.01  # 移动止损比例
    
    # 策略配置
    strategy_type: StrategyType
    strategy_parameters: Dict = {}
    
    @validator('max_position_ratio')
    def validate_position_ratio(cls, v):
        if not 0 < v <= 1:
            raise ValueError('持仓比例必须在0-1之间')
        return v
    
    @validator('leverage')
    def validate_leverage(cls, v, values):
        if 'account_type' in values and values['account_type'] == AccountType.SPOT:
            if v != 1:
                raise ValueError('现货账户不支持杠杆')
        return v


class TRADING_CONFIG:
    """交易配置管理器"""
    
    # 默认配置模板
    default_configs: Dict[AccountType, TradingConfig] = {
        AccountType.SPOT: TradingConfig(
            account_type=AccountType.SPOT,
            max_position_ratio=0.8,
            max_daily_loss_ratio=0.05,
            leverage=1,
            stop_loss_ratio=0.02,
            take_profit_ratio=0.04,
            strategy_type=StrategyType.TECHNICAL
        ),
        
        AccountType.CONTRACT: TradingConfig(
            account_type=AccountType.CONTRACT,
            max_position_ratio=0.5,
            max_daily_loss_ratio=0.03,
            leverage=10,
            stop_loss_ratio=0.01,
            take_profit_ratio=0.02,
            strategy_type=StrategyType.TECHNICAL
        ),
        
        AccountType.OPTION: TradingConfig(
            account_type=AccountType.OPTION,
            max_position_ratio=0.3,
            max_daily_loss_ratio=0.02,
            leverage=1,
            stop_loss_ratio=0.05,
            take_profit_ratio=0.1,
            strategy_type=StrategyType.TECHNICAL
        )
    }
    
    @classmethod
    def get_default_config(cls, account_type: AccountType) -> TradingConfig:
        """获取默认配置"""
        return cls.default_configs[account_type]
    
    @classmethod
    def create_custom_config(cls, account_type: AccountType, **kwargs) -> TradingConfig:
        """创建自定义配置"""
        default_config = cls.get_default_config(account_type)
        config_dict = default_config.dict()
        config_dict.update(kwargs)
        return TradingConfig(**config_dict)


# 策略参数配置
class StrategyParameterConfig(BaseModel):
    """策略参数配置"""
    # 技术指标策略参数
    ma_fast_period: int = 10
    ma_slow_period: int = 30
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    
    # 机器学习策略参数
    ml_model_type: str = "xgboost"
    training_period: int = 1000
    prediction_horizon: int = 60
    
    # 强化学习策略参数
    rl_algorithm: str = "ppo"
    rl_training_steps: int = 10000
    rl_episode_length: int = 1000
    
    # 通用参数
    lookback_period: int = 100
    confidence_threshold: float = 0.7


class STRATEGY_PARAM_CONFIG:
    """策略参数配置管理器"""
    
    # 策略参数模板
    parameter_templates: Dict[StrategyType, StrategyParameterConfig] = {
        StrategyType.TECHNICAL: StrategyParameterConfig(
            ma_fast_period=10,
            ma_slow_period=30,
            rsi_period=14,
            lookback_period=100
        ),
        
        StrategyType.ML: StrategyParameterConfig(
            ml_model_type="xgboost",
            training_period=1000,
            prediction_horizon=60,
            confidence_threshold=0.7
        ),
        
        StrategyType.RL: StrategyParameterConfig(
            rl_algorithm="ppo",
            rl_training_steps=10000,
            rl_episode_length=1000,
            lookback_period=100
        )
    }
    
    @classmethod
    def get_parameter_template(cls, strategy_type: StrategyType) -> StrategyParameterConfig:
        """获取策略参数模板"""
        return cls.parameter_templates[strategy_type]


# 性能指标配置
class PerformanceConfig(BaseModel):
    """性能指标配置"""
    # 回测配置
    backtest_period: int = 365  # 回测天数
    initial_capital: float = 10000.0
    transaction_cost: float = 0.001  # 交易成本
    
    # 性能指标阈值
    min_sharpe_ratio: float = 1.0
    max_drawdown: float = 0.2
    min_win_rate: float = 0.5
    min_profit_factor: float = 1.2
    
    # 优化配置
    optimization_method: str = "genetic"  # genetic, grid, random
    optimization_iterations: int = 100


class PERFORMANCE_CONFIG:
    """性能指标配置管理器"""
    
    default_config = PerformanceConfig()
    
    @classmethod
    def get_default_config(cls) -> PerformanceConfig:
        """获取默认性能配置"""
        return cls.default_config


if __name__ == "__main__":
    # 配置验证测试
    print("=== 交易配置验证 ===")
    
    for account_type in AccountType:
        config = TRADING_CONFIG.get_default_config(account_type)
        print(f"{account_type.value}账户配置:")
        print(f"  最大持仓比例: {config.max_position_ratio}")
        print(f"  单日最大亏损: {config.max_daily_loss_ratio}")
        print(f"  止损比例: {config.stop_loss_ratio}")
        print()
    
    print("=== 策略参数配置验证 ===")
    for strategy_type in StrategyType:
        params = STRATEGY_PARAM_CONFIG.get_parameter_template(strategy_type)
        print(f"{strategy_type.value}策略参数:")
        print(f"  回看周期: {params.lookback_period}")
        print(f"  置信阈值: {params.confidence_threshold}")
        print()