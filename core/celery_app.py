"""
Celery异步任务配置
负责处理后台任务、定时任务和异步执行
"""

import os
from celery import Celery
from celery.schedules import crontab
from .config import settings


# 创建Celery应用
celery_app = Celery(
    "ai_trading",
    broker=settings.redis.url,
    backend=settings.redis.url,
    include=[
        "tasks.data_collection",
        "tasks.strategy_execution", 
        "tasks.risk_monitoring",
        "tasks.backtesting"
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "tasks.data_collection.*": {"queue": "data"},
        "tasks.strategy_execution.*": {"queue": "trading"},
        "tasks.risk_monitoring.*": {"queue": "risk"},
        "tasks.backtesting.*": {"queue": "backtest"},
    },
    
    # 定时任务配置
    beat_schedule={
        # 数据采集任务
        "collect-market-data": {
            "task": "tasks.data_collection.collect_market_data",
            "schedule": 60.0,  # 每60秒执行一次
            "options": {"queue": "data"}
        },
        
        # 策略执行任务
        "execute-strategies": {
            "task": "tasks.strategy_execution.execute_strategies",
            "schedule": 10.0,  # 每10秒执行一次
            "options": {"queue": "trading"}
        },
        
        # 风险监控任务
        "monitor-risk": {
            "task": "tasks.risk_monitoring.monitor_risk",
            "schedule": 30.0,  # 每30秒执行一次
            "options": {"queue": "risk"}
        },
        
        # 每日备份任务
        "daily-backup": {
            "task": "tasks.backup.daily_backup",
            "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
            "options": {"queue": "backup"}
        },
        
        # 性能报告任务
        "performance-report": {
            "task": "tasks.reporting.daily_performance_report",
            "schedule": crontab(hour=18, minute=0),  # 每天下午6点执行
            "options": {"queue": "report"}
        }
    },
    
    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # 并发配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# 任务模块定义
@celery_app.task(bind=True)
def collect_market_data(self):
    """市场数据采集任务"""
    from tasks.data_collection import collect_market_data_impl
    return collect_market_data_impl()


@celery_app.task(bind=True)
def execute_strategies(self):
    """策略执行任务"""
    from tasks.strategy_execution import execute_strategies_impl
    return execute_strategies_impl()


@celery_app.task(bind=True)
def monitor_risk(self):
    """风险监控任务"""
    from tasks.risk_monitoring import monitor_risk_impl
    return monitor_risk_impl()


@celery_app.task(bind=True)
def daily_backup(self):
    """每日备份任务"""
    from tasks.backup import daily_backup_impl
    return daily_backup_impl()


@celery_app.task(bind=True)
def daily_performance_report(self):
    """每日性能报告任务"""
    from tasks.reporting import daily_performance_report_impl
    return daily_performance_report_impl()


# 错误处理
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, exc, traceback):
    """任务失败处理"""
    from core.logging import logger
    logger.error(f"任务 {task_id} 执行失败: {exc}")
    
    # 发送警报
    from tasks.alerting import send_alert
    send_alert.delay(
        f"任务执行失败: {task_id}",
        f"错误信息: {exc}",
        "high"
    )


if __name__ == "__main__":
    # Celery应用测试
    celery_app.start()