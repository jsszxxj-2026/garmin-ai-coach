import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TooltipProps } from 'recharts'
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent'
import type { ChartData, ChartDataPoint } from '../types'

interface ChartViewProps {
  data: ChartData
}

const formatPace = (seconds: number) => {
  if (!seconds || seconds <= 0) return 'N/A'
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

function SportTooltip({ active, payload }: TooltipProps<ValueType, NameType>) {
  if (!active || !payload || payload.length === 0) return null

  const first = payload[0]
  const label = first?.payload && 'label' in first.payload ? String(first.payload.label) : ''

  return (
    <div className="rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur">
      <p className="mb-2 text-sm font-semibold text-slate-900">{label}</p>
      {payload.map((entry) => {
        const name = String(entry.name ?? '')
        const value = typeof entry.value === 'number' ? entry.value : Number(entry.value ?? 0)
        const shown = name.includes('配速') ? formatPace(value) : value

        return (
          <p key={`${name}-${entry.dataKey}`} style={{ color: entry.color }} className="text-sm">
            {name}: {shown}
          </p>
        )
      })}
    </div>
  )
}

export function ChartView({ data }: ChartViewProps) {
  const chartData: ChartDataPoint[] = data.labels.map((label, index) => ({
    label,
    pace: data.paces[index] || 0,
    heartRate: data.heart_rates[index] || 0,
    cadence: data.cadences[index] || 0,
  }))

  return (
    <div className="space-y-8">
      <div>
        <h3 className="mb-1 text-lg font-bold text-slate-900">配速与心率趋势</h3>
        <p className="mb-4 text-sm text-slate-500">观察后半程配速和心率漂移，判断耐力稳定性</p>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 8, right: 24, left: 12, bottom: 8 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" />
            <XAxis dataKey="label" stroke="#64748b" style={{ fontSize: '12px' }} />
            <YAxis
              yAxisId="left"
              stroke="#64748b"
              label={{ value: '配速 (秒/km)', angle: -90, position: 'insideLeft', style: { fontSize: '12px' } }}
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#64748b"
              label={{ value: '心率 (bpm)', angle: 90, position: 'insideRight', style: { fontSize: '12px' } }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<SportTooltip />} />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="pace"
              stroke="#ea580c"
              name="配速 (秒/km)"
              strokeWidth={3}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="heartRate"
              stroke="#0f172a"
              name="心率 (bpm)"
              strokeWidth={2.2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3 className="mb-1 text-lg font-bold text-slate-900">步频趋势</h3>
        <p className="mb-4 text-sm text-slate-500">步频稳定通常意味着跑姿效率更高</p>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData} margin={{ top: 8, right: 24, left: 12, bottom: 8 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" />
            <XAxis dataKey="label" stroke="#64748b" style={{ fontSize: '12px' }} />
            <YAxis
              stroke="#64748b"
              label={{ value: '步频 (步/分)', angle: -90, position: 'insideLeft', style: { fontSize: '12px' } }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<SportTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="cadence"
              stroke="#f59e0b"
              name="步频 (步/分)"
              strokeWidth={2.6}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
