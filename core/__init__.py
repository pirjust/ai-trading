"""
AI量化交易系统核心模块
提供系统基础功能、数据库连接、配置管理等核心组件
"""

__version__ = "1.0.0"
__author__ = "AI Trading Team"

from .config import settings
from .database import DatabaseManager
from .celery_app import celery_app

__all__ = ["settings", "DatabaseManager", "celery_app"]