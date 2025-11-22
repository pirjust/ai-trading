/**
 * 交易系统工具函数库
 */

/**
 * 格式化货币金额
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * 格式化百分比
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date, includeTime: boolean = true): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    ...(includeTime && {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  };
  
  return new Intl.DateTimeFormat('zh-CN', options).format(dateObj);
}

/**
 * 计算夏普比率
 */
export function calculateSharpeRatio(returns: number[], riskFreeRate: number = 0.02): number {
  if (returns.length === 0) return 0;
  
  const avgReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
  const stdDev = Math.sqrt(
    returns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / returns.length
  );
  
  if (stdDev === 0) return 0;
  return (avgReturn - riskFreeRate) / stdDev;
}

/**
 * 计算最大回撤
 */
export function calculateMaxDrawdown(prices: number[]): number {
  if (prices.length === 0) return 0;
  
  let maxDrawdown = 0;
  let peak = prices[0];
  
  for (let i = 1; i < prices.length; i++) {
    if (prices[i] > peak) {
      peak = prices[i];
    }
    
    const drawdown = (peak - prices[i]) / peak;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  
  return maxDrawdown * 100; // 转换为百分比
}

/**
 * 计算胜率
 */
export function calculateWinRate(trades: { profitLoss: number }[]): number {
  if (trades.length === 0) return 0;
  
  const winningTrades = trades.filter(trade => trade.profitLoss > 0).length;
  return (winningTrades / trades.length) * 100;
}

/**
 * 计算交易频率
 */
export function calculateTradingFrequency(trades: { timestamp: string }[], periodDays: number = 30): number {
  if (trades.length === 0) return 0;
  
  const sortedTrades = trades.sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  
  const firstTrade = new Date(sortedTrades[0].timestamp);
  const lastTrade = new Date(sortedTrades[sortedTrades.length - 1].timestamp);
  
  const daysDiff = Math.max(1, (lastTrade.getTime() - firstTrade.getTime()) / (1000 * 60 * 60 * 24));
  
  return (trades.length / daysDiff) * periodDays; // 标准化为30天频率
}

/**
 * 风险评估函数
 */
export function assessRiskLevel(
  leverage: number,
  volatility: number,
  winRate: number,
  maxDrawdown: number
): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
  let riskScore = 0;
  
  // 杠杆风险 (权重: 40%)
  if (leverage <= 2) riskScore += 10;
  else if (leverage <= 5) riskScore += 25;
  else if (leverage <= 10) riskScore += 40;
  else riskScore += 60;
  
  // 波动率风险 (权重: 30%)
  if (volatility <= 0.05) riskScore += 7.5;
  else if (volatility <= 0.15) riskScore += 15;
  else if (volatility <= 0.3) riskScore += 22.5;
  else riskScore += 30;
  
  // 胜率风险 (权重: 20%)
  if (winRate >= 70) riskScore += 5;
  else if (winRate >= 60) riskScore += 10;
  else if (winRate >= 50) riskScore += 15;
  else riskScore += 20;
  
  // 回撤风险 (权重: 10%)
  if (maxDrawdown <= 5) riskScore += 2.5;
  else if (maxDrawdown <= 10) riskScore += 5;
  else if (maxDrawdown <= 20) riskScore += 7.5;
  else riskScore += 10;
  
  // 计算总风险分数
  riskScore = riskScore * 0.4; // 标准化到40分制
  
  if (riskScore <= 10) return 'LOW';
  else if (riskScore <= 20) return 'MEDIUM';
  else if (riskScore <= 30) return 'HIGH';
  else return 'CRITICAL';
}

/**
 * 生成交易信号强度颜色
 */
export function getSignalColor(strength: number): string {
  if (strength <= 0.3) return 'text-gray-500';
  else if (strength <= 0.6) return 'text-yellow-500';
  else return 'text-green-500';
}

/**
 * 获取风险等级颜色
 */
export function getRiskColor(level: string): string {
  switch (level) {
    case 'LOW': return 'bg-green-500';
    case 'MEDIUM': return 'bg-yellow-500';
    case 'HIGH': return 'bg-orange-500';
    case 'CRITICAL': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
}

/**
 * 计算仓位大小
 */
export function calculatePositionSize(
  accountBalance: number,
  riskPerTrade: number,
  entryPrice: number,
  stopLossPrice: number
): number {
  const riskAmount = accountBalance * (riskPerTrade / 100);
  const priceRisk = Math.abs(entryPrice - stopLossPrice);
  
  if (priceRisk === 0) return 0;
  
  return riskAmount / priceRisk;
}

/**
 * 验证交易参数
 */
export function validateTradeParameters(params: {
  symbol: string;
  quantity: number;
  price: number;
  leverage?: number;
}): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // 验证交易对格式
  if (!/^[A-Z]{3,10}\/[A-Z]{3,10}$/.test(params.symbol)) {
    errors.push('交易对格式不正确');
  }
  
  // 验证数量
  if (params.quantity <= 0) {
    errors.push('交易数量必须大于0');
  }
  
  // 验证价格
  if (params.price <= 0) {
    errors.push('交易价格必须大于0');
  }
  
  // 验证杠杆
  if (params.leverage && (params.leverage < 1 || params.leverage > 100)) {
    errors.push('杠杆倍数必须在1-100之间');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 模拟交易数据生成器
 */
export function generateMockTradingData(count: number = 100) {
  const data = [];
  let basePrice = 50000; // BTC价格
  
  for (let i = 0; i < count; i++) {
    const priceChange = (Math.random() - 0.5) * 0.1; // ±5%波动
    basePrice = basePrice * (1 + priceChange);
    
    data.push({
      timestamp: new Date(Date.now() - (count - i) * 60000).toISOString(), // 每分钟一个数据点
      open: basePrice * (1 - Math.random() * 0.01),
      high: basePrice * (1 + Math.random() * 0.02),
      low: basePrice * (1 - Math.random() * 0.02),
      close: basePrice,
      volume: Math.random() * 1000
    });
  }
  
  return data;
}

export default {
  formatCurrency,
  formatPercentage,
  formatDateTime,
  calculateSharpeRatio,
  calculateMaxDrawdown,
  calculateWinRate,
  calculateTradingFrequency,
  assessRiskLevel,
  getSignalColor,
  getRiskColor,
  calculatePositionSize,
  validateTradeParameters,
  generateMockTradingData
};