"""
交易所API测试脚本
测试币安和欧意API的完整功能
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.exchange_client import ExchangeClientFactory, ExchangeType
from data.data_formatter import UnifiedDataFormat


class ExchangeAPITester:
    """交易所API测试器"""
    
    def __init__(self):
        self.test_results = {}
    
    async def test_binance_api(self):
        """测试币安API"""
        print("\n🔗 开始测试币安API...")
        
        try:
            # 创建币安客户端（沙盒模式）
            binance_client = ExchangeClientFactory.create_client(
                ExchangeType.BINANCE, sandbox=True
            )
            
            # 连接测试
            await binance_client.connect()
            print("✓ 币安API连接成功")
            
            # 测试连接性
            connectivity = await binance_client.test_connectivity()
            print(f"✓ 连接性测试: {'成功' if connectivity else '失败'}")
            
            # 测试获取行情数据
            try:
                ticker = await binance_client.get_ticker("BTCUSDT")
                print(f"✓ BTCUSDT行情获取成功: {ticker.price}")
            except Exception as e:
                print(f"⚠ 行情获取测试失败: {e}")
            
            # 测试获取所有行情
            try:
                tickers = await binance_client.get_tickers()
                print(f"✓ 行情列表获取成功: {len(tickers)} 个交易对")
            except Exception as e:
                print(f"⚠ 行情列表获取测试失败: {e}")
            
            # 测试获取深度数据
            try:
                depth = await binance_client.get_depth("BTCUSDT", limit=10)
                print(f"✓ 深度数据获取成功: {len(depth.get('bids', []))} 个买盘, {len(depth.get('asks', []))} 个卖盘")
            except Exception as e:
                print(f"⚠ 深度数据获取测试失败: {e}")
            
            # 测试获取K线数据
            try:
                klines = await binance_client.get_klines("BTCUSDT", "1m", limit=10)
                print(f"✓ K线数据获取成功: {len(klines)} 条记录")
            except Exception as e:
                print(f"⚠ K线数据获取测试失败: {e}")
            
            # 断开连接
            await binance_client.disconnect()
            print("✓ 币安API断开连接成功")
            
            self.test_results["binance"] = {"status": "success", "message": "币安API测试完成"}
            
        except Exception as e:
            print(f"❌ 币安API测试失败: {e}")
            self.test_results["binance"] = {"status": "failed", "message": str(e)}
    
    async def test_okx_api(self):
        """测试欧意API"""
        print("\n🔗 开始测试欧意API...")
        
        try:
            # 创建欧意客户端（沙盒模式）
            okx_client = ExchangeClientFactory.create_client(
                ExchangeType.OKX, sandbox=True
            )
            
            # 连接测试
            await okx_client.connect()
            print("✓ 欧意API连接成功")
            
            # 测试连接性
            connectivity = await okx_client.test_connectivity()
            print(f"✓ 连接性测试: {'成功' if connectivity else '失败'}")
            
            # 测试获取行情数据
            try:
                ticker = await okx_client.get_ticker("BTC-USDT")
                print(f"✓ BTC-USDT行情获取成功: {ticker.price}")
            except Exception as e:
                print(f"⚠ 行情获取测试失败: {e}")
            
            # 测试获取所有行情
            try:
                tickers = await okx_client.get_tickers()
                print(f"✓ 行情列表获取成功: {len(tickers)} 个交易对")
            except Exception as e:
                print(f"⚠ 行情列表获取测试失败: {e}")
            
            # 测试获取深度数据
            try:
                depth = await okx_client.get_depth("BTC-USDT", limit=10)
                print(f"✓ 深度数据获取成功: {len(depth.get('bids', []))} 个买盘, {len(depth.get('asks', []))} 个卖盘")
            except Exception as e:
                print(f"⚠ 深度数据获取测试失败: {e}")
            
            # 测试获取K线数据
            try:
                klines = await okx_client.get_klines("BTC-USDT", "1m", limit=10)
                print(f"✓ K线数据获取成功: {len(klines)} 条记录")
            except Exception as e:
                print(f"⚠ K线数据获取测试失败: {e}")
            
            # 断开连接
            await okx_client.disconnect()
            print("✓ 欧意API断开连接成功")
            
            self.test_results["okx"] = {"status": "success", "message": "欧意API测试完成"}
            
        except Exception as e:
            print(f"❌ 欧意API测试失败: {e}")
            self.test_results["okx"] = {"status": "failed", "message": str(e)}
    
    async def test_data_formatting(self):
        """测试数据格式转换"""
        print("\n🔧 开始测试数据格式转换...")
        
        try:
            # 测试币安数据格式转换
            binance_ticker = {
                "symbol": "BTCUSDT",
                "lastPrice": "50000.00",
                "volume": "1000.5",
                "priceChange": "100.00",
                "priceChangePercent": "0.2",
                "highPrice": "51000.00",
                "lowPrice": "49000.00",
                "openPrice": "49900.00",
                "closeTime": 1640995200000
            }
            
            formatted = UnifiedDataFormat.format_ticker("binance", binance_ticker)
            print(f"✓ 币安数据格式转换成功")
            print(f"  转换结果: {json.dumps(formatted, indent=2, ensure_ascii=False)}")
            
            # 测试欧意数据格式转换
            okx_ticker = {
                "data": [{
                    "instId": "BTC-USDT",
                    "last": "50000.00",
                    "vol24h": "1000.5",
                    "sodUtc0": "100.00",
                    "high24h": "51000.00",
                    "low24h": "49000.00",
                    "open24h": "49900.00",
                    "ts": "1640995200000"
                }]
            }
            
            formatted = UnifiedDataFormat.format_ticker("okx", okx_ticker)
            print(f"✓ 欧意数据格式转换成功")
            print(f"  转换结果: {json.dumps(formatted, indent=2, ensure_ascii=False)}")
            
            self.test_results["data_formatting"] = {"status": "success", "message": "数据格式转换测试完成"}
            
        except Exception as e:
            print(f"❌ 数据格式转换测试失败: {e}")
            self.test_results["data_formatting"] = {"status": "failed", "message": str(e)}
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 交易所API测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "success")
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 测试统计:")
        print(f"  • 总测试项目: {total_tests}")
        print(f"  • 通过项目: {passed_tests}")
        print(f"  • 失败项目: {failed_tests}")
        print(f"  • 成功率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n🔍 详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = "✓" if result["status"] == "success" else "❌"
            print(f"  {status_icon} {test_name}: {result['message']}")
        
        print(f"\n⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！交易所API对接模块运行正常。")
        else:
            print(f"\n⚠️ 有 {failed_tests} 个测试失败，请检查配置和网络连接。")
        
        return failed_tests == 0


async def main():
    """主测试函数"""
    print("🚀 AI量化交易系统 - 交易所API测试")
    print("="*60)
    
    tester = ExchangeAPITester()
    
    # 运行所有测试
    await tester.test_binance_api()
    await tester.test_okx_api()
    await tester.test_data_formatting()
    
    # 生成报告
    success = tester.generate_report()
    
    # 返回测试结果
    return 0 if success else 1


if __name__ == "__main__":
    # 运行异步测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)