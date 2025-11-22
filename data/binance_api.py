"""
币安API专用实现
提供完整的币安交易所API接口
"""

import asyncio
import time
import hmac
import hashlib
import urllib.parse
from typing import Dict, List, Optional, Any
import aiohttp
import logging
from datetime import datetime
import json

from config.api_config import API_CONFIG
from config.exchanges import EXCHANGE_CONFIG

logger = logging.getLogger(__name__)


class BinanceAPI:
    """币安API实现类"""
    
    def __init__(self, sandbox: bool = False, testnet: bool = False):
        self.config = EXCHANGE_CONFIG.get_exchange_config("binance")
        self.api_config = API_CONFIG.get_exchange_config("binance")
        
        # 设置基础URL
        if sandbox or testnet:
            self.base_url = self.config.sandbox_url
        else:
            self.base_url = self.config.base_url
        
        self.api_key = self.api_config.api_key
        self.api_secret = self.api_config.api_secret
        self.session = None
        self.rate_limit = self.config.rate_limit
        self.last_request_time = 0
        
    async def __aenter__(self):
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
    
    async def _initialize_session(self):
        """初始化HTTP会话"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'X-MBX-APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
        )
    
    async def _close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """对请求进行签名"""
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _rate_limit_wait(self):
        """请求频率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # 计算最小请求间隔
        min_interval = 60.0 / self.rate_limit
        
        if time_since_last_request < min_interval:
            await asyncio.sleep(min_interval - time_since_last_request)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, method: str, endpoint: str, 
                           params: Dict[str, Any] = None, 
                           signed: bool = False) -> Dict[str, Any]:
        """发送HTTP请求"""
        try:
            await self._rate_limit_wait()
            
            url = f"{self.base_url}{endpoint}"
            
            if params is None:
                params = {}
            
            # 添加时间戳（需要签名的请求）
            if signed:
                params['timestamp'] = int(time.time() * 1000)
                params['signature'] = self._sign_request(params)
            
            if method.upper() == 'GET':
                async with self.session.get(url, params=params) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                async with self.session.post(url, data=params) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, params=params) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
                
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise
    
    async def _handle_response(self, response) -> Dict[str, Any]:
        """处理HTTP响应"""
        if response.status == 200:
            data = await response.json()
            
            # 检查币安API错误码
            if 'code' in data and data['code'] != 0:
                error_msg = data.get('msg', 'Unknown error')
                raise Exception(f"币安API错误: {error_msg} (代码: {data['code']})")
            
            return data
        else:
            error_text = await response.text()
            raise Exception(f"HTTP错误: {response.status} - {error_text}")
    
    # 市场数据接口
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取单个交易对行情"""
        endpoint = "/api/v3/ticker/24hr"
        params = {'symbol': symbol}
        return await self._make_request('GET', endpoint, params)
    
    async def get_tickers(self) -> List[Dict[str, Any]]:
        """获取所有交易对行情"""
        endpoint = "/api/v3/ticker/24hr"
        return await self._make_request('GET', endpoint)
    
    async def get_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取深度数据"""
        endpoint = "/api/v3/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return await self._make_request('GET', endpoint, params)
    
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: int = None, end_time: int = None, 
                        limit: int = 1000) -> List[List[Any]]:
        """获取K线数据"""
        endpoint = "/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return await self._make_request('GET', endpoint, params)
    
    # 账户接口
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        endpoint = "/api/v3/account"
        return await self._make_request('GET', endpoint, signed=True)
    
    async def get_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        account_info = await self.get_account_info()
        balances = {}
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            balances[asset] = {
                'free': free,
                'locked': locked,
                'total': free + locked
            }
        
        return balances
    
    # 交易接口
    async def create_order(self, symbol: str, side: str, order_type: str,
                          quantity: float, price: float = None,
                          time_in_force: str = 'GTC') -> Dict[str, Any]:
        """创建订单"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity
        }
        
        if order_type.upper() == 'LIMIT':
            if price is None:
                raise ValueError("限价单需要指定价格")
            params['price'] = price
            params['timeInForce'] = time_in_force
        
        return await self._make_request('POST', endpoint, params, signed=True)
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """取消订单"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return await self._make_request('DELETE', endpoint, params, signed=True)
    
    async def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """查询订单"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return await self._make_request('GET', endpoint, params, signed=True)
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """获取当前挂单"""
        endpoint = "/api/v3/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request('GET', endpoint, params, signed=True)
    
    # 现货交易接口
    async def get_my_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """获取账户成交历史"""
        endpoint = "/api/v3/myTrades"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return await self._make_request('GET', endpoint, params, signed=True)
    
    # 工具方法
    async def test_connectivity(self) -> bool:
        """测试连接性"""
        try:
            endpoint = "/api/v3/ping"
            await self._make_request('GET', endpoint)
            return True
        except Exception:
            return False
    
    async def get_server_time(self) -> int:
        """获取服务器时间"""
        endpoint = "/api/v3/time"
        response = await self._make_request('GET', endpoint)
        return response['serverTime']
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        endpoint = "/api/v3/exchangeInfo"
        return await self._make_request('GET', endpoint)


# 币安WebSocket实现
class BinanceWebSocket:
    """币安WebSocket客户端"""
    
    def __init__(self):
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.testnet_url = "wss://testnet.binance.vision/ws"
        self.websocket = None
        self.is_connected = False
    
    async def connect(self, streams: List[str]):
        """连接WebSocket"""
        try:
            combined_stream = '/'.join(streams)
            url = f"{self.ws_url}/{combined_stream}"
            
            self.websocket = await websockets.connect(url)
            self.is_connected = True
            logger.info("币安WebSocket连接成功")
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            raise
    
    async def receive_messages(self, callback):
        """接收消息并回调"""
        while self.is_connected:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                callback(data)
                
            except websockets.exceptions.ConnectionClosed:
                logger.error("WebSocket连接已关闭")
                self.is_connected = False
                break
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("币安WebSocket连接已关闭")


# 使用示例
async def example_usage():
    """使用示例"""
    try:
        async with BinanceAPI(sandbox=True) as api:
            # 测试连接
            if await api.test_connectivity():
                print("✓ 币安API连接正常")
            
            # 获取行情
            ticker = await api.get_ticker("BTCUSDT")
            print(f"BTCUSDT价格: {ticker['lastPrice']}")
            
            # 获取账户余额
            balances = await api.get_balance()
            print(f"账户余额: {balances}")
            
            # 创建测试订单（仅在沙盒环境）
            # order = await api.create_order(
            #     symbol="BTCUSDT",
            #     side="BUY",
            #     order_type="MARKET",
            #     quantity=0.001
            # )
            # print(f"订单创建成功: {order['orderId']}")
            
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())