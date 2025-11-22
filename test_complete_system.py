#!/usr/bin/env python3
"""
AI量化交易系统完整测试脚本
测试所有主要组件和功能
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入测试目标
from core.config import settings
from core.database import db_manager
from core.logger import get_logger
from core.strategy_naming import StrategyNameGenerator
from data.data_manager import get_data_manager
from strategies.ai_strategies import (
    MachineLearningStrategy, 
    LSTMPredictionStrategy, 
    ReinforcementLearningStrategy
)

logger = get_logger("system_test")


class SystemTestSuite:
    """系统测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始AI量化交易系统完整测试")
        print("=" * 60)
        
        # 基础环境测试
        await self.test_basic_environment()
        
        # 配置测试
        await self.test_configuration()
        
        # 数据库测试
        await self.test_database()
        
        # 策略命名测试
        await self.test_strategy_naming()
        
        # 数据管理测试
        await self.test_data_management()
        
        # AI策略测试
        await self.test_ai_strategies()
        
        # API测试（模拟）
        await self.test_api_endpoints()
        
        # 性能测试
        await self.test_performance()
        
        # 显示测试结果
        self.show_test_results()
        
        return self.passed_tests == self.total_tests
    
    async def test_basic_environment(self):
        """测试基础环境"""
        print("\n📋 基础环境测试")
        print("-" * 30)
        
        tests = [
            self.test_python_version,
            self.test_dependencies,
            self.test_directory_structure,
            self.test_environment_variables,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_configuration(self):
        """测试配置"""
        print("\n⚙️  配置测试")
        print("-" * 30)
        
        tests = [
            self.test_settings_loading,
            self.test_database_config,
            self.test_exchange_config,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_database(self):
        """测试数据库"""
        print("\n💾 数据库测试")
        print("-" * 30)
        
        tests = [
            self.test_database_connection,
            self.test_table_creation,
            self.test_model_imports,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_strategy_naming(self):
        """测试策略命名"""
        print("\n🏷️  策略命名测试")
        print("-" * 30)
        
        tests = [
            self.test_strategy_name_generation,
            self.test_strategy_name_parsing,
            self.test_batch_name_generation,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_data_management(self):
        """测试数据管理"""
        print("\n📊 数据管理测试")
        print("-" * 30)
        
        tests = [
            self.test_data_manager_init,
            self.test_kline_data_mock,
            self.test_cache_functionality,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_ai_strategies(self):
        """测试AI策略"""
        print("\n🤖 AI策略测试")
        print("-" * 30)
        
        tests = [
            self.test_ml_strategy_init,
            self.test_lstm_strategy_init,
            self.test_rl_strategy_init,
            self.test_strategy_signal_generation,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_api_endpoints(self):
        """测试API端点（模拟）"""
        print("\n🔌 API端点测试")
        print("-" * 30)
        
        tests = [
            self.test_api_imports,
            self.test_trading_endpoints,
            self.test_error_handling,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def test_performance(self):
        """测试性能"""
        print("\n⚡ 性能测试")
        print("-" * 30)
        
        tests = [
            self.test_strategy_performance,
            self.test_memory_usage,
        ]
        
        for test in tests:
            await self.run_test(test)
    
    async def run_test(self, test_func):
        """运行单个测试"""
        self.total_tests += 1
        test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
        
        try:
            start_time = time.time()
            result = await test_func()
            duration = time.time() - start_time
            
            if result:
                self.passed_tests += 1
                status = "✅ PASS"
                logger.info(f"Test {test_name}: {status} ({duration:.2f}s)")
            else:
                self.failed_tests += 1
                status = "❌ FAIL"
                logger.error(f"Test {test_name}: {status}")
            
            self.test_results.append({
                'test': test_name,
                'status': status,
                'duration': duration,
                'details': result if isinstance(result, dict) else {}
            })
            
        except Exception as e:
            self.failed_tests += 1
            status = "❌ ERROR"
            logger.error(f"Test {test_name}: {status} - {str(e)}")
            logger.error(traceback.format_exc())
            
            self.test_results.append({
                'test': test_name,
                'status': status,
                'duration': 0,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
    
    # 具体测试方法
    async def test_python_version(self) -> bool:
        """测试Python版本"""
        import sys
        version = sys.version_info
        return version.major >= 3 and version.minor >= 8
    
    async def test_dependencies(self) -> bool:
        """测试依赖包"""
        try:
            import pandas
            import numpy
            import fastapi
            import sqlalchemy
            import asyncio
            import aiohttp
            return True
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            return False
    
    async def test_directory_structure(self) -> bool:
        """测试目录结构"""
        required_dirs = [
            'app', 'core', 'data', 'strategies', 'frontend', 'scripts', 'docs'
        ]
        
        for dir_name in required_dirs:
            if not Path(dir_name).is_dir():
                logger.error(f"Missing directory: {dir_name}")
                return False
        
        return True
    
    async def test_environment_variables(self) -> bool:
        """测试环境变量"""
        try:
            # 测试配置加载
            assert hasattr(settings, 'database')
            assert hasattr(settings, 'redis')
            assert hasattr(settings, 'exchange')
            return True
        except Exception as e:
            logger.error(f"Environment variables test failed: {e}")
            return False
    
    async def test_settings_loading(self) -> bool:
        """测试设置加载"""
        try:
            assert settings.app_env in ['development', 'production', 'testing']
            assert settings.web_port > 0
            assert hasattr(settings.database, 'url')
            return True
        except Exception as e:
            logger.error(f"Settings loading test failed: {e}")
            return False
    
    async def test_database_config(self) -> bool:
        """测试数据库配置"""
        try:
            assert settings.database.host
            assert settings.database.name
            assert settings.database.user
            return True
        except Exception as e:
            logger.error(f"Database config test failed: {e}")
            return False
    
    async def test_exchange_config(self) -> bool:
        """测试交易所配置"""
        try:
            assert hasattr(settings.exchange, 'binance_api_key')
            assert hasattr(settings.exchange, 'okx_api_key')
            return True
        except Exception as e:
            logger.error(f"Exchange config test failed: {e}")
            return False
    
    async def test_database_connection(self) -> bool:
        """测试数据库连接"""
        try:
            # 简单连接测试（不实际连接数据库）
            engine = db_manager.engine
            assert engine is not None
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def test_table_creation(self) -> bool:
        """测试表创建"""
        try:
            # 测试模型导入
            from app.models.database_models import Base
            assert Base is not None
            return True
        except Exception as e:
            logger.error(f"Table creation test failed: {e}")
            return False
    
    async def test_model_imports(self) -> bool:
        """测试模型导入"""
        try:
            from app.models.database_models import User, Strategy, Trade, Account
            assert all([User, Strategy, Trade, Account])
            return True
        except Exception as e:
            logger.error(f"Model imports test failed: {e}")
            return False
    
    async def test_strategy_name_generation(self) -> bool:
        """测试策略名称生成"""
        try:
            # 测试基本名称生成
            name1 = StrategyNameGenerator.generate_strategy_name(
                algorithm_type="lstm",
                symbols=["BTCUSDT"],
                include_random=False
            )
            
            name2 = StrategyNameGenerator.generate_strategy_name(
                algorithm_type="rl",
                market_type="futures",
                include_random=True
            )
            
            assert isinstance(name1, str) and len(name1) > 0
            assert isinstance(name2, str) and len(name2) > 0
            assert name1 != name2
            return True
        except Exception as e:
            logger.error(f"Strategy name generation test failed: {e}")
            return False
    
    async def test_strategy_name_parsing(self) -> bool:
        """测试策略名称解析"""
        try:
            parsed = StrategyNameGenerator.parse_strategy_name("LSTMBTCSpot15MinMid")
            assert parsed['algorithm_type'] == 'lstm'
            assert 'BTC' in parsed.get('features', [])
            return True
        except Exception as e:
            logger.error(f"Strategy name parsing test failed: {e}")
            return False
    
    async def test_batch_name_generation(self) -> bool:
        """测试批量名称生成"""
        try:
            names = StrategyNameGenerator.generate_batch_names(3)
            assert len(names) == 3
            assert len(set(names)) == 3  # 确保唯一性
            return True
        except Exception as e:
            logger.error(f"Batch name generation test failed: {e}")
            return False
    
    async def test_data_manager_init(self) -> bool:
        """测试数据管理器初始化"""
        try:
            # 简单的初始化测试
            dm = get_data_manager()
            assert dm is not None
            return True
        except Exception as e:
            logger.error(f"Data manager init test failed: {e}")
            return False
    
    async def test_kline_data_mock(self) -> bool:
        """测试K线数据模拟"""
        try:
            # 模拟数据获取（不实际调用API）
            import pandas as pd
            mock_data = pd.DataFrame({
                'open': [50000, 50100, 50200],
                'high': [50100, 50200, 50300],
                'low': [49900, 50000, 50100],
                'close': [50100, 50200, 50300],
                'volume': [100, 150, 120]
            })
            assert len(mock_data) == 3
            assert list(mock_data.columns) == ['open', 'high', 'low', 'close', 'volume']
            return True
        except Exception as e:
            logger.error(f"Kline data mock test failed: {e}")
            return False
    
    async def test_cache_functionality(self) -> bool:
        """测试缓存功能"""
        try:
            # 简单缓存测试
            from core.logger import logger_manager
            logger_manager._set_cache("test_key", "test_value", 60)
            assert logger_manager._is_cache_valid("test_key")
            assert logger_manager.cache["test_key"] == "test_value"
            return True
        except Exception as e:
            logger.error(f"Cache functionality test failed: {e}")
            return False
    
    async def test_ml_strategy_init(self) -> bool:
        """测试机器学习策略初始化"""
        try:
            config = {
                'symbols': ['BTCUSDT'],
                'timeframe': '1h',
                'parameters': {'window': 20}
            }
            strategy = MachineLearningStrategy(
                name="TestML",
                config=config
            )
            assert strategy.name == "TestML"
            assert strategy.config == config
            return True
        except Exception as e:
            logger.error(f"ML strategy init test failed: {e}")
            return False
    
    async def test_lstm_strategy_init(self) -> bool:
        """测试LSTM策略初始化"""
        try:
            config = {
                'symbols': ['ETHUSDT'],
                'sequence_length': 60,
                'prediction_horizon': 5
            }
            strategy = LSTMPredictionStrategy(
                name="TestLSTM",
                config=config
            )
            assert strategy.name == "TestLSTM"
            assert strategy.sequence_length == 60
            return True
        except Exception as e:
            logger.error(f"LSTM strategy init test failed: {e}")
            return False
    
    async def test_rl_strategy_init(self) -> bool:
        """测试强化学习策略初始化"""
        try:
            config = {
                'symbols': ['BTCUSDT'],
                'state_size': 10,
                'epsilon': 0.1
            }
            strategy = ReinforcementLearningStrategy(
                name="TestRL",
                config=config
            )
            assert strategy.name == "TestRL"
            assert strategy.state_size == 10
            return True
        except Exception as e:
            logger.error(f"RL strategy init test failed: {e}")
            return False
    
    async def test_strategy_signal_generation(self) -> bool:
        """测试策略信号生成"""
        try:
            import pandas as pd
            import numpy as np
            
            # 创建模拟数据
            dates = pd.date_range('2024-01-01', periods=100, freq='H')
            data = pd.DataFrame({
                'close': np.random.normal(50000, 1000, 100),
                'volume': np.random.uniform(100, 1000, 100)
            }, index=dates)
            
            config = {'symbols': ['BTCUSDT']}
            strategy = MachineLearningStrategy(name="Test", config=config)
            
            # 测试特征创建
            features = strategy.create_features(data)
            assert not features.empty
            assert 'rsi' in features.columns
            return True
        except Exception as e:
            logger.error(f"Strategy signal generation test failed: {e}")
            return False
    
    async def test_api_imports(self) -> bool:
        """测试API导入"""
        try:
            from app.api.api_v1.endpoints.trading import router
            assert router is not None
            return True
        except Exception as e:
            logger.error(f"API imports test failed: {e}")
            return False
    
    async def test_trading_endpoints(self) -> bool:
        """测试交易端点"""
        try:
            from app.api.api_v1.endpoints.trading import (
                get_kline_data, get_ticker_data, place_order
            )
            assert all([get_kline_data, get_ticker_data, place_order])
            return True
        except Exception as e:
            logger.error(f"Trading endpoints test failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        try:
            from core.logger import get_logger
            test_logger = get_logger("test")
            
            # 测试日志记录
            test_logger.info("Test log message")
            
            # 测试错误处理工具
            from core.logger import logger_manager
            logger_manager.log_risk_event("test", "low", "test message")
            
            return True
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    async def test_strategy_performance(self) -> bool:
        """测试策略性能"""
        try:
            start_time = time.time()
            
            # 模拟策略执行
            config = {'symbols': ['BTCUSDT']}
            strategy = MachineLearningStrategy(name="PerfTest", config=config)
            
            # 模拟数据处理
            import pandas as pd
            import numpy as np
            
            data = pd.DataFrame({
                'close': np.random.normal(50000, 1000, 1000),
                'volume': np.random.uniform(100, 1000, 1000)
            })
            
            features = strategy.create_features(data)
            duration = time.time() - start_time
            
            # 性能要求：1000条数据处理应在1秒内完成
            assert duration < 1.0
            assert len(features) == 1000
            return True
        except Exception as e:
            logger.error(f"Strategy performance test failed: {e}")
            return False
    
    async def test_memory_usage(self) -> bool:
        """测试内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # 创建大量对象
            objects = []
            for i in range(10000):
                objects.append({
                    'id': i,
                    'data': list(range(100)),
                    'name': f"object_{i}"
                })
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            # 内存增长不应超过100MB
            assert memory_increase < 100
            del objects  # 清理内存
            
            return True
        except Exception as e:
            logger.error(f"Memory usage test failed: {e}")
            return False
    
    def show_test_results(self):
        """显示测试结果"""
        duration = datetime.now() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        print(f"⏱️  总耗时: {duration.total_seconds():.2f} 秒")
        print(f"📋 总测试数: {self.total_tests}")
        print(f"✅ 通过: {self.passed_tests}")
        print(f"❌ 失败: {self.failed_tests}")
        print(f"📈 成功率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        
        # 显示失败的测试
        failed_tests = [r for r in self.test_results if '❌' in r['status']]
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test.get('error', 'Unknown error')}")
        
        # 显示详细的测试结果
        print(f"\n📝 详细结果:")
        for result in self.test_results:
            print(f"   {result['status']} {result['test']} ({result['duration']:.2f}s)")
        
        # 总结
        print("\n" + "=" * 60)
        if self.passed_tests == self.total_tests:
            print("🎉 所有测试通过！系统准备就绪！")
        else:
            print("⚠️  部分测试失败，请检查上述错误信息")
        print("=" * 60)


async def main():
    """主函数"""
    try:
        # 创建测试套件
        test_suite = SystemTestSuite()
        
        # 运行所有测试
        success = await test_suite.run_all_tests()
        
        # 根据测试结果设置退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    print("AI量化交易系统 - 完整系统测试")
    print(f"Python版本: {sys.version}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行测试
    asyncio.run(main())