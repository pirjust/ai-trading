#!/usr/bin/env python3
"""
认证系统测试脚本
用于测试用户认证系统的完整功能
"""

import requests
import json
import time
from typing import Dict, Any

class AuthTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_url = f"{base_url}/api/v1/auth"
        self.session = requests.Session()
        self.access_token = None
        self.user_info = None
        
    def test_register(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """测试用户注册"""
        print(f"\n=== 测试用户注册 ===")
        
        data = {
            "username": username,
            "password": password,
            "email": email
        }
        
        try:
            response = self.session.post(f"{self.auth_url}/register", data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 注册成功: {result}")
                return result
            else:
                error = response.json()
                print(f"❌ 注册失败 ({response.status_code}): {error}")
                return error
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器，请确保后端服务已启动")
            return {"error": "Connection failed"}
    
    def test_login(self, username: str, password: str) -> Dict[str, Any]:
        """测试用户登录"""
        print(f"\n=== 测试用户登录 ===")
        
        data = {
            "username": username,
            "password": password
        }
        
        try:
            response = self.session.post(f"{self.auth_url}/login", data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                self.user_info = {
                    "user_id": result["user_id"],
                    "username": result["username"],
                    "email": result["email"],
                    "is_superuser": result["is_superuser"]
                }
                print(f"✅ 登录成功: {result['username']}")
                return result
            else:
                error = response.json()
                print(f"❌ 登录失败 ({response.status_code}): {error}")
                return error
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器，请确保后端服务已启动")
            return {"error": "Connection failed"}
    
    def test_get_current_user(self) -> Dict[str, Any]:
        """测试获取当前用户信息"""
        print(f"\n=== 测试获取当前用户信息 ===")
        
        if not self.access_token:
            print("❌ 需要先登录才能获取用户信息")
            return {"error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = self.session.get(f"{self.auth_url}/me", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 获取用户信息成功: {result}")
                return result
            else:
                error = response.json()
                print(f"❌ 获取用户信息失败 ({response.status_code}): {error}")
                return error
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            return {"error": "Connection failed"}
    
    def test_refresh_token(self) -> Dict[str, Any]:
        """测试刷新令牌"""
        print(f"\n=== 测试刷新令牌 ===")
        
        if not self.access_token:
            print("❌ 需要先登录才能刷新令牌")
            return {"error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = self.session.post(f"{self.auth_url}/refresh", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                print(f"✅ 令牌刷新成功")
                return result
            else:
                error = response.json()
                print(f"❌ 令牌刷新失败 ({response.status_code}): {error}")
                return error
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            return {"error": "Connection failed"}
    
    def test_logout(self) -> Dict[str, Any]:
        """测试用户登出"""
        print(f"\n=== 测试用户登出 ===")
        
        if not self.access_token:
            print("❌ 需要先登录才能登出")
            return {"error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = self.session.post(f"{self.auth_url}/logout", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = None
                self.user_info = None
                print(f"✅ 登出成功: {result}")
                return result
            else:
                error = response.json()
                print(f"❌ 登出失败 ({response.status_code}): {error}")
                return error
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            return {"error": "Connection failed"}
    
    def run_complete_test(self):
        """运行完整的认证测试流程"""
        print("🔧 开始认证系统完整测试流程")
        print("=" * 60)
        
        # 测试注册新用户
        test_user = {
            "username": f"test_user_{int(time.time())}",
            "password": "testpassword123",
            "email": f"test_{int(time.time())}@example.com"
        }
        
        register_result = self.test_register(**test_user)
        
        # 如果注册成功，继续测试登录
        if "user_id" in register_result:
            # 测试登录
            login_result = self.test_login(test_user["username"], test_user["password"])
            
            if "access_token" in login_result:
                # 测试获取用户信息
                self.test_get_current_user()
                
                # 测试刷新令牌
                self.test_refresh_token()
                
                # 测试登出
                self.test_logout()
                
                # 测试再次获取用户信息（应该失败）
                self.test_get_current_user()
        
        print("\n" + "=" * 60)
        print("📊 认证系统测试完成")

def main():
    """主函数"""
    print("🚀 AI量化交易系统 - 认证系统测试")
    print("=" * 60)
    
    # 创建测试器
    tester = AuthTester()
    
    # 运行完整测试
    tester.run_complete_test()
    
    # 测试演示账户
    print("\n📋 测试演示账户")
    print("-" * 40)
    
    demo_accounts = [
        {"username": "admin", "password": "admin123"},
        {"username": "demo", "password": "demo123"}
    ]
    
    for account in demo_accounts:
        print(f"\n测试账户: {account['username']}")
        login_result = tester.test_login(account["username"], account["password"])
        
        if "access_token" in login_result:
            tester.test_get_current_user()
            tester.test_logout()
        
        print("-" * 40)

if __name__ == "__main__":
    main()