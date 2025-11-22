/**
 * 监控和风险管理API服务
 */

import { apiClient } from './api';

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  memory_total: number;
  memory_percent: number;
  disk_usage: number;
  disk_total: number;
  disk_percent: number;
  network_bytes_sent: number;
  network_bytes_recv: number;
  process_count: number;
  uptime: number;
  timestamp: string;
}

export interface TradingMetrics {
  total_trades: number;
  successful_trades: number;
  failed_trades: number;
  total_volume: number;
  total_pnl: number;
  daily_pnl: number;
  win_rate: number;
  avg_trade_size: number;
  active_positions: number;
  open_orders: number;
  timestamp: string;
}

export interface RiskMetrics {
  var_95: number;
  var_99: number;
  max_drawdown: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  volatility: number;
  beta: number;
  correlation_matrix?: number[][];
  timestamp: string;
}

export interface Alert {
  id: string;
  alert_id: string;
  risk_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  symbol?: string;
  value?: number;
  threshold?: number;
  action_required?: string;
  acknowledged: boolean;
  resolved_at?: string;
}

export interface PerformanceReport {
  id: string;
  report_type: 'daily' | 'weekly' | 'monthly';
  period_start: string;
  period_end: string;
  total_return: number;
  benchmark_return: number;
  alpha: number;
  beta: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  win_rate: number;
  profit_factor: number;
  trade_count: number;
  avg_trade_return: number;
  generated_at: string;
}

export interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  services: {
    web_app: 'running' | 'stopped' | 'error';
    database: 'running' | 'stopped' | 'error';
    redis: 'running' | 'stopped' | 'error';
    trading_engine: 'running' | 'stopped' | 'error';
    risk_engine: 'running' | 'stopped' | 'error';
  };
  last_check: string;
  issues: Array<{
    service: string;
    issue: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    timestamp: string;
  }>;
}

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  service: string;
  message: string;
  metadata?: Record<string, any>;
}

class MonitoringService {
  /**
   * 获取系统指标
   */
  async getSystemMetrics(timeRange?: string): Promise<SystemMetrics[]> {
    const response = await apiClient.get('/api/monitoring/system-metrics', {
      params: timeRange ? { time_range: timeRange } : {}
    });
    return response.data;
  }

  /**
   * 获取交易指标
   */
  async getTradingMetrics(timeRange?: string): Promise<TradingMetrics[]> {
    const response = await apiClient.get('/api/monitoring/trading-metrics', {
      params: timeRange ? { time_range: timeRange } : {}
    });
    return response.data;
  }

  /**
   * 获取风险指标
   */
  async getRiskMetrics(timeRange?: string): Promise<RiskMetrics[]> {
    const response = await apiClient.get('/api/monitoring/risk-metrics', {
      params: timeRange ? { time_range: timeRange } : {}
    });
    return response.data;
  }

  /**
   * 获取风险警报
   */
  async getAlerts(filters?: {
    severity?: string;
    risk_type?: string;
    acknowledged?: boolean;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<Alert[]> {
    const response = await apiClient.get('/api/monitoring/alerts', {
      params: filters
    });
    return response.data;
  }

  /**
   * 确认警报
   */
  async acknowledgeAlert(alertId: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.post(`/api/monitoring/alerts/${alertId}/acknowledge`);
    return response.data;
  }

  /**
   * 解决警报
   */
  async resolveAlert(alertId: string, resolution?: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.post(`/api/monitoring/alerts/${alertId}/resolve`, {
      resolution
    });
    return response.data;
  }

  /**
   * 获取健康状态
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await apiClient.get('/api/monitoring/health');
    return response.data;
  }

  /**
   * 获取日志
   */
  async getLogs(filters?: {
    level?: string;
    service?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<LogEntry[]> {
    const response = await apiClient.get('/api/monitoring/logs', {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取性能报告
   */
  async getPerformanceReports(filters?: {
    report_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PerformanceReport[]> {
    const response = await apiClient.get('/api/monitoring/performance-reports', {
      params: filters
    });
    return response.data;
  }

  /**
   * 生成性能报告
   */
  async generatePerformanceReport(config: {
    report_type: 'daily' | 'weekly' | 'monthly';
    start_date: string;
    end_date: string;
    include_benchmark?: boolean;
    include_charts?: boolean;
  }): Promise<PerformanceReport> {
    const response = await apiClient.post('/api/monitoring/performance-reports', config);
    return response.data;
  }

  /**
   * 获取风险报告
   */
  async getRiskReport(period?: string): Promise<{
    risk_metrics: RiskMetrics;
    alerts_summary: {
      total: number;
      by_severity: Record<string, number>;
      recent: Alert[];
    };
    portfolio_analysis: {
      total_value: number;
      concentration: Record<string, number>;
      risk_metrics: {
        herfindahl_index: number;
        max_concentration: number;
        diversification_score: number;
      };
    };
    recommendations: Array<{
      type: string;
      priority: 'low' | 'medium' | 'high' | 'critical';
      title: string;
      description: string;
      actions: string[];
    }>;
    compliance_check: {
      overall: string;
      checks: Array<{
        rule: string;
        status: string;
      }>;
      violations: Array<{
        rule: string;
        limit: string;
        actual: string;
        status: string;
      }>;
    };
  }> {
    const response = await apiClient.get('/api/monitoring/risk-report', {
      params: period ? { period } : {}
    });
    return response.data;
  }

  /**
   * 导出监控数据
   */
  async exportMonitoringData(config: {
    data_type: 'system_metrics' | 'trading_metrics' | 'risk_metrics' | 'alerts' | 'logs';
    start_date: string;
    end_date: string;
    format?: 'json' | 'csv' | 'xlsx';
  }): Promise<string> {
    const response = await apiClient.post('/api/monitoring/export', config, {
      responseType: 'blob'
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `monitoring_data_${config.data_type}_${new Date().toISOString().slice(0, 10)}.${config.format || 'json'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    return url;
  }

  /**
   * 实时监控数据订阅
   */
  subscribeMonitoringData(callback: (data: {
    type: 'system_metrics' | 'trading_metrics' | 'risk_metrics' | 'alert';
    data: any;
  }) => void): () => void {
    const ws = new WebSocket('ws://localhost:8000/ws/monitoring');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['system_metrics', 'trading_metrics', 'risk_metrics', 'alerts']
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callback(data);
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }

  /**
   * 格式化指标值
   */
  formatMetricValue(value: number, metric: string): string {
    switch (metric) {
      case 'cpu_usage':
      case 'memory_percent':
      case 'disk_percent':
        return `${value.toFixed(1)}%`;
      case 'memory_usage':
      case 'disk_usage':
        return this.formatBytes(value);
      case 'network_bytes_sent':
      case 'network_bytes_recv':
        return this.formatBytes(value);
      case 'total_trades':
      case 'successful_trades':
      case 'failed_trades':
      case 'active_positions':
      case 'open_orders':
        return value.toLocaleString();
      case 'total_pnl':
      case 'daily_pnl':
        return this.formatCurrency(value);
      case 'win_rate':
        return `${(value * 100).toFixed(1)}%`;
      case 'var_95':
      case 'var_99':
      case 'max_drawdown':
        return `${(value * 100).toFixed(2)}%`;
      case 'sharpe_ratio':
      case 'sortino_ratio':
        return value.toFixed(2);
      case 'volatility':
        return `${(value * 100).toFixed(2)}%`;
      case 'uptime':
        return this.formatDuration(value);
      default:
        return value.toString();
    }
  }

  /**
   * 格式化字节数
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 格式化货币
   */
  private formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  }

  /**
   * 格式化时长
   */
  private formatDuration(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  /**
   * 获取警报颜色
   */
  getAlertColor(severity: Alert['severity']): string {
    const colors = {
      low: '#4caf50',      // 绿色
      medium: '#ff9800',   // 橙色
      high: '#f44336',     // 红色
      critical: '#9c27b0'  // 紫色
    };
    return colors[severity] || '#666666';
  }

  /**
   * 获取健康状态颜色
   */
  getHealthColor(status: HealthStatus['status']): string {
    const colors = {
      healthy: '#4caf50',   // 绿色
      warning: '#ff9800',   // 橙色
      critical: '#f44336'   // 红色
    };
    return colors[status] || '#666666';
  }

  /**
   * 获取服务状态图标
   */
  getServiceStatusIcon(status: 'running' | 'stopped' | 'error'): string {
    const icons = {
      running: '✅',
      stopped: '⏸️',
      error: '❌'
    };
    return icons[status] || '❓';
  }

  /**
   * 计算风险等级
   */
  calculateRiskLevel(alerts: Alert[]): {
    level: 'low' | 'medium' | 'high' | 'critical';
    score: number;
    factors: string[];
  } {
    const criticalCount = alerts.filter(a => a.severity === 'critical').length;
    const highCount = alerts.filter(a => a.severity === 'high').length;
    const mediumCount = alerts.filter(a => a.severity === 'medium').length;
    const totalCount = alerts.length;

    let score = 0;
    score += criticalCount * 4;
    score += highCount * 3;
    score += mediumCount * 2;

    const factors = [];
    if (criticalCount > 0) factors.push(`${criticalCount} 个严重警报`);
    if (highCount > 0) factors.push(`${highCount} 个高危警报`);
    if (mediumCount > 0) factors.push(`${mediumCount} 个中等警报`);

    let level: 'low' | 'medium' | 'high' | 'critical' = 'low';
    if (criticalCount > 0 || score >= 10) {
      level = 'critical';
    } else if (highCount > 2 || score >= 7) {
      level = 'high';
    } else if (score >= 4) {
      level = 'medium';
    }

    return { level, score, factors };
  }
}

export const monitoringService = new MonitoringService();
export default monitoringService;