"""
脚本工具模块
提供系统初始化、数据迁移、测试等脚本功能
"""

__version__ = "1.0.0"
__author__ = "AI Trading Team"

from .init_database import init_database
from .init_data import init_default_data
from .backup_script import backup_database
from .deploy_check import check_deployment_environment

__all__ = ["init_database", "init_default_data", "backup_database", "check_deployment_environment"]