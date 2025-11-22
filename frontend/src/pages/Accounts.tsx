import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { formatCurrency, formatPercentage } from '@/lib/utils'

interface Account {
  id: string
  name: string
  type: 'CONTRACT' | 'SPOT' | 'OPTION'
  exchange: 'BINANCE' | 'OKX' | 'HUOBI'
  balance: number
  available: number
  profitLoss: number
  profitLossPercentage: number
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED'
  lastUpdate: string
  apiConfigured: boolean
}

interface SubAccount {
  id: string
  name: string
  parentAccount: string
  strategies: number
  status: 'ACTIVE' | 'INACTIVE'
}

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([
    {
      id: '1',
      name: '主合约账户',
      type: 'CONTRACT',
      exchange: 'BINANCE',
      balance: 5000,
      available: 4200,
      profitLoss: 850.50,
      profitLossPercentage: 17.01,
      status: 'ACTIVE',
      lastUpdate: new Date().toISOString(),
      apiConfigured: true
    },
    {
      id: '2',
      name: '主现货账户',
      type: 'SPOT',
      exchange: 'OKX',
      balance: 3000,
      available: 2800,
      profitLoss: 450.25,
      profitLossPercentage: 15.01,
      status: 'ACTIVE',
      lastUpdate: new Date().toISOString(),
      apiConfigured: true
    },
    {
      id: '3',
      name: '期权交易账户',
      type: 'OPTION',
      exchange: 'BINANCE',
      balance: 2000,
      available: 1500,
      profitLoss: -150.75,
      profitLossPercentage: -7.54,
      status: 'ACTIVE',
      lastUpdate: new Date().toISOString(),
      apiConfigured: true
    }
  ])

  const [subAccounts, setSubAccounts] = useState<SubAccount[]>([
    {
      id: 's1',
      name: '高频交易子账户',
      parentAccount: '1',
      strategies: 3,
      status: 'ACTIVE'
    },
    {
      id: 's2',
      name: '套利子账户',
      parentAccount: '2',
      strategies: 2,
      status: 'ACTIVE'
    },
    {
      id: 's3',
      name: '风险对冲子账户',
      parentAccount: '3',
      strategies: 1,
      status: 'INACTIVE'
    }
  ])

  const [showApiForm, setShowApiForm] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'CONTRACT': return 'bg-blue-500'
      case 'SPOT': return 'bg-green-500'
      case 'OPTION': return 'bg-purple-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-500'
      case 'INACTIVE': return 'bg-yellow-500'
      case 'SUSPENDED': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const configureApi = (accountId: string) => {
    // 模拟API配置
    setAccounts(accounts.map(acc => 
      acc.id === accountId ? { ...acc, apiConfigured: true } : acc
    ))
    setShowApiForm(false)
    setApiKey('')
    setApiSecret('')
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">账户管理</h1>
        <Button onClick={() => setShowApiForm(!showApiForm)}>
          添加交易所账户
        </Button>
      </div>

      {/* API配置表单 */}
      {showApiForm && (
        <Card>
          <CardHeader>
            <CardTitle>配置交易所API</CardTitle>
            <CardDescription>添加新的交易所账户API密钥</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">API Key</label>
                <Input 
                  type="text" 
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="请输入API Key"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">API Secret</label>
                <Input 
                  type="password" 
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  placeholder="请输入API Secret"
                />
              </div>
              
              <div className="flex space-x-2">
                <Button onClick={() => configureApi('new')}>
                  保存配置
                </Button>
                <Button variant="outline" onClick={() => setShowApiForm(false)}>
                  取消
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 主账户列表 */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">主账户</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {accounts.map((account) => (
            <Card key={account.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{account.name}</CardTitle>
                    <CardDescription>
                      {account.exchange} • {account.type === 'CONTRACT' ? '合约' : 
                      account.type === 'SPOT' ? '现货' : '期权'}
                    </CardDescription>
                  </div>
                  <Badge className={getTypeColor(account.type)}>
                    {account.type}
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>总资金:</span>
                    <span className="font-bold">{formatCurrency(account.balance)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span>可用资金:</span>
                    <span className="font-bold">{formatCurrency(account.available)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span>盈亏:</span>
                    <span className={`font-bold ${
                      account.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(account.profitLoss)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span>收益率:</span>
                    <span className={`font-bold ${
                      account.profitLossPercentage >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercentage(account.profitLossPercentage)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span>API状态:</span>
                    <Badge className={account.apiConfigured ? 'bg-green-500' : 'bg-red-500'}>
                      {account.apiConfigured ? '已配置' : '未配置'}
                    </Badge>
                  </div>
                </div>
                
                <div className="mt-4 flex space-x-2">
                  <Button variant="outline" size="sm">
                    编辑
                  </Button>
                  {!account.apiConfigured && (
                    <Button size="sm" onClick={() => configureApi(account.id)}>
                      配置API
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 子账户管理 */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">子账户管理</h2>
        <Card>
          <CardHeader>
            <CardTitle>子账户列表</CardTitle>
            <CardDescription>管理各主账户下的子账户</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {subAccounts.map((subAccount) => (
                <div key={subAccount.id} className="flex justify-between items-center p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">{subAccount.name}</div>
                    <div className="text-sm text-muted-foreground">
                      父账户: {accounts.find(a => a.id === subAccount.parentAccount)?.name}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <div className="font-bold">{subAccount.strategies}</div>
                      <div className="text-xs text-muted-foreground">策略数</div>
                    </div>
                    
                    <Badge className={getStatusColor(subAccount.status)}>
                      {subAccount.status === 'ACTIVE' ? '活跃' : '非活跃'}
                    </Badge>
                    
                    <Button variant="outline" size="sm">管理</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 账户隔离监控 */}
      <Card>
        <CardHeader>
          <CardTitle>账户隔离监控</CardTitle>
          <CardDescription>实时监控账户资金隔离状态</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">100%</div>
              <div className="text-sm">合约账户隔离</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">100%</div>
              <div className="text-sm">现货账户隔离</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">95%</div>
              <div className="text-sm">期权账户隔离</div>
              <Badge className="bg-yellow-500 mt-2">警告</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}