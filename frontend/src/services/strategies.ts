/**
 * 策略管理API服务
 */

import { apiClient } from './api';

export interface Strategy {
  id: string;
  name: string;
  type: 'machine_learning' | 'lstm_prediction' | 'reinforcement_learning' | 'moving_average' | 'rsi' | 'bollinger_bands' | 'macd';
  description?: string;
  is_active: boolean;
  config: StrategyConfig;
  performance: StrategyPerformance;
  created_at: string;
  updated_at: string;
  last_signal_time?: string;
  total_signals: number;
  successful_trades: number;
}

export interface StrategyConfig {
  symbol: string;
  quantity: number;
  confidence_threshold: number;
  position_limit: number;
  stop_loss?: number;
  take_profit?: number;
  [key: string]: any;
}

export interface StrategyPerformance {
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
  profit_factor: number;
  avg_trade_return: number;
  last_updated: string;
}

export interface StrategyTemplate {
  name: string;
  type: Strategy['type'];
  description: string;
  default_config: Partial<StrategyConfig>;
  parameters: StrategyParameter[];
}

export interface StrategyParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  label: string;
  description: string;
  default_value: any;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ value: any; label: string }>;
  required: boolean;
}

export interface BacktestRequest {
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  config?: Partial<StrategyConfig>;
}

export interface BacktestResult {
  id: string;
  status: 'running' | 'completed' | 'failed';
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital?: number;
  total_return?: number;
  annual_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  total_trades?: number;
  profit_factor?: number;
  equity_curve?: Array<{ timestamp: string; value: number }>;
  trades?: Array<{
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
    side: 'buy' | 'sell';
  }>;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

class StrategyService {
  /**
   * 获取所有策略
   */
  async getStrategies(filters?: {
    type?: string;
    is_active?: boolean;
    symbol?: string;
  }): Promise<Strategy[]> {
    const response = await apiClient.get('/api/strategies', {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取单个策略详情
   */
  async getStrategy(id: string): Promise<Strategy> {
    const response = await apiClient.get(`/api/strategies/${id}`);
    return response.data;
  }

  /**
   * 创建策略
   */
  async createStrategy(strategy: {
    name: string;
    type: Strategy['type'];
    description?: string;
    config: StrategyConfig;
  }): Promise<Strategy> {
    const response = await apiClient.post('/api/strategies', strategy);
    return response.data;
  }

  /**
   * 更新策略
   */
  async updateStrategy(id: string, updates: {
    name?: string;
    description?: string;
    config?: Partial<StrategyConfig>;
  }): Promise<Strategy> {
    const response = await apiClient.put(`/api/strategies/${id}`, updates);
    return response.data;
  }

  /**
   * 删除策略
   */
  async deleteStrategy(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/api/strategies/${id}`);
    return response.data;
  }

  /**
   * 启动策略
   */
  async startStrategy(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.post(`/api/strategies/${id}/start`);
    return response.data;
  }

  /**
   * 停止策略
   */
  async stopStrategy(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.post(`/api/strategies/${id}/stop`);
    return response.data;
  }

  /**
   * 获取策略性能
   */
  async getStrategyPerformance(id: string): Promise<StrategyPerformance> {
    const response = await apiClient.get(`/api/strategies/${id}/performance`);
    return response.data;
  }

  /**
   * 获取策略信号历史
   */
  async getStrategySignals(id: string, filters?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<Array<{
    timestamp: string;
    signal: 'buy' | 'sell' | 'hold';
    strength: number;
    confidence: number;
    price: number;
    metadata?: Record<string, any>;
  }>> {
    const response = await apiClient.get(`/api/strategies/${id}/signals`, {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取策略模板
   */
  async getStrategyTemplates(): Promise<StrategyTemplate[]> {
    const response = await apiClient.get('/api/strategies/templates');
    return response.data;
  }

  /**
   * 根据策略类型创建配置
   */
  createStrategyConfig(type: Strategy['type'], baseConfig: Partial<StrategyConfig>): StrategyConfig {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '');
    const baseName = `${type}_${timestamp}`;

    const defaultConfigs: Record<Strategy['type'], Partial<StrategyConfig>> = {
      machine_learning: {
        model_type: 'random_forest',
        retrain_interval: 3600,
        confidence_threshold: 0.7
      },
      lstm_prediction: {
        sequence_length: 60,
        prediction_horizon: 5,
        model_path: `models/lstm_${timestamp}.pkl`
      },
      reinforcement_learning: {
        state_size: 20,
        epsilon: 0.1,
        learning_rate: 0.001
      },
      moving_average: {
        short_period: 10,
        long_period: 30,
        signal_threshold: 0.02
      },
      rsi: {
        rsi_period: 14,
        oversold: 30,
        overbought: 70
      },
      bollinger_bands: {
        period: 20,
        std_dev: 2,
        position_threshold: 0.1
      },
      macd: {
        fast_period: 12,
        slow_period: 26,
        signal_period: 9
      }
    };

    const typeConfig = defaultConfigs[type] || {};

    return {
      symbol: 'BTCUSDT',
      quantity: 0.001,
      confidence_threshold: 0.7,
      position_limit: 0.1,
      stop_loss: 0.05,
      take_profit: 0.1,
      strategy_name: baseName,
      ...typeConfig,
      ...baseConfig
    } as StrategyConfig;
  }

  /**
   * 运行回测
   */
  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    const response = await apiClient.post('/api/strategies/backtest', request);
    return response.data;
  }

  /**
   * 获取回测结果
   */
  async getBacktestResult(id: string): Promise<BacktestResult> {
    const response = await apiClient.get(`/api/strategies/backtest/${id}`);
    return response.data;
  }

  /**
   * 获取回测列表
   */
  async getBacktestList(strategyId?: string): Promise<BacktestResult[]> {
    const response = await apiClient.get('/api/strategies/backtest', {
      params: strategyId ? { strategy_id: strategyId } : {}
    });
    return response.data;
  }

  /**
   * 优化策略参数
   */
  async optimizeStrategy(strategyId: string, optimizationConfig: {
    start_date: string;
    end_date: string;
    optimization_method: 'grid_search' | 'bayesian' | 'random';
    parameter_ranges: Record<string, { min: number; max: number; step?: number }>;
    objective: 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'win_rate';
  }): Promise<{
    optimization_id: string;
    status: 'running' | 'completed' | 'failed';
    best_params?: Record<string, any>;
    best_score?: number;
    results?: Array<{ params: Record<string, any>; score: number }>;
  }> {
    const response = await apiClient.post(`/api/strategies/${strategyId}/optimize`, optimizationConfig);
    return response.data;
  }

  /**
   * 获取优化结果
   */
  async getOptimizationResult(optimizationId: string): Promise<{
    optimization_id: string;
    status: 'running' | 'completed' | 'failed';
    best_params?: Record<string, any>;
    best_score?: number;
    results?: Array<{ params: Record<string, any>; score: number }>;
  }> {
    const response = await apiClient.get(`/api/strategies/optimization/${optimizationId}`);
    return response.data;
  }

  /**
   * 导出策略配置
   */
  async exportStrategy(id: string): Promise<string> {
    const response = await apiClient.get(`/api/strategies/${id}/export`, {
      responseType: 'blob'
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `strategy_${id}_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    return url;
  }

  /**
   * 导入策略配置
   */
  async importStrategy(file: File): Promise<Strategy> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/strategies/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  }

  /**
   * 复制策略
   */
  async duplicateStrategy(id: string, newName?: string): Promise<Strategy> {
    const original = await this.getStrategy(id);
    const newStrategy = {
      name: newName || `${original.name} (copy)`,
      type: original.type,
      description: original.description ? `${original.description} (copied)` : undefined,
      config: original.config
    };
    
    return this.createStrategy(newStrategy);
  }

  /**
   * 获取策略状态摘要
   */
  getStrategySummary(strategies: Strategy[]): {
    total: number;
    active: number;
    inactive: number;
    by_type: Record<string, number>;
    avg_performance: {
      total_return: number;
      sharpe_ratio: number;
      win_rate: number;
    };
  } {
    const summary = {
      total: strategies.length,
      active: strategies.filter(s => s.is_active).length,
      inactive: strategies.filter(s => !s.is_active).length,
      by_type: {} as Record<string, number>,
      avg_performance: {
        total_return: 0,
        sharpe_ratio: 0,
        win_rate: 0
      }
    };

    // 按类型统计
    strategies.forEach(strategy => {
      summary.by_type[strategy.type] = (summary.by_type[strategy.type] || 0) + 1;
      
      // 累计性能指标
      summary.avg_performance.total_return += strategy.performance.total_return;
      summary.avg_performance.sharpe_ratio += strategy.performance.sharpe_ratio;
      summary.avg_performance.win_rate += strategy.performance.win_rate;
    });

    // 计算平均值
    if (strategies.length > 0) {
      summary.avg_performance.total_return /= strategies.length;
      summary.avg_performance.sharpe_ratio /= strategies.length;
      summary.avg_performance.win_rate /= strategies.length;
    }

    return summary;
  }
}

export const strategyService = new StrategyService();
export default strategyService;