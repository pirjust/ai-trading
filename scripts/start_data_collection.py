#!/usr/bin/env python3
"""
数据采集服务启动脚本
用于启动实时数据采集和WebSocket服务
"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings
from data.websocket_collector import WebSocketCollector
from data.rest_collector import RestCollector
from monitoring.system_monitor import SystemMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCollectionService:
    def __init__(self):
        self.settings = get_settings()
        self.collectors = []
        self.monitor = SystemMonitor()
        
    async def setup_collectors(self):
        """设置数据采集器"""
        logger.info("设置数据采集器...")
        
        # 币安WebSocket采集器
        binance_ws = WebSocketCollector(
            exchange="binance",
            symbols=["btcusdt", "ethusdt", "adausdt"],
            channels=["trade", "kline_1m", "depth"]
        )
        self.collectors.append(binance_ws)
        
        # 欧意WebSocket采集器
        okx_ws = WebSocketCollector(
            exchange="okx",
            symbols=["BTC-USDT", "ETH-USDT", "ADA-USDT"],
            channels=["trades", "candle1m", "books"]
        )
        self.collectors.append(okx_ws)
        
        # REST API采集器（用于补充数据）
        rest_collector = RestCollector()
        self.collectors.append(rest_collector)
        
        logger.info(f"已设置 {len(self.collectors)} 个数据采集器")
    
    async def start_collectors(self):
        """启动所有采集器"""
        logger.info("启动数据采集器...")
        
        tasks = []
        for collector in self.collectors:
            try:
                task = asyncio.create_task(collector.start())
                tasks.append(task)
                logger.info(f"启动采集器: {collector.__class__.__name__}")
            except Exception as e:
                logger.error(f"启动采集器失败: {e}")
        
        return tasks
    
    async def start_monitoring(self):
        """启动系统监控"""
        logger.info("启动系统监控...")
        
        try:
            await self.monitor.start()
            logger.info("系统监控已启动")
        except Exception as e:
            logger.error(f"启动系统监控失败: {e}")
    
    async def run(self):
        """运行数据采集服务"""
        logger.info("🚀 启动AI量化交易数据采集服务")
        
        try:
            # 设置采集器
            await self.setup_collectors()
            
            # 启动监控
            await self.start_monitoring()
            
            # 启动采集器
            tasks = await self.start_collectors()
            
            if not tasks:
                logger.error("没有成功启动任何采集器")
                return
            
            logger.info("✅ 数据采集服务启动完成")
            
            # 等待所有任务
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭服务...")
        except Exception as e:
            logger.error(f"服务运行异常: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止服务"""
        logger.info("正在停止数据采集服务...")
        
        # 停止所有采集器
        for collector in self.collectors:
            try:
                await collector.stop()
                logger.info(f"停止采集器: {collector.__class__.__name__}")
            except Exception as e:
                logger.error(f"停止采集器失败: {e}")
        
        # 停止监控
        try:
            await self.monitor.stop()
            logger.info("系统监控已停止")
        except Exception as e:
            logger.error(f"停止系统监控失败: {e}")
        
        logger.info("✅ 数据采集服务已完全停止")

async def main():
    """主函数"""
    service = DataCollectionService()
    
    try:
        await service.run()
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())