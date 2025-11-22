import React, { useState } from 'react';
import { authService } from '../services/auth';

const AuthTest: React.FC = () => {
  const [testResults, setTestResults] = useState<string[]>([]);
  const [isTesting, setIsTesting] = useState(false);

  const addResult = (message: string, isSuccess: boolean) => {
    setTestResults(prev => [...prev, `${isSuccess ? '✅' : '❌'} ${message}`]);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const runAuthTest = async () => {
    setIsTesting(true);
    clearResults();
    
    try {
      // 测试1: 注册新用户
      addResult('开始测试用户注册', true);
      const testUsername = `test_${Date.now()}`;
      
      try {
        await authService.register({
          username: testUsername,
          password: 'testpassword123',
          email: `${testUsername}@example.com`
        });
        addResult('用户注册成功', true);
      } catch (error) {
        addResult(`用户注册失败: ${error.message}`, false);
      }

      // 测试2: 用户登录
      addResult('开始测试用户登录', true);
      try {
        const loginResult = await authService.login({
          username: testUsername,
          password: 'testpassword123'
        });
        addResult(`用户登录成功: ${loginResult.username}`, true);
      } catch (error) {
        addResult(`用户登录失败: ${error.message}`, false);
      }

      // 测试3: 获取当前用户信息
      addResult('开始测试获取用户信息', true);
      try {
        const userInfo = await authService.getCurrentUser();
        addResult(`获取用户信息成功: ${userInfo.username}`, true);
      } catch (error) {
        addResult(`获取用户信息失败: ${error.message}`, false);
      }

      // 测试4: 检查认证状态
      addResult('开始检查认证状态', true);
      const isAuthenticated = authService.isAuthenticated();
      addResult(`认证状态: ${isAuthenticated ? '已认证' : '未认证'}`, isAuthenticated);

      // 测试5: 刷新令牌
      addResult('开始测试令牌刷新', true);
      try {
        const refreshResult = await authService.refreshToken();
        addResult('令牌刷新成功', true);
      } catch (error) {
        addResult(`令牌刷新失败: ${error.message}`, false);
      }

      // 测试6: 用户登出
      addResult('开始测试用户登出', true);
      try {
        await authService.logout();
        addResult('用户登出成功', true);
      } catch (error) {
        addResult(`用户登出失败: ${error.message}`, false);
      }

      // 测试7: 验证登出后状态
      addResult('验证登出后状态', true);
      const afterLogout = authService.isAuthenticated();
      addResult(`登出后认证状态: ${afterLogout ? '仍认证' : '未认证'}`, !afterLogout);

    } catch (error) {
      addResult(`测试过程中发生错误: ${error.message}`, false);
    } finally {
      setIsTesting(false);
    }
  };

  const runDemoAccountTest = async () => {
    setIsTesting(true);
    clearResults();
    
    const demoAccounts = [
      { username: 'admin', password: 'admin123' },
      { username: 'demo', password: 'demo123' }
    ];

    for (const account of demoAccounts) {
      addResult(`测试演示账户: ${account.username}`, true);
      
      try {
        const loginResult = await authService.login(account);
        addResult(`登录成功: ${loginResult.username}`, true);
        
        const userInfo = await authService.getCurrentUser();
        addResult(`获取用户信息成功: ${userInfo.username}`, true);
        
        await authService.logout();
        addResult('登出成功', true);
        
      } catch (error) {
        addResult(`演示账户测试失败: ${error.message}`, false);
      }
    }
    
    setIsTesting(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          认证系统测试页面
        </h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            测试控制面板
          </h2>
          
          <div className="flex space-x-4 mb-4">
            <button
              onClick={runAuthTest}
              disabled={isTesting}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isTesting ? '测试中...' : '运行完整认证测试'}
            </button>
            
            <button
              onClick={runDemoAccountTest}
              disabled={isTesting}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isTesting ? '测试中...' : '测试演示账户'}
            </button>
            
            <button
              onClick={clearResults}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              清除结果
            </button>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            测试结果
          </h2>
          
          {testResults.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">
              点击上方按钮开始测试
            </p>
          ) : (
            <div className="space-y-2">
              {testResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-3 rounded ${
                    result.includes('✅') ? 'bg-green-50 dark:bg-green-900/20' : 
                    result.includes('❌') ? 'bg-red-50 dark:bg-red-900/20' : 
                    'bg-gray-50 dark:bg-gray-700'
                  }`}
                >
                  <code className="font-mono text-sm">{result}</code>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-200 mb-2">
            测试说明
          </h3>
          <ul className="text-yellow-700 dark:text-yellow-300 text-sm space-y-1">
            <li>• 完整认证测试：创建新用户并测试完整认证流程</li>
            <li>• 演示账户测试：测试预配置的演示账户</li>
            <li>• 确保后端服务运行在 http://localhost:8000</li>
            <li>• 测试前请确保数据库已初始化</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AuthTest;