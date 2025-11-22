import React, { createContext, useContext, useState, useEffect } from 'react'
import { formatCurrency, formatPercentage } from '@/lib/utils'

interface TradingData {
  exchange: string
  symbol: string
  price: number
  volume: number
  priceChange: number
  priceChangePercent: number
  timestamp: number
}

interface AccountData {
  accountType: 'spot' | 'contract' | 'option'
  balance: number
  available: number
  frozen: number
  pnl: number
  pnlPercent: number
}

interface StrategyData {
  id: string
  name: string
  status: 'active' | 'paused' | 'stopped'
  accountType: 'spot' | 'contract' | 'option'
  exchange: string
  symbol: string
  currentPrice: number
  profit: number
  profitPercent: number
  gridLevels: number
}

interface RiskData {
  var: number
  maxDrawdown: number
  sharpeRatio: number
  leverage: number
  alerts: Array<{
    level: 'warning' | 'critical'
    message: string
    timestamp: number
  }>
}

interface TradingContextType {
  // 实时数据
  tradingData: TradingData[]
  accounts: AccountData[]
  strategies: StrategyData[]
  riskData: RiskData
  
  // 状态
  isLoading: boolean
  isConnected: boolean
  
  // 操作
  refreshData: () => void
  toggleStrategy: (strategyId: string, status: 'active' | 'paused' | 'stopped') => void
  updateRiskSettings: (settings: Partial<RiskData>) => void
}

const TradingContext = createContext<TradingContextType | undefined>(undefined)

// 模拟数据生成器
const generateMockData = (): TradingContextType => {
  const tradingData: TradingData[] = [
    {
      exchange: 'binance',
      symbol: 'BTCUSDT',
      price: 45000.50,
      volume: 1200.5,
      priceChange: 500.25,
      priceChangePercent: 1.12,
      timestamp: Date.now()
    },
    {
      exchange: 'okx',
      symbol: 'ETHUSDT',
      price: 2500.75,
      volume: 8500.3,
      priceChange: 25.50,
      priceChangePercent: 1.03,
      timestamp: Date.now()
    }
  ]

  const accounts: AccountData[] = [
    {
      accountType: 'spot',
      balance: 100000,
      available: 85000,
      frozen: 15000,
      pnl: 2500,
      pnlPercent: 2.5
    },
    {
      accountType: 'contract',
      balance: 50000,
      available: 45000,
      frozen: 5000,
      pnl: -500,
      pnlPercent: -1.0
    },
    {
      accountType: 'option',
      balance: 20000,
      available: 18000,
      frozen: 2000,
      pnl: 800,
      pnlPercent: 4.0
    }
  ]

  const strategies: StrategyData[] = [
    {
      id: '1',
      name: 'BTC网格策略',
      status: 'active',
      accountType: 'spot',
      exchange: 'binance',
      symbol: 'BTCUSDT',
      currentPrice: 45000.50,
      profit: 1200,
      profitPercent: 2.4,
      gridLevels: 20
    },
    {
      id: '2',
      name: 'ETH合约策略',
      status: 'paused',
      accountType: 'contract',
      exchange: 'okx',
      symbol: 'ETHUSDT',
      currentPrice: 2500.75,
      profit: -300,
      profitPercent: -1.2,
      gridLevels: 15
    }
  ]

  const riskData: RiskData = {
    var: 5000,
    maxDrawdown: -8.5,
    sharpeRatio: 1.8,
    leverage: 3.2,
    alerts: [
      {
        level: 'warning',
        message: 'ETH合约策略亏损超过阈值',
        timestamp: Date.now() - 300000
      }
    ]
  }

  return {
    tradingData,
    accounts,
    strategies,
    riskData,
    isLoading: false,
    isConnected: true,
    refreshData: () => {},
    toggleStrategy: () => {},
    updateRiskSettings: () => {}
  }
}

export const TradingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [data, setData] = useState<TradingContextType>(generateMockData())

  const refreshData = () => {
    setData(prev => ({
      ...prev,
      tradingData: prev.tradingData.map(item => ({
        ...item,
        price: item.price * (1 + (Math.random() - 0.5) * 0.01),
        timestamp: Date.now()
      }))
    }))
  }

  const toggleStrategy = (strategyId: string, status: 'active' | 'paused' | 'stopped') => {
    setData(prev => ({
      ...prev,
      strategies: prev.strategies.map(strategy =>
        strategy.id === strategyId ? { ...strategy, status } : strategy
      )
    }))
  }

  const updateRiskSettings = (settings: Partial<RiskData>) => {
    setData(prev => ({
      ...prev,
      riskData: { ...prev.riskData, ...settings }
    }))
  }

  useEffect(() => {
    const interval = setInterval(refreshData, 5000) // 每5秒更新数据
    return () => clearInterval(interval)
  }, [])

  const value: TradingContextType = {
    ...data,
    refreshData,
    toggleStrategy,
    updateRiskSettings
  }

  return (
    <TradingContext.Provider value={value}>
      {children}
    </TradingContext.Provider>
  )
}

export const useTrading = () => {
  const context = useContext(TradingContext)
  if (context === undefined) {
    throw new Error('useTrading must be used within a TradingProvider')
  }
  return context
}