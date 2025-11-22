import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'

interface ProfitData {
  date: string
  profit: number
  cumulative: number
}

interface ProfitChartProps {
  data: ProfitData[]
  height?: number
}

export default function ProfitChart({ data, height = 300 }: ProfitChartProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">累计收益曲线</h3>
        <div className="text-sm text-muted-foreground">
          累计收益: {data.length > 0 ? data[data.length - 1].cumulative.toFixed(2) : '--'} USD
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="date" 
            tick={{ fill: '#9CA3AF' }}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis 
            tick={{ fill: '#9CA3AF' }}
            axisLine={{ stroke: '#374151' }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151' }}
            labelStyle={{ color: '#F3F4F6' }}
            formatter={(value: number) => [value.toFixed(2), '收益']}
          />
          <defs>
            <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Area 
            type="monotone" 
            dataKey="cumulative" 
            stroke="#10B981" 
            fill="url(#colorProfit)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}