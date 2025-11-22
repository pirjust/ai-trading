import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface CandleData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface CandlestickChartProps {
  data: CandleData[]
  height?: number
  symbol?: string
}

export default function CandlestickChart({ data, height = 300, symbol = 'BTCUSDT' }: CandlestickChartProps) {
  // 转换数据格式用于折线图显示
  const chartData = data.map(item => ({
    time: item.time,
    price: item.close,
    volume: item.volume
  }))

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">{symbol} 价格走势</h3>
        <div className="text-sm text-muted-foreground">
          最新价: {data.length > 0 ? data[data.length - 1].close.toFixed(2) : '--'}
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            tick={{ fill: '#9CA3AF' }}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis 
            tick={{ fill: '#9CA3AF' }}
            axisLine={{ stroke: '#374151' }}
            domain={['dataMin - 100', 'dataMax + 100']}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151' }}
            labelStyle={{ color: '#F3F4F6' }}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#10B981" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#10B981', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* 简单的K线图模拟 */}
      <div className="mt-4 grid grid-cols-5 gap-2">
        {data.slice(-5).map((candle, index) => (
          <div key={index} className="text-center">
            <div className="text-xs text-muted-foreground mb-1">
              {candle.time.split(' ')[1]}
            </div>
            <div className="relative h-16 border border-gray-600 rounded">
              {/* 上影线 */}
              <div 
                className="absolute left-1/2 w-px bg-gray-400"
                style={{ 
                  height: `${Math.max(0, (candle.high - Math.max(candle.open, candle.close)) / (candle.high - candle.low) * 100)}%`,
                  top: '0%'
                }}
              />
              {/* 实体 */}
              <div 
                className={`absolute left-1/4 w-1/2 ${candle.close >= candle.open ? 'bg-green-500' : 'bg-red-500'}`}
                style={{ 
                  height: `${Math.abs(candle.close - candle.open) / (candle.high - candle.low) * 100}%`,
                  top: `${(Math.max(candle.open, candle.close) - candle.low) / (candle.high - candle.low) * 100}%`
                }}
              />
              {/* 下影线 */}
              <div 
                className="absolute left-1/2 w-px bg-gray-400"
                style={{ 
                  height: `${Math.max(0, (Math.min(candle.open, candle.close) - candle.low) / (candle.high - candle.low) * 100)}%`,
                  bottom: '0%'
                }}
              />
            </div>
            <div className="text-xs mt-1">{candle.close.toFixed(0)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}