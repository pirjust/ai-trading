# 交易所API集成文档

## 概述

本项目实现了对主流加密货币交易所的API集成，目前支持币安(Binance)和欧意(OKX)交易所。提供统一的接口进行市场数据获取、账户管理、交易执行等操作。

## 支持的交易所

- ✅ **币安 (Binance)** - 全球最大的加密货币交易所
- ✅ **欧意 (OKX)** - 亚洲领先的加密货币交易所
- 🔄 **Bybit** - 合约交易平台（开发中）

## 核心架构

### 类结构图

```
ExchangeClientFactory
    ├── BaseExchangeClient (抽象基类)
    │   ├── BinanceClient
    │   └── OKXClient
    └── ExchangeType (枚举)

DataExchangeAPI (具体实现)
    ├── BinanceAPI
    └── OKXAPI

DataFormatter (数据转换)
    └── UnifiedDataFormat

ErrorHandler (错误处理)
    └── RetryDecorator
```

### 统一数据格式

项目使用统一的数据格式来屏蔽不同交易所的API差异：

- `UnifiedTicker` - 统一行情数据
- `UnifiedOrder` - 统一订单数据  
- `UnifiedPosition` - 统一持仓数据
- `UnifiedBalance` - 统一余额数据

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

复制环境变量模板：

```bash
cp .env.example .env
```

编辑`.env`文件，填入实际的API密钥：

```env
# 币安API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# 欧意API配置  
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here
```

### 3. 基本使用示例

```python
import asyncio
from data.exchange_client import ExchangeClientFactory, ExchangeType

async def main():
    # 创建币安客户端（沙盒模式）
    client = ExchangeClientFactory.create_client(ExchangeType.BINANCE, sandbox=True)
    
    try:
        # 连接交易所
        await client.connect()
        
        # 获取行情数据
        ticker = await client.get_ticker("BTCUSDT")
        print(f"BTCUSDT价格: {ticker.price}")
        
        # 获取账户余额
        balances = await client.get_balance()
        for balance in balances:
            if balance.total > 0:
                print(f"{balance.asset}: {balance.total}")
                
    finally:
        # 断开连接
        await client.disconnect()

# 运行示例
asyncio.run(main())
```

## API接口说明

### 市场数据接口

#### 获取单个交易对行情

```python
async def get_ticker(self, symbol: str) -> UnifiedTicker:
    """获取指定交易对的实时行情"""
```

**参数:**
- `symbol`: 交易对符号，如 "BTCUSDT"

**返回:** UnifiedTicker对象，包含价格、涨跌幅等信息

#### 获取所有交易对行情

```python
async def get_tickers(self) -> List[UnifiedTicker]:
    """获取所有交易对的实时行情"""
```

#### 获取深度数据

```python
async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
    """获取指定交易对的深度数据"""
```

**参数:**
- `symbol`: 交易对符号
- `limit`: 深度数量，默认100档

#### 获取K线数据

```python
async def get_klines(self, symbol: str, interval: str, limit: int = 1000) -> List[List[Any]]:
    """获取K线数据"""
```

**参数:**
- `symbol`: 交易对符号
- `interval`: K线周期，如 "1m", "5m", "1h", "1d"
- `limit`: 数据条数，默认1000条

### 账户管理接口

#### 获取账户余额

```python
async def get_balance(self) -> List[UnifiedBalance]:
    """获取账户所有资产余额"""
```

#### 创建订单

```python
async def create_order(self, symbol: str, side: OrderSide, 
                      order_type: OrderType, quantity: float,
                      price: float = None) -> UnifiedOrder:
    """创建新订单"""
```

**参数:**
- `symbol`: 交易对符号
- `side`: 订单方向（BUY/SELL）
- `order_type`: 订单类型（MARKET/LIMIT）
- `quantity`: 订单数量
- `price`: 订单价格（限价单必填）

#### 取消订单

```python
async def cancel_order(self, symbol: str, order_id: str) -> bool:
    """取消指定订单"""
```

#### 查询订单

```python
async def get_order(self, symbol: str, order_id: str) -> UnifiedOrder:
    """查询订单详情"""
```

#### 获取当前挂单

```python
async def get_open_orders(self, symbol: str = None) -> List[UnifiedOrder]:
    """获取当前所有挂单"""
```

### 工具接口

#### 测试连接性

```python
async def test_connectivity(self) -> bool:
    """测试API连接是否正常"""
```

## 错误处理机制

### 错误类型

系统定义了完整的错误分类体系：

- `NetworkError` - 网络连接错误
- `AuthenticationError` - 认证错误
- `RateLimitError` - 限流错误
- `TimeoutError` - 超时错误
- `APIError` - 交易所API错误

### 重试机制

系统内置智能重试机制：

```python
from data.error_handler import RetryDecorator, ErrorHandler

# 创建错误处理器
error_handler = ErrorHandler("binance")
retry_decorator = RetryDecorator(error_handler)

@retry_decorator
async def api_call():
    # API调用会自动重试
    pass
```

**重试策略:**
- 网络错误：最多重试5次，指数退避
- 限流错误：最多重试3次，固定延迟
- 认证错误：不重试，立即失败
- 验证错误：不重试，立即失败

## 数据格式转换

### 统一数据格式

所有交易所返回的数据都会被转换为统一的内部格式：

```python
from data.data_formatter import UnifiedDataFormat

# 转换币安行情数据
formatted = UnifiedDataFormat.format_ticker("binance", raw_data)

# 转换欧意订单数据
formatted = UnifiedDataFormat.format_order("okx", raw_data)
```

### 数据验证

```python
from data.data_formatter import DataFormatter

# 验证数据格式
is_valid = DataFormatter.validate_data_format(data, "ticker")

# 标准化符号
normalized_symbol = DataFormatter.normalize_symbol("btcusdt", "binance")
```

## 沙盒测试

所有交易所都支持沙盒环境测试：

```python
# 使用沙盒环境
client = ExchangeClientFactory.create_client(ExchangeType.BINANCE, sandbox=True)
```

**沙盒环境URL:**
- 币安: `https://testnet.binance.vision`
- 欧意: 使用实盘域名，但数据为测试数据

## 测试

### 运行API测试

```bash
python scripts/test_exchange_api.py
```

### 测试内容

1. **连接性测试** - 验证API连接
2. **行情数据测试** - 获取实时行情
3. **深度数据测试** - 获取买卖盘深度
4. **K线数据测试** - 获取历史K线
5. **数据格式测试** - 验证数据转换

## 最佳实践

### 1. 使用上下文管理器

```python
async with ExchangeClientFactory.create_client(ExchangeType.BINANCE) as client:
    # 自动管理连接生命周期
    ticker = await client.get_ticker("BTCUSDT")
```

### 2. 错误处理

```python
try:
    await client.create_order(...)
except AuthenticationError as e:
    # 认证错误，需要重新配置API密钥
    logger.error("API认证失败")
except RateLimitError as e:
    # 限流错误，等待重试
    await asyncio.sleep(e.retry_after)
```

### 3. 性能优化

- 使用连接池复用HTTP连接
- 批量获取数据减少API调用
- 合理设置请求频率限制

## 配置说明

### 配置文件位置

- `config/api_config.py` - API密钥配置
- `config/exchanges.py` - 交易所配置
- `config/trading_config.py` - 交易配置

### 环境变量

所有敏感配置都通过环境变量管理：

```python
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
```

## 故障排除

### 常见问题

1. **认证失败**
   - 检查API密钥是否正确
   - 验证IP白名单设置
   - 检查API权限设置

2. **网络连接失败**
   - 检查网络连接
   - 验证防火墙设置
   - 检查代理配置

3. **限流错误**
   - 降低请求频率
   - 使用批量接口
   - 实现请求队列

### 日志调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展开发

### 添加新交易所

1. 在`ExchangeType`枚举中添加新交易所
2. 实现具体的API类（继承`BaseExchangeClient`）
3. 在`ExchangeClientFactory`中注册
4. 添加数据格式转换逻辑

### 自定义错误处理

```python
class CustomErrorHandler(ErrorHandler):
    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        # 自定义重试逻辑
        pass
```

## 版本历史

- v1.0.0 - 初始版本，支持币安、欧意交易所
- v1.1.0 - 添加错误处理和重试机制
- v1.2.0 - 完善数据格式转换和验证

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。