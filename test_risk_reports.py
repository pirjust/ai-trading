#!/usr/bin/env python3
"""
风险报告系统测试脚本
测试风险报告生成、查看、导出等功能
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from risk_management.risk_reporter import get_risk_reporter, ReportType
from risk_management.risk_monitor import get_risk_monitor

async def test_risk_report_system():
    """测试风险报告系统"""
    print("=== 风险报告系统测试 ===")
    
    try:
        # 初始化风险报告器
        reporter = await get_risk_reporter()
        print("✓ 风险报告器初始化成功")
        
        # 测试生成日报
        print("\n1. 测试生成日报...")
        daily_report = await reporter.generate_report(ReportType.DAILY)
        print(f"✓ 日报生成成功 - ID: {daily_report.report_id}")
        print(f"   报告类型: {daily_report.report_type.value}")
        print(f"   时间范围: {daily_report.start_time} - {daily_report.end_time}")
        print(f"   活跃警报: {daily_report.active_alerts}")
        print(f"   危急警报: {daily_report.critical_alerts}")
        
        # 测试生成周报
        print("\n2. 测试生成周报...")
        weekly_report = await reporter.generate_report(ReportType.WEEKLY)
        print(f"✓ 周报生成成功 - ID: {weekly_report.report_id}")
        
        # 测试生成月报
        print("\n3. 测试生成月报...")
        monthly_report = await reporter.generate_report(ReportType.MONTHLY)
        print(f"✓ 月报生成成功 - ID: {monthly_report.report_id}")
        
        # 测试生成实时报告
        print("\n4. 测试生成实时报告...")
        realtime_report = await reporter.generate_report(ReportType.REAL_TIME)
        print(f"✓ 实时报告生成成功 - ID: {realtime_report.report_id}")
        
        # 测试报告列表
        print("\n5. 测试报告列表...")
        reports = list(reporter.reports.values())
        print(f"✓ 报告列表获取成功 - 总计: {len(reports)} 份报告")
        
        # 测试报告详情
        print("\n6. 测试报告详情...")
        if reports:
            report_detail = await reporter.get_report_detail(reports[0].report_id)
            print(f"✓ 报告详情获取成功")
            print(f"   风险指标数量: {len(report_detail.risk_metrics)}")
            print(f"   仓位风险数量: {len(report_detail.position_risks)}")
            print(f"   建议措施数量: {len(report_detail.recommendations)}")
        
        # 测试导出功能
        print("\n7. 测试报告导出...")
        if reports:
            # JSON导出
            json_content = await reporter.export_report(reports[0], "json")
            print(f"✓ JSON导出成功 - 内容长度: {len(json_content)} 字符")
            
            # CSV导出
            csv_content = await reporter.export_report(reports[0], "csv")
            print(f"✓ CSV导出成功 - 内容长度: {len(csv_content)} 字符")
            
            # HTML导出
            html_content = await reporter.export_report(reports[0], "html")
            print(f"✓ HTML导出成功 - 内容长度: {len(html_content)} 字符")
        
        # 测试自定义时间范围
        print("\n8. 测试自定义时间范围...")
        custom_start = datetime.now() - timedelta(hours=24)
        custom_end = datetime.now()
        custom_report = await reporter.generate_report(
            ReportType.DAILY, 
            custom_start, 
            custom_end
        )
        print(f"✓ 自定义时间范围报告生成成功")
        
        # 测试风险指标计算
        print("\n9. 测试风险指标计算...")
        risk_metrics = await reporter.calculate_risk_metrics()
        print(f"✓ 风险指标计算成功 - 指标数量: {len(risk_metrics)}")
        
        # 测试风险分析
        print("\n10. 测试风险分析...")
        risk_analysis = await reporter.analyze_risk_factors()
        print(f"✓ 风险分析成功 - 分析项数量: {len(risk_analysis)}")
        
        print("\n=== 所有测试通过! ===")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """测试API集成"""
    print("\n=== API集成测试 ===")
    
    try:
        # 测试风险监控器集成
        monitor = await get_risk_monitor()
        print("✓ 风险监控器集成成功")
        
        # 测试数据模拟
        await monitor.simulate_risk_data()
        print("✓ 风险数据模拟成功")
        
        # 测试实时监控
        await monitor.start_monitoring()
        print("✓ 实时监控启动成功")
        
        # 等待几秒收集数据
        await asyncio.sleep(5)
        
        # 获取当前状态
        status = await monitor.get_status()
        print(f"✓ 监控状态获取成功 - 活跃警报: {status.get('active_alerts', 0)}")
        
        # 停止监控
        await monitor.stop_monitoring()
        print("✓ 实时监控停止成功")
        
        print("\n=== API集成测试通过! ===")
        return True
        
    except Exception as e:
        print(f"✗ API集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("开始风险报告系统测试...")
    
    # 测试风险报告系统
    report_test_passed = await test_risk_report_system()
    
    # 测试API集成
    api_test_passed = await test_api_integration()
    
    # 输出测试结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print(f"风险报告系统测试: {'通过' if report_test_passed else '失败'}")
    print(f"API集成测试: {'通过' if api_test_passed else '失败'}")
    
    if report_test_passed and api_test_passed:
        print("\n🎉 所有测试通过! 风险报告系统运行正常")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)