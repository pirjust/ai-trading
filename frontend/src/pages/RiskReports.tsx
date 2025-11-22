import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'

interface RiskReport {
  report_id: string
  report_type: string
  start_time: string
  end_time: string
  generated_at: string
  active_alerts: number
  critical_alerts: number
}

interface RiskMetric {
  name: string
  value: number
  threshold: number
  status: string
  trend: string
  description: string
}

interface PortfolioRisk {
  portfolio_value: number
  var_95: number
  var_99: number
  expected_shortfall: number
  concentration_risk: number
  liquidity_risk: number
  max_drawdown: number
  sharpe_ratio: number
}

interface PositionRisk {
  symbol: string
  position_value: number
  risk_score: number
  volatility: number
  correlation: number
  margin_usage: number
}

interface ReportDetail {
  report_id: string
  report_type: string
  start_time: string
  end_time: string
  generated_at: string
  risk_metrics: RiskMetric[]
  portfolio_risk: PortfolioRisk
  position_risks: PositionRisk[]
  active_alerts: number
  critical_alerts: number
  recommendations: string[]
  monitoring_status: any
}

export default function RiskReports() {
  const [reports, setReports] = useState<RiskReport[]>([])
  const [selectedReport, setSelectedReport] = useState<ReportDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [reportType, setReportType] = useState('daily')

  const { toast } = useToast()

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get('/risk/reports?limit=50')
      setReports(response.data.reports)
    } catch (error) {
      console.error('加载报告失败:', error)
      toast({
        title: '加载失败',
        description: '无法获取风险报告列表',
        variant: 'destructive'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const generateReport = async () => {
    try {
      setIsGenerating(true)
      const response = await apiClient.get(`/risk/reports/generate?report_type=${reportType}`)
      
      toast({
        title: '生成成功',
        description: '风险报告已生成',
      })
      
      // 重新加载报告列表
      await loadReports()
      
      // 自动查看新生成的报告
      await viewReport(response.data.report_id)
    } catch (error) {
      console.error('生成报告失败:', error)
      toast({
        title: '生成失败',
        description: '无法生成风险报告',
        variant: 'destructive'
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const viewReport = async (reportId: string) => {
    try {
      const response = await apiClient.get(`/risk/reports/${reportId}`)
      setSelectedReport(response.data)
    } catch (error) {
      console.error('查看报告失败:', error)
      toast({
        title: '查看失败',
        description: '无法获取报告详情',
        variant: 'destructive'
      })
    }
  }

  const exportReport = async (reportId: string, format: string) => {
    try {
      const response = await apiClient.get(`/risk/reports/${reportId}/export?format=${format}`)
      
      // 创建下载链接
      const blob = new Blob([response.data.content], { type: response.data.content_type })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `risk_report_${reportId}.${format}`
      link.click()
      
      toast({
        title: '导出成功',
        description: '风险报告已导出',
      })
    } catch (error) {
      console.error('导出报告失败:', error)
      toast({
        title: '导出失败',
        description: '无法导出风险报告',
        variant: 'destructive'
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SAFE': return 'bg-green-500'
      case 'WARNING': return 'bg-yellow-500'
      case 'DANGER': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getReportTypeName = (type: string) => {
    switch (type) {
      case 'daily': return '日报'
      case 'weekly': return '周报'
      case 'monthly': return '月报'
      case 'real_time': return '实时报告'
      default: return type
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">风险报告系统</h1>

      {/* 报告生成控制 */}
      <Card>
        <CardHeader>
          <CardTitle>生成风险报告</CardTitle>
          <CardDescription>选择报告类型并生成详细的风险分析报告</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">报告类型</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">日报</SelectItem>
                  <SelectItem value="weekly">周报</SelectItem>
                  <SelectItem value="monthly">月报</SelectItem>
                  <SelectItem value="real_time">实时报告</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={generateReport} disabled={isGenerating}>
              {isGenerating ? '生成中...' : '生成报告'}
            </Button>
            
            <Button variant="outline" onClick={loadReports}>
              刷新列表
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="reports" className="space-y-4">
        <TabsList>
          <TabsTrigger value="reports">报告列表</TabsTrigger>
          <TabsTrigger value="dashboard">风险仪表板</TabsTrigger>
        </TabsList>

        {/* 报告列表 */}
        <TabsContent value="reports" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-8">加载中...</div>
          ) : reports.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">暂无风险报告</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {reports.map((report) => (
                <Card key={report.report_id} className="cursor-pointer hover:bg-muted/50"
                      onClick={() => viewReport(report.report_id)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="secondary">{getReportTypeName(report.report_type)}</Badge>
                          <span className="font-medium">{report.report_id}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          时间范围: {new Date(report.start_time).toLocaleDateString()} - {new Date(report.end_time).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div className="text-right">
                        <div className="flex items-center space-x-2">
                          {report.critical_alerts > 0 && (
                            <Badge variant="destructive">危急: {report.critical_alerts}</Badge>
                          )}
                          {report.active_alerts > 0 && (
                            <Badge variant="default">警报: {report.active_alerts}</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {new Date(report.generated_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 风险仪表板 */}
        <TabsContent value="dashboard" className="space-y-4">
          {selectedReport ? (
            <div className="space-y-6">
              {/* 报告概览 */}
              <Card>
                <CardHeader>
                  <CardTitle>报告概览</CardTitle>
                  <CardDescription>
                    {getReportTypeName(selectedReport.report_type)} - {selectedReport.report_id}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{selectedReport.portfolio_risk.portfolio_value.toLocaleString()}</div>
                      <div className="text-sm text-muted-foreground">组合价值</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">{selectedReport.active_alerts}</div>
                      <div className="text-sm text-muted-foreground">活跃警报</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">{selectedReport.critical_alerts}</div>
                      <div className="text-sm text-muted-foreground">危急警报</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">{selectedReport.position_risks.length}</div>
                      <div className="text-sm text-muted-foreground">监控仓位</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 风险指标 */}
              <Card>
                <CardHeader>
                  <CardTitle>风险指标监控</CardTitle>
                  <CardDescription>主要风险指标和阈值监控</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {selectedReport.risk_metrics.map((metric) => (
                      <div key={metric.name} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{metric.name}</span>
                          <div className="flex items-center space-x-2">
                            <Badge className={getStatusColor(metric.status)}>
                              {metric.status === 'SAFE' ? '安全' : 
                               metric.status === 'WARNING' ? '警告' : '危险'}
                            </Badge>
                            <span className="text-sm font-bold">{metric.value.toFixed(2)}</span>
                          </div>
                        </div>
                        
                        <Progress value={Math.min((metric.value / metric.threshold) * 100, 100)} className="h-2" />
                        
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>阈值: {metric.threshold}</span>
                          <span>{metric.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 仓位风险分析 */}
              <Card>
                <CardHeader>
                  <CardTitle>仓位风险分析</CardTitle>
                  <CardDescription>各交易对的详细风险分析</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedReport.position_risks.map((position) => (
                      <Card key={position.symbol} className="p-4">
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="font-bold">{position.symbol}</span>
                            <Badge variant={position.risk_score > 0.7 ? "destructive" : 
                                           position.risk_score > 0.4 ? "default" : "secondary"}>
                              风险评分: {(position.risk_score * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>价值: {position.position_value.toLocaleString()}</div>
                            <div>波动率: {(position.volatility * 100).toFixed(1)}%</div>
                            <div>相关性: {(position.correlation * 100).toFixed(1)}%</div>
                            <div>保证金: {(position.margin_usage * 100).toFixed(1)}%</div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 建议措施 */}
              <Card>
                <CardHeader>
                  <CardTitle>建议措施</CardTitle>
                  <CardDescription>基于风险分析的建议措施</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {selectedReport.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-green-500">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* 导出选项 */}
              <Card>
                <CardHeader>
                  <CardTitle>导出报告</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-2">
                    <Button variant="outline" onClick={() => exportReport(selectedReport.report_id, 'json')}>
                      导出 JSON
                    </Button>
                    <Button variant="outline" onClick={() => exportReport(selectedReport.report_id, 'csv')}>
                      导出 CSV
                    </Button>
                    <Button variant="outline" onClick={() => exportReport(selectedReport.report_id, 'html')}>
                      导出 HTML
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">请选择一个报告查看详情</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}