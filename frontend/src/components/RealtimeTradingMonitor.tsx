/**
 * 实时交易监控组件
 */
import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'

interface Trade {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  quantity: number
  price: number
  timestamp: string
  profit: number
  status: 'OPEN' | 'CLOSED' | 'PENDING'
}

interface MarketData {
  symbol: string
  price: number
  change: number
  volume: number
  timestamp: string
}

const RealtimeTradingMonitor: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([
    {
      id: '1',
      symbol: 'BTCUSDT',
      side: 'BUY',
      quantity: 0.1,
      price: 45000,
      timestamp: new Date().toISOString(),
      profit: 125.5,
      status: 'OPEN'
    },
    {
      id: '2',
      symbol: 'ETHUSDT',
      side: 'SELL',
      quantity: 2,
      price: 2850,
      timestamp: new Date().toISOString(),
      profit: -45.2,
      status: 'CLOSED'
    }
  ])

  const [marketData, setMarketData] = useState<MarketData[]>([
    {
      symbol: 'BTCUSDT',
      price: 45050.25,
      change: 2.5,
      volume: 2850000000,
      timestamp: new Date().toISOString()
    },
    {
      symbol: 'ETHUSDT',
      price: 2855.75,
      change: 1.8,
      volume: 1850000000,
      timestamp: new Date().toISOString()
    }
  ])

  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      // 模拟实时数据更新
      setMarketData(prev => prev.map(data => ({
        ...data,
        price: data.price * (1 + (Math.random() - 0.5) * 0.01),
        change: data.change + (Math.random() - 0.5) * 0.2,
        timestamp: new Date().toISOString()
      })))

      // 模拟新交易
      if (Math.random() > 0.7) {
        const newTrade: Trade = {
          id: Date.now().toString(),
          symbol: Math.random() > 0.5 ? 'BTCUSDT' : 'ETHUSDT',
          side: Math.random() > 0.5 ? 'BUY' : 'SELL',
          quantity: Math.random() * 0.5,
          price: Math.random() > 0.5 ? 45000 : 2850,
          timestamp: new Date().toISOString(),
          profit: (Math.random() - 0.5) * 200,
          status: 'OPEN'
        }
        setTrades(prev => [newTrade, ...prev].slice(0, 10))
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'bg-green-500' : 'bg-red-500'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'bg-blue-500'
      case 'CLOSED': return 'bg-gray-500'
      case 'PENDING': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>实时交易监控</CardTitle>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">自动刷新</span>
              <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
              <Button variant="outline" size="sm">手动刷新</Button>
            </div>
          </div>
          <CardDescription>实时监控交易执行和市场数据</CardDescription>
        </CardHeader>
      </Card>

      {/* 市场数据 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {marketData.map((data) => (
          <Card key={data.symbol}>
            <CardHeader className="pb-2">
              <div className="flex justify-between items-center">
                <CardTitle className="text-lg">{data.symbol}</CardTitle>
                <Badge className={data.change >= 0 ? 'bg-green-500' : 'bg-red-500'}>
                  {formatPercentage(data.change)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">{formatCurrency(data.price)}</div>
                <div className="text-sm text-muted-foreground">
                  成交量: {formatCurrency(data.volume)}
                </div>
                <div className="text-xs text-muted-foreground">
                  更新时间: {new Date(data.timestamp).toLocaleString('zh-CN')}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 实时交易 */}
      <Card>
        <CardHeader>
          <CardTitle>实时交易</CardTitle>
          <CardDescription>最近的交易执行记录</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {trades.map((trade) => (
              <div key={trade.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <Badge className={getSideColor(trade.side)}>
                    {trade.side}
                  </Badge>
                  <div>
                    <div className="font-medium">{trade.symbol}</div>
                    <div className="text-sm text-muted-foreground">
                      {trade.quantity} @ {formatCurrency(trade.price)}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className={`text-right ${trade.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    <div className="font-medium">{formatCurrency(trade.profit)}</div>
                    <div className="text-sm">盈亏</div>
                  </div>
                  
                  <Badge className={getStatusColor(trade.status)}>
                    {trade.status === 'OPEN' ? '持仓中' : 
                     trade.status === 'CLOSED' ? '已平仓' : '等待中'}
                  </Badge>
                  
                  <div className="text-xs text-muted-foreground">
                    {new Date(trade.timestamp).toLocaleTimeString('zh-CN')}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {trades.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              暂无交易记录
            </div>
          )}
        </CardContent>
      </Card>

      {/* 性能指标 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">活跃交易</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{trades.filter(t => t.status === 'OPEN').length}</div>
            <div className="text-xs text-muted-foreground">持仓中</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">今日盈亏</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">+$1,250.50</div>
            <div className="text-xs text-muted-foreground">累计收益</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">交易频率</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <div className="text-xs text-muted-foreground">今日交易次数</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default RealtimeTradingMonitor