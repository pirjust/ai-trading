import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import RealtimeTradingMonitor from '@/components/RealtimeTradingMonitor'

interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'NORMAL' | 'WARNING' | 'CRITICAL'
  trend: 'UP' | 'DOWN' | 'STABLE'
}

interface LogEntry {
  id: string
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  component: string
}

export default function Monitoring() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([
    {
      name: 'CPU使用率',
      value: 45.2,
      unit: '%',
      status: 'NORMAL',
      trend: 'STABLE'
    },
    {
      name: '内存使用率',
      value: 67.8,
      unit: '%',
      status: 'WARNING',
      trend: 'UP'
    },
    {
      name: '磁盘使用率',
      value: 82.5,
      unit: '%',
      status: 'CRITICAL',
      trend: 'UP'
    },
    {
      name: '网络延迟',
      value: 12.3,
      unit: 'ms',
      status: 'NORMAL',
      trend: 'STABLE'
    },
    {
      name: '数据库连接数',
      value: 23,
      unit: '',
      status: 'NORMAL',
      trend: 'STABLE'
    },
    {
      name: 'API响应时间',
      value: 156,
      unit: 'ms',
      status: 'NORMAL',
      trend: 'DOWN'
    }
  ])

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: '1',
      timestamp: new Date(Date.now() - 120000).toISOString(),
      level: 'INFO',
      message: '数据采集器启动成功',
      component: 'DataCollector'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 180000).toISOString(),
      level: 'WARNING',
      message: '内存使用率超过阈值',
      component: 'SystemMonitor'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 240000).toISOString(),
      level: 'ERROR',
      message: '交易所API连接失败',
      component: 'ExchangeAPI'
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      level: 'INFO',
      message: '风险引擎检查完成',
      component: 'RiskEngine'
    }
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      // 模拟系统指标更新
      setSystemMetrics(prev => prev.map(metric => ({
        ...metric,
        value: Math.max(0, Math.min(100, metric.value + (Math.random() - 0.5) * 10))
      })))
      
      // 模拟日志更新
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: ['INFO', 'WARNING', 'ERROR'][Math.floor(Math.random() * 3)] as 'INFO' | 'WARNING' | 'ERROR',
        message: '系统监控数据更新',
        component: 'SystemMonitor'
      }
      
      setLogs(prev => [newLog, ...prev.slice(0, 9)])
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NORMAL': return 'bg-green-500'
      case 'WARNING': return 'bg-yellow-500'
      case 'CRITICAL': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'bg-blue-500'
      case 'WARNING': return 'bg-yellow-500'
      case 'ERROR': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">系统监控</h1>
        <div className="flex items-center space-x-2">
          <Badge className="bg-green-500">运行正常</Badge>
          <span className="text-sm text-muted-foreground">最后更新: {new Date().toLocaleString('zh-CN')}</span>
        </div>
      </div>
      
      {/* 实时交易监控 */}
      <RealtimeTradingMonitor />

      {/* 系统指标概览 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">系统健康度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">78%</div>
            <p className="text-xs text-muted-foreground">1个严重问题需要关注</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">活跃组件</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">12/15</div>
            <p className="text-xs text-muted-foreground">系统组件运行状态</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">API可用性</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">99.8%</div>
            <p className="text-xs text-muted-foreground">交易所API连接状态</p>
          </CardContent>
        </Card>
      </div>

      {/* 详细系统指标 */}
      <Card>
        <CardHeader>
          <CardTitle>系统指标监控</CardTitle>
          <CardDescription>实时系统性能和资源使用情况</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {systemMetrics.map((metric) => (
              <div key={metric.name} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{metric.name}</span>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(metric.status)}>
                      {metric.status === 'NORMAL' ? '正常' : 
                       metric.status === 'WARNING' ? '警告' : '严重'}
                    </Badge>
                    <span className="text-lg font-bold">
                      {metric.value.toFixed(1)}{metric.unit}
                    </span>
                  </div>
                </div>
                
                <div className="text-xs text-muted-foreground">
                  趋势: {metric.trend === 'UP' ? '上升' : metric.trend === 'DOWN' ? '下降' : '稳定'}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 组件状态 */}
      <Card>
        <CardHeader>
          <CardTitle>组件状态监控</CardTitle>
          <CardDescription>系统各组件运行状态</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="font-semibold">数据采集器</div>
              <Badge className="bg-green-500 mt-2">运行中</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">策略引擎</div>
              <Badge className="bg-green-500 mt-2">运行中</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">交易执行器</div>
              <Badge className="bg-green-500 mt-2">运行中</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">风险引擎</div>
              <Badge className="bg-yellow-500 mt-2">警告</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">数据库</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">Redis缓存</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">WebSocket服务</div>
              <Badge className="bg-green-500 mt-2">运行中</Badge>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">API网关</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 实时日志 */}
      <Card>
        <CardHeader>
          <CardTitle>实时日志监控</CardTitle>
          <CardDescription>系统运行日志和错误信息</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.map((log) => (
              <div key={log.id} className="p-3 rounded-lg border bg-background">
                <div className="flex items-center space-x-2">
                  <Badge className={getLevelColor(log.level)}>
                    {log.level === 'INFO' ? '信息' : 
                     log.level === 'WARNING' ? '警告' : '错误'}
                  </Badge>
                  <span className="text-sm font-medium">{log.component}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                  </span>
                </div>
                <div className="text-sm mt-1">{log.message}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 操作面板 */}
      <Card>
        <CardHeader>
          <CardTitle>运维操作</CardTitle>
          <CardDescription>系统维护和管理操作</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline">重启数据采集器</Button>
            <Button variant="outline">清理缓存</Button>
            <Button variant="outline">导出日志</Button>
            <Button variant="outline">性能分析</Button>
            <Button variant="outline">数据库备份</Button>
            <Button variant="destructive">紧急重启</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}