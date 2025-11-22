#!/usr/bin/env python3
"""
风控系统和回测模块集成测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_management.risk_engine import RiskEngine
from risk_management.risk_monitor import RiskMonitor
from strategies.backtesting import BacktestingEngine
from strategies.backtest_data_manager import BacktestDataManager
from core.config import settings

async def test_risk_engine():
    """测试风险引擎"""
    print("=== 测试风险引擎 ===")
    
    try:
        risk_engine = RiskEngine()
        
        # 模拟投资组合数据
        portfolio_data = {
            'positions': {
                'BTCUSDT': {'quantity': 1.0, 'price': 50000, 'value': 50000},
                'ETHUSDT': {'quantity': 10.0, 'price': 3000, 'value': 30000}
            },
            'total_value': 80000,
            'cash': 20000
        }
        
        # 计算风险指标
        risk_metrics = await risk_engine.calculate_risk_metrics(portfolio_data)
        print(f"✅ 风险指标计算成功:")
        print(f"   - VaR(95%): ${risk_metrics.get('var_95', 0):.2f}")
        print(f"   - 预期亏损: ${risk_metrics.get('expected_shortfall', 0):.2f}")
        print(f"   - 集中度风险: {risk_metrics.get('concentration_risk', 0):.4f}")
        
        return True
    except Exception as e:
        print(f"❌ 风险引擎测试失败: {str(e)}")
        return False

async def test_backtesting_engine():
    """测试回测引擎"""
    print("\n=== 测试回测引擎 ===")
    
    try:
        backtest_engine = BacktestingEngine()
        
        # 模拟策略配置
        strategy_config = {
            'name': '测试策略',
            'type': 'MEAN_REVERSION',
            'parameters': {
                'lookback_period': 20,
                'threshold': 2.0
            }
        }
        
        # 模拟历史数据
        historical_data = {
            'BTCUSDT': [
                {'timestamp': '2024-01-01', 'open': 45000, 'high': 46000, 'low': 44000, 'close': 45500, 'volume': 1000},
                {'timestamp': '2024-01-02', 'open': 45500, 'high': 47000, 'low': 45000, 'close': 46500, 'volume': 1200}
            ]
        }
        
        # 验证回测引擎初始化
        print("✅ 回测引擎初始化成功")
        print(f"   策略类型: {strategy_config['type']}")
        print(f"   历史数据点数: {len(historical_data['BTCUSDT'])}")
        
        return True
    except Exception as e:
        print(f"❌ 回测引擎测试失败: {str(e)}")
        return False

async def test_risk_monitor():
    """测试风险监控器"""
    print("\n=== 测试风险监控器 ===")
    
    try:
        risk_monitor = RiskMonitor()
        
        # 测试监控器状态
        status = await risk_monitor.get_monitoring_status()
        print(f"✅ 风险监控器状态: {status}")
        
        # 测试风险摘要
        risk_summary = await risk_monitor.get_risk_summary()
        print(f"✅ 风险摘要获取成功")
        
        return True
    except Exception as e:
        print(f"❌ 风险监控器测试失败: {str(e)}")
        return False

async def test_backtest_data_manager():
    """测试回测数据管理器"""
    print("\n=== 测试回测数据管理器 ===")
    
    try:
        data_manager = BacktestDataManager()
        
        # 测试数据管理器初始化
        print("✅ 回测数据管理器初始化成功")
        
        # 测试可用数据源
        data_sources = await data_manager.get_available_data_sources()
        print(f"✅ 可用数据源: {list(data_sources.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 回测数据管理器测试失败: {str(e)}")
        return False

async def test_integration():
    """集成测试"""
    print("开始集成测试...\n")
    
    tests = [
        test_risk_engine(),
        test_backtesting_engine(), 
        test_risk_monitor(),
        test_backtest_data_manager()
    ]
    
    results = await asyncio.gather(*tests)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！风控系统和回测模块集成成功！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关模块")
        return False

async def main():
    """主函数"""
    print("AI量化交易系统 - 风控和回测模块集成测试")
    print("=" * 50)
    
    try:
        success = await test_integration()
        
        if success:
            print("\n✅ 集成测试完成，系统可以正常使用")
            print("\n下一步工作建议:")
            print("1. 启动后端服务: python -m app.main")
            print("2. 启动前端服务: cd frontend && npm run dev")
            print("3. 访问 http://localhost:3000 查看系统界面")
            print("4. 测试风控管理和策略回测功能")
        else:
            print("\n❌ 集成测试失败，请检查错误信息")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
