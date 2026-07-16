import { Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, YAxis } from 'recharts'
import type { IndicatorDataset } from './chartTypes'

const format = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)

export function IndicatorSparkline({ indicator, years = 10 }: { indicator: IndicatorDataset; years?: number }) {
  const cutoff = new Date(`${indicator.latest.date}T00:00:00Z`)
  cutoff.setUTCFullYear(cutoff.getUTCFullYear() - years)
  const rows = indicator.observations.filter((row) => row.date >= cutoff.toISOString().slice(0, 10))
  const { p25, p75, historicalMedian } = indicator.referenceRanges
  return <div className="h-28 w-full" aria-label={`${years}-year history for ${indicator.label}`}>
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={rows} margin={{ top: 8, right: 4, left: 4, bottom: 4 }}>
        <YAxis hide domain={['auto', 'auto']} />
        {p25 !== null && p75 !== null && <ReferenceArea y1={p25} y2={p75} fill="#0f766e" fillOpacity={0.09} />}
        {historicalMedian !== null && <ReferenceLine y={historicalMedian} stroke="#78716c" strokeDasharray="3 3" />}
        <Tooltip labelFormatter={(date) => String(date).slice(0, 7)} formatter={(value) => [`${format(Number(value))} ${indicator.unit}`, indicator.label]} />
        <Line type="monotone" dataKey="value" stroke="#0f766e" strokeWidth={1.8} dot={false} connectNulls={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  </div>
}
