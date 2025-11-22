"""
欧意(OKX) API专用实现
提供完整的欧意交易所API接口
"""

import asyncio
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Optional, Any
import aiohttp
import logging
from datetime import datetime

try:
    import websockets
except ImportError:
    websockets = None

from config.api_config import API_CONFIG
from config.exchanges import EXCHANGE_CONFIG

logger = logging.getLogger(__name__)


class OKXAPI:
    """欧意API实现类"""
    
    def __init__(self, sandbox: bool = False):
        self.config = EXCHANGE_CONFIG.get_exchange_config("okx")
        self.api_config = API_CONFIG.get_exchange_config("okx")
        
        # 设置基础URL
        if sandbox:
            self.base_url = "https://www.okx.com"  # 欧意沙盒和实盘使用相同域名
        else:
            self.base_url = self.config.base_url
        
        self.api_key = self.api_config.api_key
        self.api_secret = self.api_config.api_secret
        self.passphrase = self.api_config.passphrase
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
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
    
    def _sign_request(self, timestamp: str, method: str, 
                     request_path: str, body: str = "") -> Dict[str, str]:
        """对请求进行签名"""
        if body:
            message = timestamp + method.upper() + request_path + body
        else:
            message = timestamp + method.upper() + request_path
        
        mac = hmac.new(
            bytes(self.api_secret, encoding='utf-8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        
        signature = base64.b64encode(mac.digest()).decode()
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
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
            
            headers = {}
            body = ""
            
            if signed:
                timestamp = str(int(time.time()))
                
                if method.upper() == 'GET' and params:
                    # GET请求将参数放在URL中
                    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                    request_path = f"{endpoint}?{query_string}"
                else:
                    request_path = endpoint
                    
                if method.upper() in ['POST', 'PUT'] and params:
                    body = json.dumps(params)
                
                headers = self._sign_request(timestamp, method, request_path, body)
            
            if method.upper() == 'GET':
                async with self.session.get(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                async with self.session.post(url, json=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, params=params, headers=headers) as response:
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
            
            # 检查欧意API错误码
            if data.get('code') != '0':
                error_msg = data.get('msg', 'Unknown error')
                raise Exception(f"欧意API错误: {error_msg} (代码: {data['code']})")
            
            return data
        else:
            error_text = await response.text()
            raise Exception(f"HTTP错误: {response.status} - {error_text}")
    
    # 市场数据接口
    async def get_ticker(self, inst_id: str) -> Dict[str, Any]:
        """获取单个交易对行情"""
        endpoint = "/api/v5/market/ticker"
        params = {'instId': inst_id}
        return await self._make_request('GET', endpoint, params)
    
    async def get_tickers(self, inst_type: str = 'SPOT') -> List[Dict[str, Any]]:
        """获取所有交易对行情"""
        endpoint = "/api/v5/market/tickers"
        params = {'instType': inst_type}
        response = await self._make_request('GET', endpoint, params)
        return response.get('data', [])
    
    async def get_depth(self, inst_id: str, sz: int = 400) -> Dict[str, Any]:
        """获取深度数据"""
        endpoint = "/api/v5/market/books"
        params = {
            'instId': inst_id,
            'sz': sz
        }
        return await self._make_request('GET', endpoint, params)
    
    async def get_klines(self, inst_id: str, bar: str = '1m',
                        after: int = None, before: int = None,
                        limit: int = 100) -> List[List[Any]]:
        """获取K线数据"""
        endpoint = "/api/v5/market/candles"
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': limit
        }
        
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        
        response = await self._make_request('GET', endpoint, params)
        return response.get('data', [])
    
    # 账户接口
    async def get_account_balance(self, ccy: str = None) -> Dict[str, Any]:
        """获取账户余额"""
        endpoint = "/api/v5/account/balance"
        params = {}
        if ccy:
            params['ccy'] = ccy
        
        return await self._make_request('GET', endpoint, params, signed=True)
    
    async def get_account_config(self) -> Dict[str, Any]:
        """获取账户配置"""
        endpoint = "/api/v5/account/config"
        return await self._make_request('GET', endpoint, signed=True)
    
    # 交易接口
    async def place_order(self, inst_id: str, td_mode: str, side: str, 
                         ord_type: str, sz: str, px: str = None,
                         cl_ord_id: str = None) -> Dict[str, Any]:
        """下单"""
        endpoint = "/api/v5/trade/order"
        params = {
            'instId': inst_id,
            'tdMode': td_mode,
            'side': side,
            'ordType': ord_type,
            'sz': sz
        }
        
        if px:
            params['px'] = px
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id
        
        return await self._make_request('POST', endpoint, params, signed=True)
    
    async def cancel_order(self, inst_id: str, ord_id: str = None, 
                          cl_ord_id: str = None) -> Dict[str, Any]:
        """撤单"""
        endpoint = "/api/v5/trade/cancel-order"
        params = {'instId': inst_id}
        
        if ord_id:
            params['ordId'] = ord_id
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id
        
        return await self._make_request('POST', endpoint, params, signed=True)
    
    async def get_order_info(self, inst_id: str, ord_id: str = None,
                            cl_ord_id: str = None) -> Dict[str, Any]:
        """获取订单信息"""
        endpoint = "/api/v5/trade/order"
        params = {'instId': inst_id}
        
        if ord_id:
            params['ordId'] = ord_id
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id
        
        return await self._make_request('GET', endpoint, params, signed=True)
    
    async def get_order_history(self, inst_type: str = 'SPOT', 
                               after: str = None, before: str = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """获取订单历史"""
        endpoint = "/api/v5/trade/orders-history"
        params = {
            'instType': inst_type,
            'limit': limit
        }
        
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        
        response = await self._make_request('GET', endpoint, params, signed=True)
        return response.get('data', [])
    
    # 持仓接口
    async def get_positions(self, inst_type: str = 'SPOT',
                           inst_id: str = None) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        endpoint = "/api/v5/account/positions"
        params = {'instType': inst_type}
        
        if inst_id:
            params['instId'] = inst_id
        
        response = await self._make_request('GET', endpoint, params, signed=True)
        return response.get('data', [])
    
    # 公共接口
    async def get_instruments(self, inst_type: str = 'SPOT') -> List[Dict[str, Any]]:
        """获取交易产品信息"""
        endpoint = "/api/v5/public/instruments"
        params = {'instType': inst_type}
        
        response = await self._make_request('GET', endpoint, params)
        return response.get('data', [])
    
    async def get_system_time(self) -> int:
        """获取系统时间"""
        endpoint = "/api/v5/public/time"
        response = await self._make_request('GET', endpoint)
        return int(response['data'][0]['ts'])
    
    # 工具方法
    async def test_connectivity(self) -> bool:
        """测试连接性"""
        try:
            await self.get_system_time()
            return True
        except Exception:
            return False


# 欧意WebSocket实现
class OKXWebSocket:
    """欧意WebSocket客户端"""
    
    def __init__(self, sandbox: bool = False):
        if sandbox:
            self.ws_url = "wss://wspap.okx.com:8443/ws/v5/public"
        else:
            self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
        
        self.private_ws_url = self.ws_url.replace('/public', '/private')
        self.websocket = None
        self.is_connected = False
    
    async def connect_public(self, args: List[Dict[str, str]]):
        """连接公共WebSocket"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            
            # 订阅频道
            subscribe_msg = {
                'op': 'subscribe',
                'args': args
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info("欧意公共WebSocket连接成功")
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            raise
    
    async def connect_private(self, api_key: str, passphrase: str, secret_key: str):
        """连接私有WebSocket"""
        try:
            self.websocket = await websockets.connect(self.private_ws_url)
            self.is_connected = True
            
            # 登录
            timestamp = str(int(time.time()))
            message = timestamp + 'GET' + '/users/self/verify'
            signature = base64.b64encode(
                hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
            ).decode()
            
            login_msg = {
                'op': 'login',
                'args': [{
                    'apiKey': api_key,
                    'passphrase': passphrase,
                    'timestamp': timestamp,
                    'sign': signature
                }]
            }
            
            await self.websocket.send(json.dumps(login_msg))
            logger.info("欧意私有WebSocket连接成功")
            
        except Exception as e:
            logger.error(f"私有WebSocket连接失败: {e}")
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
            logger.info("欧意WebSocket连接已关闭")


# 使用示例
async def example_usage():
    """使用示例"""
    try:
        async with OKXAPI(sandbox=True) as api:
            # 测试连接
            if await api.test_connectivity():
                print("✓ 欧意API连接正常")
            
            # 获取行情
            ticker = await api.get_ticker("BTC-USDT")
            print(f"BTC-USDT价格: {ticker['data'][0]['last']}")
            
            # 获取交易产品信息
            instruments = await api.get_instruments('SPOT')
            print(f"现货交易对数量: {len(instruments)}")
            
            # 获取账户余额（需要有效API密钥）
            # balance = await api.get_account_balance()
            # print(f"账户余额: {balance}")
            
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())