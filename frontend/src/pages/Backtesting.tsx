import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'

interface Strategy {
  id: string
  name: string
  description: string
  type: 'TREND_FOLLOWING' | 'MEAN_REVERSION' | 'ARBITRAGE' | 'AI'
  status: 'ACTIVE' | 'PAUSED' | 'STOPPED'
}

interface BacktestResult {
  id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  status: 'RUNNING' | 'COMPLETED' | 'FAILED'
  created_at: string
}

interface BacktestRequest {
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  symbols: string[]
  timeframe: string
}

export default function Backtesting() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<string>('')
  const [backtestRequest, setBacktestRequest] = useState<BacktestRequest>({
    strategy_id: '',
    start_date: '',
    end_date: '',
    initial_capital: 10000,
    symbols: ['BTCUSDT', 'ETHUSDT'],
    timeframe: '1h'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [activeBacktest, setActiveBacktest] = useState<string | null>(null)

  const { toast } = useToast()

  useEffect(() => {
    loadStrategies()
    loadBacktestResults()
  }, [])

  const loadStrategies = async () => {
    try {
      const response = await apiClient.get('/strategies')
      setStrategies(response.data)
    } catch (error) {
      console.error('加载策略失败:', error)
      toast({
        title: '加载失败',
        description: '无法获取策略列表',
        variant: 'destructive'
      })
    }
  }

  const loadBacktestResults = async () => {
    try {
      const response = await apiClient.get('/backtesting/results')
      setBacktestResults(response.data)
      
      // 检查是否有运行中的回测
      const runningBacktest = response.data.find((result: BacktestResult) => 
        result.status === 'RUNNING'
      )
      if (runningBacktest) {
        setActiveBacktest(runningBacktest.id)
        startBacktestProgressPolling(runningBacktest.id)
      }
    } catch (error) {
      console.error('加载回测结果失败:', error)
    }
  }

  const startBacktestProgressPolling = (backtestId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await apiClient.get(`/backtesting/results/${backtestId}`)
        const backtest = response.data
        
        if (backtest.status === 'COMPLETED' || backtest.status === 'FAILED') {
          clearInterval(interval)
          setActiveBacktest(null)
          await loadBacktestResults()
        }
      } catch (error) {
        console.error('获取回测进度失败:', error)
        clearInterval(interval)
        setActiveBacktest(null)
      }
    }, 2000)
  }

  const runBacktest = async () => {
    if (!backtestRequest.strategy_id) {
      toast({
        title: '参数错误',
        description: '请选择策略',
        variant: 'destructive'
      })
      return
    }

    try {
      setIsLoading(true)
      const response = await apiClient.post('/backtesting/run', backtestRequest)
      
      toast({
        title: '回测已启动',
        description: '回测任务正在执行中'
      })
      
      setActiveBacktest(response.data.id)
      startBacktestProgressPolling(response.data.id)
      await loadBacktestResults()
      
    } catch (error) {
      console.error('启动回测失败:', error)
      toast({
        title: '启动失败',
        description: '无法启动回测任务',
        variant: 'destructive'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getStrategyTypeColor = (type: string) => {
    switch (type) {
      case 'TREND_FOLLOWING': return 'bg-blue-500'
      case 'MEAN_REVERSION': return 'bg-green-500'
      case 'ARBITRAGE': return 'bg-purple-500'
      case 'AI': return 'bg-orange-500'
      default: return 'bg-gray-500'
    }
  }

  const getStrategyTypeText = (type: string) => {
    switch (type) {
      case 'TREND_FOLLOWING': return '趋势跟踪'
      case 'MEAN_REVERSION': return '均值回归'
      case 'ARBITRAGE': return '套利'
      case 'AI': return '人工智能'
      default: return '未知'
    }
  }

  const getReturnColor = (returnValue: number) => {
    if (returnValue > 0) return 'text-green-600'
    if (returnValue < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">策略回测系统</h1>

      {/* 回测配置 */}
      <Card>
        <CardHeader>
          <CardTitle>回测配置</CardTitle>
          <CardDescription>设置回测参数并执行回测</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="strategy">选择策略</Label>
              <Select 
                value={backtestRequest.strategy_id} 
                onValueChange={(value) => setBacktestRequest({...backtestRequest, strategy_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择策略" />
                </SelectTrigger>
                <SelectContent>
                  {strategies.map((strategy) => (
                    <SelectItem key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="capital">初始资金 (USD)</Label>
              <Input
                type="number"
                value={backtestRequest.initial_capital}
                onChange={(e) => setBacktestRequest({
                  ...backtestRequest, 
                  initial_capital: Number(e.target.value)
                })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="start_date">开始日期</Label>
              <Input
                type="date"
                value={backtestRequest.start_date}
                onChange={(e) => setBacktestRequest({
                  ...backtestRequest, 
                  start_date: e.target.value
                })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end_date">结束日期</Label>
              <Input
                type="date"
                value={backtestRequest.end_date}
                onChange={(e) => setBacktestRequest({
                  ...backtestRequest, 
                  end_date: e.target.value
                })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeframe">时间周期</Label>
              <Select 
                value={backtestRequest.timeframe} 
                onValueChange={(value) => setBacktestRequest({...backtestRequest, timeframe: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择时间周期" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1m">1分钟</SelectItem>
                  <SelectItem value="5m">5分钟</SelectItem>
                  <SelectItem value="15m">15分钟</SelectItem>
                  <SelectItem value="1h">1小时</SelectItem>
                  <SelectItem value="4h">4小时</SelectItem>
                  <SelectItem value="1d">1天</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button 
            onClick={runBacktest} 
            disabled={isLoading || !backtestRequest.strategy_id}
            className="w-full"
          >
            {isLoading ? '执行中...' : '执行回测'}
          </Button>
        </CardContent>
      </Card>

      {/* 策略列表 */}
      <Card>
        <CardHeader>
          <CardTitle>可用策略</CardTitle>
          <CardDescription>系统支持的交易策略</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((strategy) => (
              <Card key={strategy.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">{strategy.name}</h3>
                    <p className="text-sm text-muted-foreground">{strategy.description}</p>
                  </div>
                  <Badge className={getStrategyTypeColor(strategy.type)}>
                    {getStrategyTypeText(strategy.type)}
                  </Badge>
                </div>
                <div className="mt-2">
                  <Badge variant={strategy.status === 'ACTIVE' ? 'default' : 'secondary'}>
                    {strategy.status === 'ACTIVE' ? '活跃' : 
                     strategy.status === 'PAUSED' ? '暂停' : '停止'}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 回测结果 */}
      <Card>
        <CardHeader>
          <CardTitle>回测结果</CardTitle>
          <CardDescription>历史回测结果和性能指标</CardDescription>
        </CardHeader>
        <CardContent>
          {activeBacktest && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-medium">回测进行中...</span>
                <Progress value={50} className="w-24" />
              </div>
            </div>
          )}
          
          <div className="space-y-4">
            {backtestResults.map((result) => (
              <Card key={result.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">
                      {strategies.find(s => s.id === result.strategy_id)?.name || '未知策略'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {new Date(result.start_date).toLocaleDateString('zh-CN')} - 
                      {new Date(result.end_date).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  
                  <Badge variant={result.status === 'COMPLETED' ? 'default' : 
                                 result.status === 'RUNNING' ? 'secondary' : 'destructive'}>
                    {result.status === 'COMPLETED' ? '已完成' : 
                     result.status === 'RUNNING' ? '进行中' : '失败'}
                  </Badge>
                </div>
                
                {result.status === 'COMPLETED' && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">总收益率</div>
                      <div className={`font-bold ${getReturnColor(result.total_return)}`}>
                        {(result.total_return * 100).toFixed(2)}%
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">年化收益率</div>
                      <div className={`font-bold ${getReturnColor(result.annual_return)}`}>
                        {(result.annual_return * 100).toFixed(2)}%
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">夏普比率</div>
                      <div className="font-bold">{result.sharpe_ratio.toFixed(2)}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">最大回撤</div>
                      <div className="font-bold text-red-600">
                        {(result.max_drawdown * 100).toFixed(2)}%
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">胜率</div>
                      <div className="font-bold">{(result.win_rate * 100).toFixed(1)}%</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">交易次数</div>
                      <div className="font-bold">{result.total_trades}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">初始资金</div>
                      <div className="font-bold">${result.initial_capital.toLocaleString()}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-sm text-muted-foreground">最终资金</div>
                      <div className="font-bold">${result.final_capital.toLocaleString()}</div>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}