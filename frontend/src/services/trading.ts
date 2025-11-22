/**
 * 交易API服务
 */

import { apiClient } from './api';

export interface TradingSignal {
  strategy_id: string;
  symbol: string;
  signal: 'buy' | 'sell' | 'hold';
  strength: number;
  confidence: number;
  timestamp: string;
  price: number;
  metadata?: Record<string, any>;
}

export interface Trade {
  id: string;
  strategy_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  price?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  created_at: string;
  updated_at: string;
  filled_quantity?: number;
  average_price?: number;
  commission?: number;
  pnl?: number;
}

export interface Position {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  percentage_pnl: number;
  leverage: number;
  margin: number;
  created_at: string;
}

export interface Balance {
  asset: string;
  free: number;
  locked: number;
  total: number;
}

export interface MarketData {
  symbol: string;
  price: number;
  price_change: number;
  price_change_percent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  timestamp: number;
}

export interface OrderBook {
  symbol: string;
  bids: Array<[number, number]>;
  asks: Array<[number, number]>;
  timestamp: number;
}

export interface KlineData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

class TradingService {
  /**
   * 获取市场数据
   */
  async getMarketData(symbol: string): Promise<MarketData> {
    const response = await apiClient.get(`/api/trading/market/${symbol}`);
    return response.data;
  }

  /**
   * 获取订单簿
   */
  async getOrderBook(symbol: string, limit: number = 100): Promise<OrderBook> {
    const response = await apiClient.get(`/api/trading/orderbook/${symbol}`, {
      params: { limit }
    });
    return response.data;
  }

  /**
   * 获取K线数据
   */
  async getKlines(symbol: string, interval: string = '1m', limit: number = 500): Promise<KlineData[]> {
    const response = await apiClient.get(`/api/trading/klines/${symbol}`, {
      params: { interval, limit }
    });
    return response.data;
  }

  /**
   * 获取账户余额
   */
  async getBalances(): Promise<Balance[]> {
    const response = await apiClient.get('/api/trading/balances');
    return response.data;
  }

  /**
   * 获取持仓信息
   */
  async getPositions(symbol?: string): Promise<Position[]> {
    const response = await apiClient.get('/api/trading/positions', {
      params: symbol ? { symbol } : {}
    });
    return response.data;
  }

  /**
   * 创建订单
   */
  async createOrder(order: {
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit';
    quantity: number;
    price?: number;
  }): Promise<Trade> {
    const response = await apiClient.post('/api/trading/orders', order);
    return response.data;
  }

  /**
   * 取消订单
   */
  async cancelOrder(orderId: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/api/trading/orders/${orderId}`);
    return response.data;
  }

  /**
   * 获取订单列表
   */
  async getOrders(filters?: {
    symbol?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Trade[]> {
    const response = await apiClient.get('/api/trading/orders', {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取订单详情
   */
  async getOrder(orderId: string): Promise<Trade> {
    const response = await apiClient.get(`/api/trading/orders/${orderId}`);
    return response.data;
  }

  /**
   * 获取交易历史
   */
  async getTradeHistory(filters?: {
    symbol?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<Trade[]> {
    const response = await apiClient.get('/api/trading/trades', {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取交易信号
   */
  async getTradingSignals(filters?: {
    strategy_id?: string;
    symbol?: string;
    signal?: string;
    limit?: number;
  }): Promise<TradingSignal[]> {
    const response = await apiClient.get('/api/trading/signals', {
      params: filters
    });
    return response.data;
  }

  /**
   * 获取策略性能
   */
  async getStrategyPerformance(strategyId: string): Promise<{
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    profit_factor: number;
    equity_curve: Array<{ timestamp: string; value: number }>;
  }> {
    const response = await apiClient.get(`/api/trading/strategies/${strategyId}/performance`);
    return response.data;
  }

  /**
   * 获取实时价格更新
   */
  subscribePriceUpdates(symbols: string[], callback: (data: MarketData) => void): () => void {
    const ws = new WebSocket(`ws://localhost:8000/ws/price`);
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        symbols
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'price_update') {
          callback(data.data);
        }
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
   * 获取实时交易更新
   */
  subscribeTradeUpdates(callback: (trade: Trade) => void): () => void {
    const ws = new WebSocket('ws://localhost:8000/ws/trades');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'trades'
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'trade_update') {
          callback(data.data);
        }
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
   * 获取实时信号更新
   */
  subscribeSignalUpdates(callback: (signal: TradingSignal) => void): () => void {
    const ws = new WebSocket('ws://localhost:8000/ws/signals');
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'signals'
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'signal_update') {
          callback(data.data);
        }
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
   * 计算仓位价值
   */
  calculatePositionValue(position: Position): number {
    return position.quantity * position.mark_price;
  }

  /**
   * 计算仓位盈亏百分比
   */
  calculatePositionPnLPercentage(position: Position): number {
    if (position.side === 'long') {
      return ((position.mark_price - position.entry_price) / position.entry_price) * 100;
    } else {
      return ((position.entry_price - position.mark_price) / position.entry_price) * 100;
    }
  }

  /**
   * 格式化价格
   */
  formatPrice(price: number, decimals: number = 2): string {
    return price.toFixed(decimals);
  }

  /**
   * 格式化百分比
   */
  formatPercentage(value: number, decimals: number = 2): string {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(decimals)}%`;
  }

  /**
   * 格式化数量
   */
  formatQuantity(quantity: number, decimals: number = 6): string {
    return quantity.toFixed(decimals);
  }
}

export const tradingService = new TradingService();
export default tradingService;