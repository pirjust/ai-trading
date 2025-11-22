"""
策略名称生成器
根据时间、算法类型和参数自动生成有意义的策略名称
"""

import random
import string
from datetime import datetime
from typing import Dict, Any, List


class StrategyNameGenerator:
    """策略名称生成器"""
    
    # 算法类型前缀
    ALGORITHM_PREFIXES = {
        'lstm': 'LSTM',
        'gru': 'GRU', 
        'transformer': 'Transformer',
        'cnn': 'CNN',
        'random_forest': 'RF',
        'xgboost': 'XGB',
        'lightgbm': 'LGBM',
        'rl': 'RL',
        'dqn': 'DQN',
        'ppo': 'PPO',
        'a3c': 'A3C',
        'sac': 'SAC',
        'trend_following': 'Trend',
        'mean_reversion': 'MeanRev',
        'momentum': 'Momentum',
        'arbitrage': 'Arb',
        'market_making': 'MM',
        'grid': 'Grid',
        'dca': 'DCA',
        'scalping': 'Scalp',
        'swing': 'Swing',
        'position': 'Position',
        'multi_timeframe': 'MTF',
        'ensemble': 'Ensemble',
        'hybrid': 'Hybrid'
    }
    
    # 时间段描述
    TIME_PERIODS = {
        '1m': '1Min',
        '5m': '5Min',
        '15m': '15Min',
        '30m': '30Min',
        '1h': '1Hour',
        '4h': '4Hour',
        '1d': '1Day',
        '1w': '1Week'
    }
    
    # 市场类型
    MARKET_TYPES = {
        'spot': 'Spot',
        'futures': 'Futures',
        'swap': 'Swap',
        'option': 'Option'
    }
    
    # 风险等级
    RISK_LEVELS = {
        'low': 'Low',
        'medium': 'Mid',
        'high': 'High',
        'aggressive': 'Agg'
    }
    
    # 常用后缀
    COMMON_SUFFIXES = [
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Pro', 'Max', 'Ultra', 'Plus', 'Prime', 'Elite', 'Advanced', 'Smart',
        'Quant', 'AI', 'ML', 'Deep', 'Neural', 'Quantum', 'Rocket', 'Nitro',
        'V1', 'V2', 'V3', 'V4', 'V5', 'X1', 'X2', 'X3'
    ]
    
    @classmethod
    def generate_strategy_name(cls, 
                             algorithm_type: str = None,
                             time_period: str = None,
                             market_type: str = None,
                             risk_level: str = None,
                            symbols: List[str] = None,
                             parameters: Dict[str, Any] = None,
                             custom_suffix: str = None,
                             include_timestamp: bool = False,
                             include_random: bool = False) -> str:
        """
        生成策略名称
        
        Args:
            algorithm_type: 算法类型
            time_period: 时间周期
            market_type: 市场类型
            risk_level: 风险等级
            symbols: 交易标的列表
            parameters: 策略参数
            custom_suffix: 自定义后缀
            include_timestamp: 是否包含时间戳
            include_random: 是否包含随机标识
            
        Returns:
            生成的策略名称
        """
        
        name_parts = []
        
        # 1. 算法前缀
        if algorithm_type:
            prefix = cls.ALGORITHM_PREFIXES.get(algorithm_type.lower(), algorithm_type.upper())
            name_parts.append(prefix)
        
        # 2. 市场类型
        if market_type:
            market = cls.MARKET_TYPES.get(market_type.lower(), market_type.upper())
            name_parts.append(market)
        
        # 3. 时间周期
        if time_period:
            period = cls.TIME_PERIODS.get(time_period.lower(), time_period.upper())
            name_parts.append(period)
        
        # 4. 交易标的
        if symbols:
            if len(symbols) == 1:
                # 单个标的
                symbol_part = cls._clean_symbol(symbols[0])
                name_parts.append(symbol_part)
            elif len(symbols) <= 3:
                # 多个标的，取前几个
                symbol_part = ''.join([cls._clean_symbol(s)[:3] for s in symbols[:3]])
                name_parts.append(f"Multi{symbol_part}")
            else:
                # 超过3个，用通用名称
                name_parts.append("Multi")
        
        # 5. 风险等级
        if risk_level:
            risk = cls.RISK_LEVELS.get(risk_level.lower(), risk_level.upper())
            name_parts.append(risk)
        
        # 6. 参数特征
        if parameters:
            param_feature = cls._extract_parameter_feature(parameters)
            if param_feature:
                name_parts.append(param_feature)
        
        # 7. 自定义后缀或随机后缀
        if custom_suffix:
            name_parts.append(custom_suffix)
        elif include_random:
            random_suffix = random.choice(cls.COMMON_SUFFIXES)
            name_parts.append(random_suffix)
        
        # 8. 时间戳（如果需要）
        if include_timestamp:
            timestamp = datetime.now().strftime("%m%d")
            name_parts.append(timestamp)
        
        # 组合名称
        strategy_name = ''.join(name_parts)
        
        # 限制长度
        if len(strategy_name) > 50:
            strategy_name = strategy_name[:50]
        
        # 添加随机标识符确保唯一性
        if include_random and not custom_suffix:
            random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            strategy_name = f"{strategy_name}_{random_id}"
        
        return strategy_name
    
    @classmethod
    def _clean_symbol(cls, symbol: str) -> str:
        """清理交易标的名称"""
        # 移除常见后缀
        for suffix in ['USDT', 'BTC', 'ETH', 'USD', 'PERP', 'SWAP']:
            if symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break
        
        # 只保留字母和数字
        symbol = ''.join(c for c in symbol if c.isalnum())
        
        return symbol.upper()
    
    @classmethod
    def _extract_parameter_feature(cls, parameters: Dict[str, Any]) -> str:
        """从参数中提取特征"""
        if not parameters:
            return ""
        
        features = []
        
        # 杠杆倍数
        if 'leverage' in parameters and parameters['leverage'] > 1:
            features.append(f"Lever{parameters['leverage']}")
        
        # 仓位大小
        if 'position_size' in parameters:
            pos_size = parameters['position_size']
            if pos_size >= 0.9:
                features.append("Full")
            elif pos_size >= 0.5:
                features.append("Half")
            else:
                features.append("Conservative")
        
        # 止损比例
        if 'stop_loss' in parameters:
            sl_percent = parameters['stop_loss'] * 100
            if sl_percent <= 1:
                features.append(f"Tight{int(sl_percent)}%")
            else:
                features.append(f"SL{int(sl_percent)}%")
        
        # 止盈比例
        if 'take_profit' in parameters:
            tp_percent = parameters['take_profit'] * 100
            features.append(f"TP{int(tp_percent)}%")
        
        # 窗口期
        if 'window' in parameters or 'period' in parameters:
            window = parameters.get('window', parameters.get('period', 0))
            if window > 0:
                features.append(f"W{window}")
        
        # 阈值
        if 'threshold' in parameters:
            threshold = parameters['threshold']
            if isinstance(threshold, float):
                features.append(f"Thr{threshold:.2f}")
            else:
                features.append(f"Thr{threshold}")
        
        return ''.join(features)
    
    @classmethod
    def generate_batch_names(cls, count: int, base_params: Dict[str, Any] = None) -> List[str]:
        """批量生成策略名称"""
        names = []
        used_names = set()
        
        for i in range(count):
            params = base_params.copy() if base_params else {}
            
            # 为每个策略添加一些变化
            if i > 0:
                params['variant'] = i + 1
            
            name = cls.generate_strategy_name(
                include_random=True,
                include_timestamp=(i % 3 == 0),  # 每3个包含时间戳
                **params
            )
            
            # 确保名称唯一
            while name in used_names:
                name = cls.generate_strategy_name(
                    include_random=True,
                    **params
                )
            
            used_names.add(name)
            names.append(name)
        
        return names
    
    @classmethod
    def parse_strategy_name(cls, name: str) -> Dict[str, Any]:
        """解析策略名称，提取关键信息"""
        parsed = {
            'name': name,
            'algorithm_type': None,
            'market_type': None,
            'time_period': None,
            'risk_level': None,
            'features': [],
            'suffix': None,
            'timestamp': None
        }
        
        # 解析算法类型
        for alg, prefix in cls.ALGORITHM_PREFIXES.items():
            if name.startswith(prefix):
                parsed['algorithm_type'] = alg
                remaining_name = name[len(prefix):]
                break
        else:
            remaining_name = name
        
        # 解析其他特征
        for market_type, prefix in cls.MARKET_TYPES.items():
            if prefix in remaining_name:
                parsed['market_type'] = market_type
                parsed['features'].append(prefix)
        
        for period, prefix in cls.TIME_PERIODS.items():
            if prefix in remaining_name:
                parsed['time_period'] = period
                parsed['features'].append(prefix)
        
        for risk, prefix in cls.RISK_LEVELS.items():
            if prefix in remaining_name:
                parsed['risk_level'] = risk
                parsed['features'].append(prefix)
        
        return parsed


# 便捷函数
def generate_name(**kwargs) -> str:
    """便捷的策略名称生成函数"""
    return StrategyNameGenerator.generate_strategy_name(**kwargs)


def generate_lstm_strategy(symbol: str, time_period: str = "1h", **kwargs) -> str:
    """生成LSTM策略名称"""
    return StrategyNameGenerator.generate_strategy_name(
        algorithm_type="lstm",
        symbols=[symbol],
        time_period=time_period,
        include_random=True,
        **kwargs
    )


def generate_rl_strategy(symbol: str, market_type: str = "futures", **kwargs) -> str:
    """生成强化学习策略名称"""
    return StrategyNameGenerator.generate_strategy_name(
        algorithm_type="rl",
        symbols=[symbol],
        market_type=market_type,
        include_random=True,
        **kwargs
    )


def generate_technical_strategy(strategy_type: str, symbols: List[str], **kwargs) -> str:
    """生成技术分析策略名称"""
    return StrategyNameGenerator.generate_strategy_name(
        algorithm_type=strategy_type,
        symbols=symbols,
        include_random=True,
        **kwargs
    )


if __name__ == "__main__":
    # 测试策略名称生成
    print("=== 策略名称生成测试 ===")
    
    # LSTM策略
    lstm_name = generate_lstm_strategy("BTCUSDT", "1h", risk_level="medium")
    print(f"LSTM策略: {lstm_name}")
    
    # 强化学习策略
    rl_name = generate_rl_strategy("ETHUSDT", "futures", risk_level="high")
    print(f"RL策略: {rl_name}")
    
    # 技术分析策略
    tech_name = generate_technical_strategy("trend_following", ["BTCUSDT", "ETHUSDT"])
    print(f"技术策略: {tech_name}")
    
    # 自定义策略
    custom_name = StrategyNameGenerator.generate_strategy_name(
        algorithm_type="xgboost",
        market_type="spot",
        time_period="15m",
        symbols=["BTCUSDT"],
        risk_level="low",
        parameters={
            "leverage": 3,
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "window": 20
        },
        include_timestamp=True
    )
    print(f"自定义策略: {custom_name}")
    
    # 批量生成
    batch_names = StrategyNameGenerator.generate_batch_names(5, {
        "algorithm_type": "ensemble",
        "symbols": ["BTCUSDT"],
        "risk_level": "medium"
    })
    print(f"\n批量生成: {batch_names}")
    
    # 解析策略名称
    parsed = StrategyNameGenerator.parse_strategy_name(custom_name)
    print(f"\n解析结果: {parsed}")
    
    print("\n策略名称生成器测试完成!")