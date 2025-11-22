"""
风险控制配置管理
定义风险参数、监控阈值和报警规则
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, validator


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型枚举"""
    MARKET = "market"           # 市场风险
    CREDIT = "credit"           # 信用风险
    LIQUIDITY = "liquidity"     # 流动性风险
    OPERATIONAL = "operational" # 操作风险
    SYSTEMIC = "systemic"       # 系统性风险


class RiskThreshold(BaseModel):
    """风险阈值配置"""
    risk_type: RiskType
    threshold_value: float
    risk_level: RiskLevel
    action_required: bool = False
    notification_channel: List[str] = ["email", "sms"]
    
    @validator('threshold_value')
    def validate_threshold(cls, v):
        if v < 0:
            raise ValueError('阈值不能为负数')
        return v


class RiskMonitoringConfig(BaseModel):
    """风险监控配置"""
    # 基础监控配置
    monitoring_interval: int = 60  # 监控间隔(秒)
    data_retention_days: int = 30  # 数据保留天数
    
    # 风险阈值配置
    thresholds: List[RiskThreshold]
    
    # 报警配置
    alert_cooldown: int = 300  # 报警冷却时间(秒)
    max_alerts_per_hour: int = 10  # 每小时最大报警次数
    
    # 自动风控配置
    auto_stop_trading: bool = True
    auto_reduce_position: bool = True
    emergency_liquidation: bool = False


class RISK_CONFIG:
    """风险配置管理器"""
    
    # 默认风险阈值配置
    default_thresholds: Dict[RiskType, RiskThreshold] = {
        RiskType.MARKET: RiskThreshold(
            risk_type=RiskType.MARKET,
            threshold_value=0.1,  # 10% 市场波动
            risk_level=RiskLevel.HIGH,
            action_required=True
        ),
        
        RiskType.CREDIT: RiskThreshold(
            risk_type=RiskType.CREDIT,
            threshold_value=0.05,  # 5% 信用风险
            risk_level=RiskLevel.MEDIUM,
            action_required=False
        ),
        
        RiskType.LIQUIDITY: RiskThreshold(
            risk_type=RiskType.LIQUIDITY,
            threshold_value=0.2,  # 20% 流动性风险
            risk_level=RiskLevel.CRITICAL,
            action_required=True
        ),
        
        RiskType.OPERATIONAL: RiskThreshold(
            risk_type=RiskType.OPERATIONAL,
            threshold_value=0.01,  # 1% 操作风险
            risk_level=RiskLevel.LOW,
            action_required=False
        ),
        
        RiskType.SYSTEMIC: RiskThreshold(
            risk_type=RiskType.SYSTEMIC,
            threshold_value=0.15,  # 15% 系统性风险
            risk_level=RiskLevel.CRITICAL,
            action_required=True
        )
    }
    
    # 账户类型特定配置
    account_specific_configs: Dict[str, RiskMonitoringConfig] = {
        "spot": RiskMonitoringConfig(
            monitoring_interval=60,
            thresholds=[
                default_thresholds[RiskType.MARKET],
                default_thresholds[RiskType.LIQUIDITY]
            ],
            auto_stop_trading=True
        ),
        
        "contract": RiskMonitoringConfig(
            monitoring_interval=30,
            thresholds=[
                default_thresholds[RiskType.MARKET],
                default_thresholds[RiskType.LIQUIDITY],
                default_thresholds[RiskType.SYSTEMIC]
            ],
            auto_stop_trading=True,
            auto_reduce_position=True
        ),
        
        "option": RiskMonitoringConfig(
            monitoring_interval=15,
            thresholds=list(default_thresholds.values()),
            auto_stop_trading=True,
            emergency_liquidation=True
        )
    }
    
    @classmethod
    def get_account_config(cls, account_type: str) -> RiskMonitoringConfig:
        """获取账户类型特定配置"""
        if account_type not in cls.account_specific_configs:
            raise ValueError(f"不支持的账户类型: {account_type}")
        return cls.account_specific_configs[account_type]
    
    @classmethod
    def get_threshold(cls, risk_type: RiskType) -> RiskThreshold:
        """获取风险阈值"""
        return cls.default_thresholds[risk_type]
    
    @classmethod
    def update_threshold(cls, risk_type: RiskType, threshold_value: float, risk_level: RiskLevel):
        """更新风险阈值"""
        cls.default_thresholds[risk_type] = RiskThreshold(
            risk_type=risk_type,
            threshold_value=threshold_value,
            risk_level=risk_level
        )


# 风险指标计算配置
class RiskMetricConfig(BaseModel):
    """风险指标计算配置"""
    # VaR配置
    var_confidence_level: float = 0.95
    var_time_horizon: int = 1  # 天数
    var_method: str = "historical"  # historical, parametric, monte_carlo
    
    # CVaR配置
    cvar_confidence_level: float = 0.95
    
    # 最大回撤配置
    max_drawdown_lookback: int = 252  # 交易日
    
    # 夏普比率配置
    sharpe_risk_free_rate: float = 0.02  # 年化无风险利率
    sharpe_period: str = "daily"  # daily, weekly, monthly
    
    # 希腊字母风险配置 (期权)
    greeks_calculation_method: str = "black_scholes"  # black_scholes, binomial


class RISK_METRIC_CONFIG:
    """风险指标配置管理器"""
    
    default_config = RiskMetricConfig()
    
    @classmethod
    def get_default_config(cls) -> RiskMetricConfig:
        """获取默认风险指标配置"""
        return cls.default_config


# 风险报警规则配置
class AlertRule(BaseModel):
    """报警规则"""
    rule_name: str
    condition: str  # 条件表达式
    severity: RiskLevel
    message_template: str
    auto_action: Optional[str] = None  # 自动执行的动作
    
    @validator('condition')
    def validate_condition(cls, v):
        # 简单的条件表达式验证
        allowed_operators = ['>', '<', '>=', '<=', '==', '!=']
        if not any(op in v for op in allowed_operators):
            raise ValueError('条件表达式必须包含比较运算符')
        return v


class ALERT_CONFIG:
    """报警配置管理器"""
    
    # 默认报警规则
    default_rules: List[AlertRule] = [
        AlertRule(
            rule_name="high_drawdown",
            condition="drawdown > 0.1",
            severity=RiskLevel.HIGH,
            message_template="当前回撤超过10%，建议减仓",
            auto_action="reduce_position"
        ),
        
        AlertRule(
            rule_name="low_sharpe",
            condition="sharpe_ratio < 1.0",
            severity=RiskLevel.MEDIUM,
            message_template="夏普比率低于1.0，策略表现不佳"
        ),
        
        AlertRule(
            rule_name="high_leverage",
            condition="leverage > 10",
            severity=RiskLevel.CRITICAL,
            message_template="杠杆率超过10倍，风险极高",
            auto_action="stop_trading"
        ),
        
        AlertRule(
            rule_name="market_crash",
            condition="market_volatility > 0.2",
            severity=RiskLevel.CRITICAL,
            message_template="市场波动率超过20%，可能发生市场崩盘",
            auto_action="emergency_liquidation"
        )
    ]
    
    @classmethod
    def get_all_rules(cls) -> List[AlertRule]:
        """获取所有报警规则"""
        return cls.default_rules
    
    @classmethod
    def add_rule(cls, rule: AlertRule):
        """添加报警规则"""
        cls.default_rules.append(rule)
    
    @classmethod
    def remove_rule(cls, rule_name: str):
        """移除报警规则"""
        cls.default_rules = [r for r in cls.default_rules if r.rule_name != rule_name]


if __name__ == "__main__":
    # 配置验证测试
    print("=== 风险配置验证 ===")
    
    for account_type in ["spot", "contract", "option"]:
        config = RISK_CONFIG.get_account_config(account_type)
        print(f"{account_type}账户风险配置:")
        print(f"  监控间隔: {config.monitoring_interval}秒")
        print(f"  风险阈值数量: {len(config.thresholds)}")
        print(f"  自动停止交易: {config.auto_stop_trading}")
        print()
    
    print("=== 报警规则验证 ===")
    for rule in ALERT_CONFIG.get_all_rules():
        print(f"规则: {rule.rule_name}")
        print(f"  条件: {rule.condition}")
        print(f"  严重程度: {rule.severity.value}")
        print(f"  自动动作: {rule.auto_action or '无'}")
        print()