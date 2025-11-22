"""
账户管理器 - 实现严格的账户隔离机制
"""
import asyncio
from typing import Dict, List, Optional
from enum import Enum

class AccountType(Enum):
    """账户类型枚举"""
    SPOT = "spot"
    FUTURES = "futures"
    OPTIONS = "options"

class AccountManager:
    """账户管理器"""
    
    def __init__(self):
        self.accounts: Dict[str, Dict] = {}
        self.account_balances: Dict[str, Dict] = {}
        self.position_limits: Dict[str, float] = {}
        self.risk_limits: Dict[str, Dict] = {}
        
    async def initialize(self):
        """初始化账户管理器"""
        print("账户管理器初始化...")
        # 加载账户配置
        await self._load_account_config()
        
    async def create_account(self, account_id: str, account_type: AccountType, 
                           exchange: str, api_key: str, api_secret: str) -> bool:
        """创建交易账户"""
        try:
            # 验证账户类型
            if not self._validate_account_type(account_type):
                raise ValueError(f"无效的账户类型: {account_type}")
            
            # 创建账户记录
            self.accounts[account_id] = {
                'account_id': account_id,
                'account_type': account_type.value,
                'exchange': exchange,
                'api_key': api_key,
                'api_secret': api_secret,
                'status': 'active',
                'created_at': asyncio.get_event_loop().time()
            }
            
            # 初始化账户余额
            self.account_balances[account_id] = {
                'total_balance': 0.0,
                'available_balance': 0.0,
                'frozen_balance': 0.0,
                'leverage': 1.0 if account_type == AccountType.SPOT else 10.0,
                'margin_ratio': 0.0
            }
            
            # 设置风险限制
            self._set_default_risk_limits(account_id, account_type)
            
            print(f"账户创建成功: {account_id} ({account_type.value})")
            return True
            
        except Exception as e:
            print(f"账户创建失败: {str(e)}")
            return False
    
    async def validate_trade(self, account_id: str, symbol: str, side: str, 
                           quantity: float, order_type: str) -> Dict:
        """验证交易请求"""
        try:
            # 检查账户存在性
            if account_id not in self.accounts:
                return {
                    "allowed": False,
                    "reason": "账户不存在",
                    "error_code": "ACCOUNT_NOT_FOUND"
                }
            
            account = self.accounts[account_id]
            balance = self.account_balances[account_id]
            
            # 账户类型验证
            if not self._validate_account_operation(account['account_type'], order_type):
                return {
                    "allowed": False,
                    "reason": f"账户类型 {account['account_type']} 不支持 {order_type} 订单",
                    "error_code": "INVALID_ORDER_TYPE"
                }
            
            # 资金验证
            if not await self._validate_funds(account_id, quantity, side):
                return {
                    "allowed": False,
                    "reason": "资金不足",
                    "error_code": "INSUFFICIENT_FUNDS"
                }
            
            # 风险验证
            risk_check = await self._check_risk_limits(account_id, symbol, quantity, side)
            if not risk_check["allowed"]:
                return risk_check
            
            # 仓位限制验证
            position_check = await self._check_position_limits(account_id, symbol, quantity, side)
            if not position_check["allowed"]:
                return position_check
            
            return {
                "allowed": True,
                "risk_level": "low",
                "available_funds": balance['available_balance']
            }
            
        except Exception as e:
            return {
                "allowed": False,
                "reason": f"验证失败: {str(e)}",
                "error_code": "VALIDATION_ERROR"
            }
    
    async def update_balance(self, account_id: str, amount: float, 
                           operation: str, symbol: str = None) -> bool:
        """更新账户余额"""
        try:
            if account_id not in self.account_balances:
                return False
            
            balance = self.account_balances[account_id]
            
            if operation == "deposit":
                balance['total_balance'] += amount
                balance['available_balance'] += amount
            elif operation == "withdraw":
                if balance['available_balance'] >= amount:
                    balance['total_balance'] -= amount
                    balance['available_balance'] -= amount
                else:
                    return False
            elif operation == "freeze":
                if balance['available_balance'] >= amount:
                    balance['available_balance'] -= amount
                    balance['frozen_balance'] += amount
                else:
                    return False
            elif operation == "unfreeze":
                if balance['frozen_balance'] >= amount:
                    balance['available_balance'] += amount
                    balance['frozen_balance'] -= amount
                else:
                    return False
            
            # 记录余额变动
            await self._record_balance_change(account_id, amount, operation, symbol)
            
            return True
            
        except Exception as e:
            print(f"余额更新失败: {str(e)}")
            return False
    
    def get_account_info(self, account_id: str) -> Optional[Dict]:
        """获取账户信息"""
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id].copy()
        balance = self.account_balances.get(account_id, {})
        
        account.update({
            'total_balance': balance.get('total_balance', 0.0),
            'available_balance': balance.get('available_balance', 0.0),
            'frozen_balance': balance.get('frozen_balance', 0.0),
            'leverage': balance.get('leverage', 1.0)
        })
        
        return account
    
    def get_all_accounts(self) -> List[Dict]:
        """获取所有账户信息"""
        accounts_info = []
        for account_id in self.accounts:
            account_info = self.get_account_info(account_id)
            if account_info:
                accounts_info.append(account_info)
        
        return accounts_info
    
    def _validate_account_type(self, account_type: AccountType) -> bool:
        """验证账户类型"""
        return account_type in [AccountType.SPOT, AccountType.FUTURES, AccountType.OPTIONS]
    
    def _validate_account_operation(self, account_type: str, order_type: str) -> bool:
        """验证账户操作"""
        # 现货账户只支持现货交易
        if account_type == "spot" and order_type not in ["market", "limit"]:
            return False
        
        # 合约账户支持更多订单类型
        if account_type == "futures" and order_type not in ["market", "limit", "stop"]:
            return False
        
        return True
    
    async def _validate_funds(self, account_id: str, quantity: float, side: str) -> bool:
        """验证资金"""
        if account_id not in self.account_balances:
            return False
        
        balance = self.account_balances[account_id]
        
        # 简化验证：检查可用余额是否足够
        # 实际应该考虑交易对、价格等因素
        required_amount = quantity * 0.1  # 简化处理
        
        return balance['available_balance'] >= required_amount
    
    async def _check_risk_limits(self, account_id: str, symbol: str, 
                               quantity: float, side: str) -> Dict:
        """检查风险限制"""
        # 获取账户风险配置
        risk_config = self.risk_limits.get(account_id, {})
        
        # 检查最大仓位限制
        max_position = risk_config.get('max_position_per_trade', 1000)
        if quantity > max_position:
            return {
                "allowed": False,
                "reason": f"单笔交易超过最大限制: {quantity} > {max_position}",
                "error_code": "EXCEED_POSITION_LIMIT"
            }
        
        # 检查杠杆限制（合约账户）
        account_type = self.accounts[account_id]['account_type']
        if account_type == "futures":
            max_leverage = risk_config.get('max_leverage', 20)
            current_leverage = self.account_balances[account_id].get('leverage', 1)
            
            if current_leverage > max_leverage:
                return {
                    "allowed": False,
                    "reason": f"杠杆超过限制: {current_leverage} > {max_leverage}",
                    "error_code": "EXCEED_LEVERAGE_LIMIT"
                }
        
        return {"allowed": True}
    
    async def _check_position_limits(self, account_id: str, symbol: str, 
                                    quantity: float, side: str) -> Dict:
        """检查仓位限制"""
        # 这里应该实现具体的仓位限制检查
        # 包括单品种持仓限制、总持仓限制等
        
        # 简化实现
        max_symbol_position = self.position_limits.get(symbol, 5000)
        
        # 获取当前仓位（简化处理）
        current_position = await self._get_current_position(account_id, symbol)
        
        new_position = current_position + (quantity if side == "buy" else -quantity)
        
        if abs(new_position) > max_symbol_position:
            return {
                "allowed": False,
                "reason": f"仓位超过限制: {new_position} > {max_symbol_position}",
                "error_code": "EXCEED_POSITION_LIMIT"
            }
        
        return {"allowed": True}
    
    def _set_default_risk_limits(self, account_id: str, account_type: AccountType):
        """设置默认风险限制"""
        if account_type == AccountType.SPOT:
            self.risk_limits[account_id] = {
                'max_position_per_trade': 1000,
                'max_daily_loss': 0.1,  # 10%
                'stop_loss_ratio': 0.05  # 5%
            }
        elif account_type == AccountType.FUTURES:
            self.risk_limits[account_id] = {
                'max_position_per_trade': 500,
                'max_leverage': 20,
                'max_daily_loss': 0.2,  # 20%
                'stop_loss_ratio': 0.03  # 3%
            }
        elif account_type == AccountType.OPTIONS:
            self.risk_limits[account_id] = {
                'max_position_per_trade': 100,
                'max_premium_ratio': 0.1,  # 权利金不超过账户10%
                'max_daily_loss': 0.15  # 15%
            }
    
    async def _load_account_config(self):
        """加载账户配置"""
        # 这里应该从数据库或配置文件加载账户配置
        pass
    
    async def _get_current_position(self, account_id: str, symbol: str) -> float:
        """获取当前仓位"""
        # 这里应该从数据库获取当前仓位
        return 0.0
    
    async def _record_balance_change(self, account_id: str, amount: float, 
                                   operation: str, symbol: str = None):
        """记录余额变动"""
        # 这里应该记录余额变动到数据库
        pass