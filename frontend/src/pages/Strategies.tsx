import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import StrategyConfigPanel from '@/components/StrategyConfigPanel'
import ProfitChart from '@/components/Charts/ProfitChart'

interface Strategy {
  id: string
  name: string
  type: 'CONTRACT' | 'SPOT' | 'OPTION'
  status: 'RUNNING' | 'PAUSED' | 'STOPPED'
  symbol: string
  profit: number
  profitPercentage: number
  trades: number
  winRate: number
  lastUpdate: string
  parameters: Record<string, any>
  aiEnabled: boolean
  leverage: number
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
}

export default function Strategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([
    {
      id: '1',
      name: '移动平均交叉策略',
      type: 'CONTRACT',
      status: 'RUNNING',
      symbol: 'BTCUSDT',
      profit: 1250.50,
      profitPercentage: 12.5,
      trades: 45,
      winRate: 68.9,
      lastUpdate: new Date().toISOString(),
      parameters: { fastPeriod: 10, slowPeriod: 30, leverage: 3 },
      aiEnabled: true,
      leverage: 3,
      riskLevel: 'MEDIUM'
    },
    {
      id: '2',
      name: 'RSI超买超卖策略',
      type: 'SPOT',
      status: 'RUNNING',
      symbol: 'ETHUSDT',
      profit: 850.25,
      profitPercentage: 8.5,
      trades: 32,
      winRate: 72.3,
      lastUpdate: new Date().toISOString(),
      parameters: { rsiPeriod: 14, overbought: 70, oversold: 30 },
      aiEnabled: true,
      leverage: 1,
      riskLevel: 'LOW'
    },
    {
      id: '3',
      name: '期权波动率策略',
      type: 'OPTION',
      status: 'PAUSED',
      symbol: 'BTC-OPTION',
      profit: -150.75,
      profitPercentage: -1.5,
      trades: 8,
      winRate: 37.5,
      lastUpdate: new Date().toISOString(),
      parameters: { volatilityThreshold: 0.3, expiry: '7d' },
      aiEnabled: false,
      leverage: 1,
      riskLevel: 'HIGH'
    }
  ])

  const [profitData] = useState([
    { date: '2025-01-01', profit: 0, cumulative: 0 },
    { date: '2025-01-02', profit: 150, cumulative: 150 },
    { date: '2025-01-03', profit: -50, cumulative: 100 },
    { date: '2025-01-04', profit: 200, cumulative: 300 },
    { date: '2025-01-05', profit: 100, cumulative: 400 },
    { date: '2025-01-06', profit: 250, cumulative: 650 },
    { date: '2025-01-07', profit: 150, cumulative: 800 }
  ])

  const { toast } = useToast()

  const toggleStrategy = (id: string, newStatus: 'RUNNING' | 'PAUSED' | 'STOPPED') => {
    setStrategies(strategies.map(s => 
      s.id === id ? { ...s, status: newStatus } : s
    ))
    
    toast({
      title: `策略${newStatus === 'RUNNING' ? '启动' : '暂停'}成功`,
      description: `策略状态已更新`
    })
  }

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
      case 'RUNNING': return 'bg-green-500'
      case 'PAUSED': return 'bg-yellow-500'
      case 'STOPPED': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">策略管理</h1>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">策略概览</TabsTrigger>
          <TabsTrigger value="config">策略配置</TabsTrigger>
          <TabsTrigger value="backtest">策略回测</TabsTrigger>
          <TabsTrigger value="performance">性能分析</TabsTrigger>
        </TabsList>

        {/* 策略概览页 */}
        <TabsContent value="overview" className="space-y-6">
          {/* 策略列表 */}
          <div className="grid grid-cols-1 gap-6">
            {strategies.map((strategy) => (
              <Card key={strategy.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center space-x-2">
                        <span>{strategy.name}</span>
                        <Badge className={getTypeColor(strategy.type)}>
                          {strategy.type === 'CONTRACT' ? '合约' : 
                           strategy.type === 'SPOT' ? '现货' : '期权'}
                        </Badge>
                        <Badge className={getStatusColor(strategy.status)}>
                          {strategy.status === 'RUNNING' ? '运行中' : 
                           strategy.status === 'PAUSED' ? '已暂停' : '已停止'}
                        </Badge>
                      </CardTitle>
                      <CardDescription>
                        {strategy.symbol} • 最后更新: {new Date(strategy.lastUpdate).toLocaleString('zh-CN')}
                      </CardDescription>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={strategy.status === 'RUNNING'}
                        onCheckedChange={(checked) => 
                          toggleStrategy(strategy.id, checked ? 'RUNNING' : 'PAUSED')
                        }
                      />
                      <Button variant="outline" size="sm">编辑</Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">盈亏</div>
                      <div className={`text-lg font-bold ${strategy.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${strategy.profit.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {strategy.profitPercentage > 0 ? '+' : ''}{strategy.profitPercentage}%
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">交易数</div>
                      <div className="text-lg font-bold">{strategy.trades}</div>
                      <div className="text-xs text-muted-foreground">总交易</div>
                    </div>
                    
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">胜率</div>
                      <div className="text-lg font-bold">{strategy.winRate}%</div>
                      <div className="text-xs text-muted-foreground">盈利占比</div>
                    </div>
                    
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">风险等级</div>
                      <div className="text-lg font-bold">{strategy.riskLevel}</div>
                      <div className="text-xs text-muted-foreground">AI优化: {strategy.aiEnabled ? '启用' : '禁用'}</div>
                    </div>
                  </div>
                  
                  {/* 策略参数 */}
                  <div>
                    <h4 className="font-semibold mb-2">策略参数</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      {Object.entries(strategy.parameters).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-muted-foreground">{key}:</span>
                          <span>{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 策略生成器 */}
          <Card>
            <CardHeader>
              <CardTitle>AI策略生成器</CardTitle>
              <CardDescription>基于AI模型的自动化策略生成</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">策略类型</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="选择策略类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="technical">技术指标策略</SelectItem>
                      <SelectItem value="ml">机器学习策略</SelectItem>
                      <SelectItem value="rl">强化学习策略</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium">交易品种</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="选择交易品种" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                      <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                      <SelectItem value="ADAUSDT">ADA/USDT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium">账户类型</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="选择账户类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="contract">合约账户</SelectItem>
                      <SelectItem value="spot">现货账户</SelectItem>
                      <SelectItem value="option">期权账户</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="mt-4">
                <Button className="w-full">生成策略</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 策略配置页 */}
        <TabsContent value="config">
          <StrategyConfigPanel />
        </TabsContent>

        {/* 性能分析页 */}
        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>策略收益走势</CardTitle>
              <CardDescription>各策略累计收益对比分析</CardDescription>
            </CardHeader>
            <CardContent>
              <ProfitChart data={profitData} height={400} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>风险指标对比</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {strategies.map((strategy) => (
                    <div key={strategy.id} className="flex justify-between items-center">
                      <span className="text-sm">{strategy.name}</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm text-muted-foreground">杠杆: {strategy.leverage}x</span>
                        <Badge className={getStatusColor(strategy.status)}>
                          {strategy.status === 'RUNNING' ? '运行' : '暂停'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI优化状态</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {strategies.map((strategy) => (
                    <div key={strategy.id} className="flex justify-between items-center">
                      <span className="text-sm">{strategy.name}</span>
                      <div className="flex items-center space-x-2">
                        <Switch checked={strategy.aiEnabled} />
                        <span className="text-sm text-muted-foreground">
                          {strategy.aiEnabled ? 'AI优化中' : '手动模式'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 策略回测页 */}
        <TabsContent value="backtest">
          <Card>
            <CardHeader>
              <CardTitle>策略回测分析</CardTitle>
              <CardDescription>历史数据回测和性能评估</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="text-sm font-medium">回测周期</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="选择回测周期" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7d">7天</SelectItem>
                      <SelectItem value="30d">30天</SelectItem>
                      <SelectItem value="90d">90天</SelectItem>
                      <SelectItem value="1y">1年</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium">初始资金</label>
                  <Input placeholder="10000" />
                </div>
                
                <div>
                  <label className="text-sm font-medium">手续费率</label>
                  <Input placeholder="0.1%" />
                </div>
              </div>
              
              <Button className="w-full">开始回测</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}