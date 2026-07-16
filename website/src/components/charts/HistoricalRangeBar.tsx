import type { IndicatorDataset } from './chartTypes'

const format = (value: number | null) => value === null ? 'n/a' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)

export function HistoricalRangeBar({ indicator }: { indicator: IndicatorDataset }) {
  const range = indicator.referenceRanges
  const span = (range.maximum ?? 0) - (range.minimum ?? 0)
  const position = (value: number | null) => value === null || !span ? 50 : Math.max(0, Math.min(100, 100 * (value - Number(range.minimum)) / span))
  return <div aria-label={`Historical range for ${indicator.label}`}>
    <div className="relative h-7" role="img" aria-label={`Current value is at the ${indicator.latest.historicalPercentile?.toFixed(0) ?? 'unknown'}th historical percentile`}>
      <div className="absolute inset-x-0 top-3 h-1" style={{ background: 'var(--chart-brush)' }} />
      <div className="absolute top-2 h-3 opacity-30" style={{ left: `${position(range.p25)}%`, width: `${Math.max(0, position(range.p75) - position(range.p25))}%`, background: 'var(--chart-1)' }} />
      {[range.p10, range.p25, range.historicalMedian, range.p75, range.p90].map((value, index) => <span key={index} className="absolute top-1 h-5 w-px" style={{ left: `${position(value)}%`, background: 'var(--chart-axis)' }} />)}
      <span className="absolute top-0 h-7 w-1" style={{ left: `calc(${position(indicator.latest.value)}% - 2px)`, background: 'var(--chart-3)' }} />
    </div>
    <div className="flex justify-between text-[10px] text-stone-500"><span>Min {format(range.minimum)}</span><span>Median {format(range.historicalMedian)}</span><span>Max {format(range.maximum)}</span></div>
  </div>
}
