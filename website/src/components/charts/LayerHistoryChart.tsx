import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { IndicatorDataset } from './chartTypes'
import { chartPalette } from './chartPalette'

export function LayerHistoryChart({ indicators }: { indicators: IndicatorDataset[] }) {
  const [visible, setVisible] = useState(() => indicators.slice(0, 5).map((item) => item.id))
  const rows = useMemo(() => {
    const dates = [...new Set(indicators.flatMap((indicator) => indicator.observations.map((row) => row.date)))].sort()
    const lookups = Object.fromEntries(indicators.map((indicator) => [indicator.id, new Map(indicator.observations.map((row) => [row.date, row.value]))]))
    const stats = Object.fromEntries(indicators.map((indicator) => {
      const values = indicator.observations.filter((row) => row.date >= '2000-01-01' && row.date <= '2019-12-31' && row.value !== null).map((row) => Number(row.value))
      const mean = values.reduce((sum, value) => sum + value, 0) / values.length
      const std = Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length)
      return [indicator.id, { mean, std }]
    }))
    return dates.map((date) => ({ date, ...Object.fromEntries(indicators.map((indicator) => { const raw = lookups[indicator.id].get(date); const stat = stats[indicator.id]; return [indicator.id, raw === null || raw === undefined || !stat.std ? null : (raw - stat.mean) / stat.std] })) }))
  }, [indicators])
  return <div className="border-y border-stone-200 py-5 dark:border-stone-800">
    <div className="flex flex-wrap gap-2">{indicators.map((indicator, index) => <button key={indicator.id} type="button" onClick={() => setVisible((current) => current.includes(indicator.id) ? current.filter((id) => id !== indicator.id) : [...current, indicator.id])} className={`border px-3 py-2 text-xs font-semibold ${visible.includes(indicator.id) ? 'bg-stone-100 dark:bg-stone-800' : 'border-stone-300 opacity-60 dark:border-stone-700'}`} style={visible.includes(indicator.id) ? { color: chartPalette[index % chartPalette.length], borderColor: chartPalette[index % chartPalette.length] } : undefined}>{indicator.label}</button>)}</div>
    <div className="mt-4 h-64"><ResponsiveContainer><LineChart data={rows}><CartesianGrid opacity={0.55} /><XAxis dataKey="date" minTickGap={48} tickFormatter={(date) => String(date).slice(0, 4)} fontSize={11} /><YAxis width={52} label={{ value: 'z-score', angle: -90, position: 'insideLeft', fontSize: 10 }} /><Tooltip labelFormatter={(date) => String(date).slice(0, 7)} formatter={(value, name) => [Number(value).toFixed(2), indicators.find((item) => item.id === name)?.label ?? name]} />{indicators.filter((item) => visible.includes(item.id)).map((indicator) => <Line key={indicator.id} dataKey={indicator.id} stroke={chartPalette[indicators.indexOf(indicator) % chartPalette.length]} strokeWidth={2.2} dot={false} connectNulls={false} isAnimationActive={false} />)}</LineChart></ResponsiveContainer></div>
    <p className="mt-2 text-xs leading-5 text-stone-500">Standardized using each series' fixed January 2000 to December 2019 mean and standard deviation. The visible range does not alter the baseline. Hover for exact z-scores; open an indicator card for raw values, units, and source dates.</p>
  </div>
}
