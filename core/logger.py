"""
日志管理模块
统一处理系统日志记录、格式化和输出
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .config import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 日志配置
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                },
                'colored': {
                    '()': ColoredFormatter,
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': settings.log_level.upper(),
                    'formatter': 'colored' if sys.stdout.isatty() else 'simple',
                    'stream': sys.stdout
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': log_dir / 'app.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': log_dir / 'error.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                },
                'trading_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': log_dir / 'trading.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                },
                'risk_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': log_dir / 'risk.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                }
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['console', 'file', 'error_file'],
                    'level': settings.log_level.upper(),
                    'propagate': False
                },
                'trading': {
                    'handlers': ['console', 'file', 'trading_file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'risk': {
                    'handlers': ['console', 'file', 'risk_file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'uvicorn': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'sqlalchemy.engine': {
                    'handlers': ['file'],
                    'level': 'WARNING',
                    'propagate': False
                }
            }
        }
        
        # 应用配置
        logging.config.dictConfig(config)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_trading_event(self, event_type: str, symbol: str, details: Dict[str, Any]):
        """记录交易事件"""
        trading_logger = self.get_logger('trading')
        
        log_message = f"[{event_type.upper()}] {symbol} - {details}"
        
        if event_type in ['buy', 'sell']:
            trading_logger.info(log_message)
        elif event_type in ['error', 'failed']:
            trading_logger.error(log_message)
        else:
            trading_logger.debug(log_message)
    
    def log_risk_event(self, risk_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """记录风险事件"""
        risk_logger = self.get_logger('risk')
        
        log_message = f"[{risk_type.upper()}] {severity.upper()} - {message}"
        if details:
            log_message += f" - Details: {details}"
        
        if severity.lower() in ['critical', 'high']:
            risk_logger.error(log_message)
        elif severity.lower() == 'medium':
            risk_logger.warning(log_message)
        else:
            risk_logger.info(log_message)
    
    def create_performance_log(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """记录性能日志"""
        main_logger = self.get_logger('performance')
        
        log_message = f"[PERFORMANCE] {operation} completed in {duration:.2f}s"
        if details:
            log_message += f" - {details}"
        
        if duration > 5.0:
            main_logger.warning(log_message)
        else:
            main_logger.info(log_message)


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logger_manager.get_logger(name)


def setup_trading_logger(name: str) -> logging.Logger:
    """设置交易专用日志器"""
    logger = logging.getLogger(f'trading.{name}')
    return logger


def setup_risk_logger(name: str) -> logging.Logger:
    """设置风控专用日志器"""
    logger = logging.getLogger(f'risk.{name}')
    return logger


# 便捷函数
def log_info(message: str, name: str = 'app'):
    """记录信息日志"""
    get_logger(name).info(message)


def log_warning(message: str, name: str = 'app'):
    """记录警告日志"""
    get_logger(name).warning(message)


def log_error(message: str, name: str = 'app'):
    """记录错误日志"""
    get_logger(name).error(message)


def log_debug(message: str, name: str = 'app'):
    """记录调试日志"""
    get_logger(name).debug(message)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger("test")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.debug("这是一条调试日志")
    
    # 测试交易日志
    logger_manager.log_trading_event("buy", "BTCUSDT", {"price": 50000, "amount": 0.1})
    logger_manager.log_trading_event("sell", "ETHUSDT", {"price": 3000, "amount": 1.0})
    
    # 测试风险日志
    logger_manager.log_risk_event("position_limit", "high", "仓位超过限制", {"symbol": "BTCUSDT", "position_ratio": 0.9})
    logger_manager.log_risk_event("margin_call", "critical", "保证金不足", {"account": "main", "margin_ratio": 0.05})
    
    # 测试性能日志
    logger_manager.create_performance_log("api_call", 0.5, {"endpoint": "/api/v1/klines"})
    logger_manager.create_performance_log("strategy_execution", 8.2, {"strategy": "ai_lstm"})
    
    print("日志系统测试完成")