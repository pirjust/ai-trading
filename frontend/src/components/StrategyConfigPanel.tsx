import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

interface StrategyConfig {
  name: string
  type: 'spot' | 'futures' | 'options'
  symbol: string
  leverage: number
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  aiEnabled: boolean
  gridSpacing: number
  gridCount: number
  stopLoss: number
  takeProfit: number
}

export default function StrategyConfigPanel() {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([
    {
      name: 'BTC合约网格',
      type: 'futures',
      symbol: 'BTCUSDT',
      leverage: 3,
      riskLevel: 'MEDIUM',
      aiEnabled: true,
      gridSpacing: 1.2,
      gridCount: 25,
      stopLoss: 10,
      takeProfit: 20
    },
    {
      name: 'ETH现货AI',
      type: 'spot',
      symbol: 'ETHUSDT',
      leverage: 1,
      riskLevel: 'LOW',
      aiEnabled: true,
      gridSpacing: 2.0,
      gridCount: 15,
      stopLoss: 5,
      takeProfit: 15
    }
  ])

  const [newStrategy, setNewStrategy] = useState<Partial<StrategyConfig>>({
    type: 'spot',
    leverage: 1,
    riskLevel: 'MEDIUM',
    aiEnabled: true,
    gridSpacing: 1.5,
    gridCount: 20,
    stopLoss: 8,
    takeProfit: 15
  })

  const addStrategy = () => {
    if (newStrategy.name && newStrategy.symbol) {
      setStrategies([...strategies, newStrategy as StrategyConfig])
      setNewStrategy({
        type: 'spot',
        leverage: 1,
        riskLevel: 'MEDIUM',
        aiEnabled: true,
        gridSpacing: 1.5,
        gridCount: 20,
        stopLoss: 8,
        takeProfit: 15
      })
    }
  }

  const toggleStrategy = (index: number) => {
    const updated = [...strategies]
    updated[index].aiEnabled = !updated[index].aiEnabled
    setStrategies(updated)
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'bg-green-500'
      case 'MEDIUM': return 'bg-yellow-500'
      case 'HIGH': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'spot': return '现货'
      case 'futures': return '合约'
      case 'options': return '期权'
      default: return type
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">策略配置管理</h2>
        <Dialog>
          <DialogTrigger asChild>
            <Button>新增策略</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>创建新策略</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>策略名称</Label>
                <Input 
                  value={newStrategy.name || ''}
                  onChange={(e) => setNewStrategy({...newStrategy, name: e.target.value})}
                  placeholder="例如：BTC合约网格"
                />
              </div>
              <div className="space-y-2">
                <Label>交易品种</Label>
                <Input 
                  value={newStrategy.symbol || ''}
                  onChange={(e) => setNewStrategy({...newStrategy, symbol: e.target.value})}
                  placeholder="例如：BTCUSDT"
                />
              </div>
              <div className="space-y-2">
                <Label>策略类型</Label>
                <Select value={newStrategy.type} onValueChange={(value: any) => setNewStrategy({...newStrategy, type: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="spot">现货</SelectItem>
                    <SelectItem value="futures">合约</SelectItem>
                    <SelectItem value="options">期权</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>杠杆倍数</Label>
                <Input 
                  type="number"
                  value={newStrategy.leverage || 1}
                  onChange={(e) => setNewStrategy({...newStrategy, leverage: Number(e.target.value)})}
                  min="1"
                  max="100"
                />
              </div>
              <div className="space-y-2">
                <Label>风险等级</Label>
                <Select value={newStrategy.riskLevel} onValueChange={(value: any) => setNewStrategy({...newStrategy, riskLevel: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">低风险</SelectItem>
                    <SelectItem value="MEDIUM">中风险</SelectItem>
                    <SelectItem value="HIGH">高风险</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>网格间距(%)</Label>
                <Input 
                  type="number"
                  value={newStrategy.gridSpacing || 1.5}
                  onChange={(e) => setNewStrategy({...newStrategy, gridSpacing: Number(e.target.value)})}
                  step="0.1"
                  min="0.1"
                  max="10"
                />
              </div>
              <div className="space-y-2">
                <Label>网格数量</Label>
                <Input 
                  type="number"
                  value={newStrategy.gridCount || 20}
                  onChange={(e) => setNewStrategy({...newStrategy, gridCount: Number(e.target.value)})}
                  min="5"
                  max="100"
                />
              </div>
              <div className="space-y-2">
                <Label>止损(%)</Label>
                <Input 
                  type="number"
                  value={newStrategy.stopLoss || 8}
                  onChange={(e) => setNewStrategy({...newStrategy, stopLoss: Number(e.target.value)})}
                  step="0.1"
                  min="1"
                  max="50"
                />
              </div>
              <div className="space-y-2">
                <Label>止盈(%)</Label>
                <Input 
                  type="number"
                  value={newStrategy.takeProfit || 15}
                  onChange={(e) => setNewStrategy({...newStrategy, takeProfit: Number(e.target.value)})}
                  step="0.1"
                  min="1"
                  max="100"
                />
              </div>
              <div className="flex items-center space-x-2 col-span-2">
                <Switch 
                  checked={newStrategy.aiEnabled}
                  onCheckedChange={(checked) => setNewStrategy({...newStrategy, aiEnabled: checked})}
                />
                <Label>启用AI优化</Label>
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline">取消</Button>
              <Button onClick={addStrategy}>创建策略</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {strategies.map((strategy, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <CardDescription>
                    {strategy.symbol} • {getTypeLabel(strategy.type)}
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getRiskColor(strategy.riskLevel)}>
                    {strategy.riskLevel}
                  </Badge>
                  <Switch 
                    checked={strategy.aiEnabled}
                    onCheckedChange={() => toggleStrategy(index)}
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">杠杆:</span>
                  <span className="ml-2">{strategy.leverage}x</span>
                </div>
                <div>
                  <span className="text-muted-foreground">网格间距:</span>
                  <span className="ml-2">{strategy.gridSpacing}%</span>
                </div>
                <div>
                  <span className="text-muted-foreground">网格数量:</span>
                  <span className="ml-2">{strategy.gridCount}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">止损:</span>
                  <span className="ml-2">{strategy.stopLoss}%</span>
                </div>
                <div>
                  <span className="text-muted-foreground">止盈:</span>
                  <span className="ml-2">{strategy.takeProfit}%</span>
                </div>
                <div>
                  <span className="text-muted-foreground">AI优化:</span>
                  <span className="ml-2">{strategy.aiEnabled ? '启用' : '禁用'}</span>
                </div>
              </div>
              <div className="mt-4 flex space-x-2">
                <Button variant="outline" size="sm">编辑</Button>
                <Button variant="outline" size="sm">回测</Button>
                <Button variant="outline" size="sm">监控</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}