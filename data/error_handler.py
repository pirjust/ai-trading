"""
API错误处理和重试机制
提供统一的错误处理、重试逻辑和异常管理
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"        # 网络错误
    API_ERROR = "api_error"                # API错误
    AUTH_ERROR = "auth_error"              # 认证错误
    RATE_LIMIT_ERROR = "rate_limit_error"  # 限流错误
    TIMEOUT_ERROR = "timeout_error"        # 超时错误
    VALIDATION_ERROR = "validation_error"   # 数据验证错误
    UNKNOWN_ERROR = "unknown_error"         # 未知错误


class ExchangeErrorCode(Enum):
    """交易所错误代码枚举"""
    # 币安错误代码
    BINANCE_INVALID_API_KEY = -2014
    BINANCE_INVALID_SIGNATURE = -1022
    BINANCE_TOO_MANY_REQUESTS = -1003
    BINANCE_ORDER_NOT_FOUND = -2013
    
    # 欧意错误代码
    OKX_INVALID_API_KEY = "50113"
    OKX_INVALID_SIGNATURE = "50114"
    OKX_RATE_LIMIT = "50116"
    OKX_ORDER_NOT_FOUND = "51020"
    
    # Bybit错误代码
    BYBIT_INVALID_API_KEY = "10001"
    BYBIT_INVALID_SIGNATURE = "10002"
    BYBIT_RATE_LIMIT = "10006"
    BYBIT_ORDER_NOT_FOUND = "20001"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0  # 基础延迟时间（秒）
    max_delay: float = 60.0  # 最大延迟时间（秒）
    backoff_factor: float = 2.0  # 退避因子
    jitter: bool = True  # 是否添加抖动
    
    # 针对不同错误类型的重试配置
    error_retry_config: Dict[ErrorType, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.error_retry_config is None:
            self.error_retry_config = {
                ErrorType.NETWORK_ERROR: {"max_retries": 5, "base_delay": 2.0},
                ErrorType.RATE_LIMIT_ERROR: {"max_retries": 3, "base_delay": 5.0},
                ErrorType.AUTH_ERROR: {"max_retries": 1, "base_delay": 1.0},
                ErrorType.API_ERROR: {"max_retries": 3, "base_delay": 1.0},
                ErrorType.TIMEOUT_ERROR: {"max_retries": 3, "base_delay": 3.0},
                ErrorType.VALIDATION_ERROR: {"max_retries": 1, "base_delay": 1.0},
                ErrorType.UNKNOWN_ERROR: {"max_retries": 2, "base_delay": 1.0}
            }


class ExchangeAPIError(Exception):
    """交易所API异常基类"""
    
    def __init__(self, 
                 exchange: str,
                 error_type: ErrorType,
                 message: str,
                 error_code: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        self.exchange = exchange
        self.error_type = error_type
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        super().__init__(f"[{exchange}] {error_type.value}: {message}")


class RateLimitError(ExchangeAPIError):
    """限流异常"""
    
    def __init__(self, exchange: str, message: str, retry_after: Optional[int] = None):
        super().__init__(exchange, ErrorType.RATE_LIMIT_ERROR, message)
        self.retry_after = retry_after


class AuthenticationError(ExchangeAPIError):
    """认证异常"""
    
    def __init__(self, exchange: str, message: str):
        super().__init__(exchange, ErrorType.AUTH_ERROR, message)


class NetworkError(ExchangeAPIError):
    """网络异常"""
    
    def __init__(self, exchange: str, message: str, original_exception: Optional[Exception] = None):
        super().__init__(exchange, ErrorType.NETWORK_ERROR, message, original_exception=original_exception)


class TimeoutError(ExchangeAPIError):
    """超时异常"""
    
    def __init__(self, exchange: str, message: str):
        super().__init__(exchange, ErrorType.TIMEOUT_ERROR, message)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, exchange: str, retry_config: Optional[RetryConfig] = None):
        self.exchange = exchange
        self.retry_config = retry_config or RetryConfig()
        self.error_stats = {
            error_type.value: {"count": 0, "last_occurrence": None}
            for error_type in ErrorType
        }
    
    def classify_error(self, exception: Exception) -> ErrorType:
        """分类错误类型"""
        if isinstance(exception, ExchangeAPIError):
            return exception.error_type
        
        # 网络相关错误
        if isinstance(exception, (ConnectionError, ConnectionRefusedError)):
            return ErrorType.NETWORK_ERROR
        
        # 超时错误
        if isinstance(exception, asyncio.TimeoutError):
            return ErrorType.TIMEOUT_ERROR
        
        # 其他异常
        return ErrorType.UNKNOWN_ERROR
    
    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """判断是否应该重试"""
        error_type = self.classify_error(exception)
        
        # 认证错误不重试
        if error_type == ErrorType.AUTH_ERROR:
            return False
        
        # 验证错误不重试
        if error_type == ErrorType.VALIDATION_ERROR:
            return False
        
        # 检查重试配置
        error_config = self.retry_config.error_retry_config.get(error_type, {})
        max_retries = error_config.get("max_retries", self.retry_config.max_retries)
        
        return retry_count < max_retries
    
    def calculate_retry_delay(self, exception: Exception, retry_count: int) -> float:
        """计算重试延迟时间"""
        error_type = self.classify_error(exception)
        
        # 获取特定错误类型的配置
        error_config = self.retry_config.error_retry_config.get(error_type, {})
        base_delay = error_config.get("base_delay", self.retry_config.base_delay)
        max_delay = error_config.get("max_delay", self.retry_config.max_delay)
        backoff_factor = error_config.get("backoff_factor", self.retry_config.backoff_factor)
        
        # 计算退避延迟
        delay = base_delay * (backoff_factor ** retry_count)
        
        # 添加抖动
        if self.retry_config.jitter:
            delay = delay * (0.5 + 0.5 * time.time() % 1)
        
        # 限制最大延迟
        return min(delay, max_delay)
    
    def record_error(self, exception: Exception):
        """记录错误统计"""
        error_type = self.classify_error(exception)
        self.error_stats[error_type.value]["count"] += 1
        self.error_stats[error_type.value]["last_occurrence"] = time.time()
        
        logger.warning(f"[{self.exchange}] 错误记录: {error_type.value} - {str(exception)}")
    
    def get_error_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取错误统计"""
        return self.error_stats
    
    def reset_stats(self):
        """重置错误统计"""
        for error_type in self.error_stats:
            self.error_stats[error_type]["count"] = 0
            self.error_stats[error_type]["last_occurrence"] = None


class RetryDecorator:
    """重试装饰器"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    def __call__(self, func: Callable):
        """装饰器实现"""
        async def wrapper(*args, **kwargs):
            retry_count = 0
            
            while True:
                try:
                    result = await func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    # 记录错误
                    self.error_handler.record_error(e)
                    
                    # 检查是否应该重试
                    if not self.error_handler.should_retry(e, retry_count):
                        logger.error(f"[{self.error_handler.exchange}] 达到最大重试次数: {retry_count}")
                        raise
                    
                    # 计算重试延迟
                    delay = self.error_handler.calculate_retry_delay(e, retry_count)
                    retry_count += 1
                    
                    logger.warning(f"[{self.error_handler.exchange}] 重试 {retry_count}/{self.error_handler.retry_config.max_retries}，延迟 {delay:.2f}秒")
                    
                    # 等待重试
                    await asyncio.sleep(delay)
        
        return wrapper


class ExchangeErrorParser:
    """交易所错误解析器"""
    
    @staticmethod
    def parse_binance_error(response_data: Dict[str, Any]) -> ExchangeAPIError:
        """解析币安错误"""
        error_code = response_data.get("code")
        error_msg = response_data.get("msg", "未知错误")
        
        if error_code == ExchangeErrorCode.BINANCE_INVALID_API_KEY.value:
            return AuthenticationError("binance", f"无效的API密钥: {error_msg}")
        elif error_code == ExchangeErrorCode.BINANCE_INVALID_SIGNATURE.value:
            return AuthenticationError("binance", f"无效的签名: {error_msg}")
        elif error_code == ExchangeErrorCode.BINANCE_TOO_MANY_REQUESTS.value:
            return RateLimitError("binance", f"请求过于频繁: {error_msg}")
        elif error_code == ExchangeErrorCode.BINANCE_ORDER_NOT_FOUND.value:
            return ExchangeAPIError("binance", ErrorType.API_ERROR, f"订单不存在: {error_msg}")
        else:
            return ExchangeAPIError("binance", ErrorType.API_ERROR, f"API错误: {error_msg}")
    
    @staticmethod
    def parse_okx_error(response_data: Dict[str, Any]) -> ExchangeAPIError:
        """解析欧意错误"""
        error_code = response_data.get("code")
        error_msg = response_data.get("msg", "未知错误")
        
        if error_code == ExchangeErrorCode.OKX_INVALID_API_KEY.value:
            return AuthenticationError("okx", f"无效的API密钥: {error_msg}")
        elif error_code == ExchangeErrorCode.OKX_INVALID_SIGNATURE.value:
            return AuthenticationError("okx", f"无效的签名: {error_msg}")
        elif error_code == ExchangeErrorCode.OKX_RATE_LIMIT.value:
            return RateLimitError("okx", f"请求过于频繁: {error_msg}")
        elif error_code == ExchangeErrorCode.OKX_ORDER_NOT_FOUND.value:
            return ExchangeAPIError("okx", ErrorType.API_ERROR, f"订单不存在: {error_msg}")
        else:
            return ExchangeAPIError("okx", ErrorType.API_ERROR, f"API错误: {error_msg}")
    
    @staticmethod
    def parse_bybit_error(response_data: Dict[str, Any]) -> ExchangeAPIError:
        """解析Bybit错误"""
        error_code = response_data.get("ret_code")
        error_msg = response_data.get("ret_msg", "未知错误")
        
        if error_code == ExchangeErrorCode.BYBIT_INVALID_API_KEY.value:
            return AuthenticationError("bybit", f"无效的API密钥: {error_msg}")
        elif error_code == ExchangeErrorCode.BYBIT_INVALID_SIGNATURE.value:
            return AuthenticationError("bybit", f"无效的签名: {error_msg}")
        elif error_code == ExchangeErrorCode.BYBIT_RATE_LIMIT.value:
            return RateLimitError("bybit", f"请求过于频繁: {error_msg}")
        elif error_code == ExchangeErrorCode.BYBIT_ORDER_NOT_FOUND.value:
            return ExchangeAPIError("bybit", ErrorType.API_ERROR, f"订单不存在: {error_msg}")
        else:
            return ExchangeAPIError("bybit", ErrorType.API_ERROR, f"API错误: {error_msg}")
    
    @staticmethod
    def parse_http_error(status_code: int, exchange: str) -> ExchangeAPIError:
        """解析HTTP错误"""
        if status_code == 401:
            return AuthenticationError(exchange, "HTTP 401: 认证失败")
        elif status_code == 403:
            return AuthenticationError(exchange, "HTTP 403: 权限不足")
        elif status_code == 429:
            return RateLimitError(exchange, "HTTP 429: 请求过于频繁")
        elif status_code >= 500:
            return NetworkError(exchange, f"HTTP {status_code}: 服务器错误")
        else:
            return ExchangeAPIError(exchange, ErrorType.API_ERROR, f"HTTP {status_code}: 未知错误")


# 使用示例
async def example_usage():
    """错误处理使用示例"""
    
    # 创建错误处理器
    error_handler = ErrorHandler("binance")
    retry_decorator = RetryDecorator(error_handler)
    
    @retry_decorator
    async def api_call_example():
        """模拟API调用"""
        # 模拟网络错误
        if time.time() % 2 < 1:
            raise ConnectionError("网络连接失败")
        
        return {"data": "success"}
    
    try:
        result = await api_call_example()
        print(f"API调用成功: {result}")
    except Exception as e:
        print(f"API调用失败: {e}")
    
    # 查看错误统计
    stats = error_handler.get_error_stats()
    print("错误统计:")
    for error_type, stats_data in stats.items():
        if stats_data["count"] > 0:
            print(f"  {error_type}: {stats_data['count']}次")


if __name__ == "__main__":
    asyncio.run(example_usage())