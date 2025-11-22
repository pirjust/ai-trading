import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'

interface RiskMetric {
  name: string
  value: number
  threshold: number
  status: 'SAFE' | 'WARNING' | 'DANGER'
  trend: 'UP' | 'DOWN' | 'STABLE'
}

interface Alert {
  id: string
  type: 'INFO' | 'WARNING' | 'DANGER'
  message: string
  timestamp: string
  resolved: boolean
}

interface RiskStatus {
  monitoring_status: {
    is_running: boolean
    monitoring_tasks: number
    active_alerts: number
    risk_events: number
    subscribers: number
  }
  risk_summary: {
    portfolio_value: number
    risk_metrics: {
      var_95: number
      var_99: number
      expected_shortfall: number
      concentration_risk: number
      liquidity_risk: number
    }
    active_alerts: Array<{
      level: string
      type: string
      symbol: string
      message: string
      timestamp: string
    }>
  }
}

export default function RiskManagement() {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([
    {
      name: 'VaR(95%)风险值',
      value: 0,
      threshold: 1000,
      status: 'SAFE',
      trend: 'STABLE'
    },
    {
      name: '预期亏损(ES)',
      value: 0,
      threshold: 800,
      status: 'SAFE',
      trend: 'STABLE'
    },
    {
      name: '集中度风险',
      value: 0,
      threshold: 0.3,
      status: 'SAFE',
      trend: 'STABLE'
    },
    {
      name: '流动性风险',
      value: 0,
      threshold: 0.5,
      status: 'SAFE',
      trend: 'STABLE'
    }
  ])

  const [alerts, setAlerts] = useState<Alert[]>([])
  const [riskStatus, setRiskStatus] = useState<RiskStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [monitorStatus, setMonitorStatus] = useState<'stopped' | 'starting' | 'running' | 'stopping'>('stopped')

  const { toast } = useToast()

  useEffect(() => {
    loadRiskStatus()
    const interval = setInterval(loadRiskStatus, 5000) // 每5秒更新一次
    return () => clearInterval(interval)
  }, [])

  const loadRiskStatus = async () => {
    try {
      const response = await apiClient.get('/risk/status')
      setRiskStatus(response.data)
      
      // 更新风险指标
      if (response.data.risk_summary) {
        const metrics = [...riskMetrics]
        const riskMetricsData = response.data.risk_summary.risk_metrics
        
        // VaR(95%)
        metrics[0].value = Math.min((riskMetricsData.var_95 / 10000) * 100, 100)
        metrics[0].status = riskMetricsData.var_95 > 1000 ? 'WARNING' : 'SAFE'
        
        // 预期亏损
        metrics[1].value = Math.min((riskMetricsData.expected_shortfall / 8000) * 100, 100)
        metrics[1].status = riskMetricsData.expected_shortfall > 800 ? 'WARNING' : 'SAFE'
        
        // 集中度风险
        metrics[2].value = Math.min((riskMetricsData.concentration_risk / 0.3) * 100, 100)
        metrics[2].status = riskMetricsData.concentration_risk > 0.3 ? 'WARNING' : 'SAFE'
        
        // 流动性风险
        metrics[3].value = Math.min((riskMetricsData.liquidity_risk / 0.5) * 100, 100)
        metrics[3].status = riskMetricsData.liquidity_risk > 0.5 ? 'WARNING' : 'SAFE'
        
        setRiskMetrics(metrics)
      }
      
      // 更新警报
      if (response.data.risk_summary.active_alerts) {
        const newAlerts = response.data.risk_summary.active_alerts.map(alert => ({
          id: alert.level + '_' + alert.timestamp,
          type: alert.level === 'critical' ? 'DANGER' : 
                alert.level === 'high' ? 'WARNING' : 'INFO',
          message: alert.message,
          timestamp: alert.timestamp,
          resolved: false
        }))
        setAlerts(newAlerts)
      }
      
      // 更新监控状态
      if (response.data.monitoring_status) {
        setMonitorStatus(response.data.monitoring_status.is_running ? 'running' : 'stopped')
      }
      
    } catch (error) {
      console.error('加载风险状态失败:', error)
      toast({
        title: '加载失败',
        description: '无法获取风险监控状态',
        variant: 'destructive'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const startRiskMonitoring = async () => {
    try {
      setMonitorStatus('starting')
      await apiClient.post('/risk/control/start')
      toast({
        title: '启动成功',
        description: '风险监控服务已启动'
      })
      await loadRiskStatus()
    } catch (error) {
      setMonitorStatus('stopped')
      toast({
        title: '启动失败',
        description: '无法启动风险监控服务',
        variant: 'destructive'
      })
    }
  }

  const stopRiskMonitoring = async () => {
    try {
      setMonitorStatus('stopping')
      await apiClient.post('/risk/control/stop')
      toast({
        title: '停止成功',
        description: '风险监控服务已停止'
      })
      await loadRiskStatus()
    } catch (error) {
      setMonitorStatus('running')
      toast({
        title: '停止失败',
        description: '无法停止风险监控服务',
        variant: 'destructive'
      })
    }
  }

  const resolveAlert = (id: string) => {
    setAlerts(alerts.map(alert => 
      alert.id === id ? { ...alert, resolved: true } : alert
    ))
    
    toast({
      title: '报警已处理',
      description: '报警状态已更新为已解决'
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SAFE': return 'bg-green-500'
      case 'WARNING': return 'bg-yellow-500'
      case 'DANGER': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'INFO': return 'bg-blue-500'
      case 'WARNING': return 'bg-yellow-500'
      case 'DANGER': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">风险管理系统</h1>

      {/* 风险指标概览 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">总体风险评分</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">82/100</div>
            <p className="text-xs text-muted-foreground">风险可控，系统运行正常</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">活跃报警</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">2</div>
            <p className="text-xs text-muted-foreground">需要关注的报警数量</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">系统健康度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">95%</div>
            <p className="text-xs text-muted-foreground">所有组件运行正常</p>
          </CardContent>
        </Card>
      </div>

      {/* 详细风险指标 */}
      <Card>
        <CardHeader>
          <CardTitle>风险指标监控</CardTitle>
          <CardDescription>实时风险指标和趋势分析</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskMetrics.map((metric) => (
              <div key={metric.name} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{metric.name}</span>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(metric.status)}>
                      {metric.status === 'SAFE' ? '安全' : 
                       metric.status === 'WARNING' ? '警告' : '危险'}
                    </Badge>
                    <span className="text-sm font-bold">{metric.value}%</span>
                  </div>
                </div>
                
                <Progress value={metric.value} className="h-2" />
                
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>阈值: {metric.threshold}%</span>
                  <span>趋势: {metric.trend === 'UP' ? '上升' : metric.trend === 'DOWN' ? '下降' : '稳定'}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 账户隔离监控 */}
      <Card>
        <CardHeader>
          <CardTitle>账户隔离监控</CardTitle>
          <CardDescription>合约、现货、期权账户资金隔离状态</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="font-semibold">合约账户</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
              <div className="text-sm text-muted-foreground mt-1">
                资金使用率: 65%
              </div>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">现货账户</div>
              <Badge className="bg-green-500 mt-2">正常</Badge>
              <div className="text-sm text-muted-foreground mt-1">
                资金使用率: 45%
              </div>
            </div>
            
            <div className="text-center">
              <div className="font-semibold">期权账户</div>
              <Badge className="bg-yellow-500 mt-2">警告</Badge>
              <div className="text-sm text-muted-foreground mt-1">
                资金使用率: 78%
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 报警日志 */}
      <Card>
        <CardHeader>
          <CardTitle>报警日志</CardTitle>
          <CardDescription>系统异常和风险事件记录</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className={`p-3 rounded-lg border ${
                alert.resolved ? 'bg-muted/50' : 'bg-background'
              }`}>
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-2">
                    <Badge className={getAlertColor(alert.type)}>
                      {alert.type === 'INFO' ? '信息' : 
                       alert.type === 'WARNING' ? '警告' : '危险'}
                    </Badge>
                    <span className={alert.resolved ? 'line-through text-muted-foreground' : ''}>
                      {alert.message}
                    </span>
                  </div>
                  
                  {!alert.resolved && (
                    <Button variant="outline" size="sm" onClick={() => resolveAlert(alert.id)}>
                      标记为已解决
                    </Button>
                  )}
                </div>
                
                <div className="text-xs text-muted-foreground mt-1">
                  {new Date(alert.timestamp).toLocaleString('zh-CN')}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 风险控制操作 */}
      <Card>
        <CardHeader>
          <CardTitle>风险控制操作</CardTitle>
          <CardDescription>紧急风险控制措施</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline">暂停所有策略</Button>
            <Button variant="outline">强制平仓</Button>
            <Button variant="outline">隔离问题账户</Button>
            <Button variant="destructive">紧急停止系统</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}