import { ArrowDown, ArrowRight, ArrowUp, Expand } from 'lucide-react'
import { EvidenceLabel } from './EvidenceLabel'
import { HistoricalRangeBar } from './charts/HistoricalRangeBar'
import { IndicatorSparkline } from './charts/IndicatorSparkline'
import type { IndicatorDataset } from './charts/chartTypes'

const format = (value: number | null) => value === null ? 'n/a' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)

export function CurrentStateIndicatorCard({ indicator, onExpand }: { indicator: IndicatorDataset; onExpand: () => void }) {
  const change = indicator.latest.threeMonthChange
  const Arrow = change === null || Math.abs(change) < 1e-12 ? ArrowRight : change > 0 ? ArrowUp : ArrowDown
  const monthsOld = Math.max(0, Math.round((Date.now() - new Date(`${indicator.latest.date}T00:00:00Z`).getTime()) / 2_629_800_000))
  const freshness = monthsOld <= 2 ? 'Current' : monthsOld <= 6 ? `${monthsOld} months old` : `Delayed: ${monthsOld} months old`
  return <article className="cursor-pointer border border-stone-200 bg-white p-5 transition hover:border-petroleum/60 dark:border-stone-800 dark:bg-[#18201d]" onClick={onExpand} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onExpand() }} role="button" tabIndex={0} aria-label={`Open full history for ${indicator.label}`}>
    <div className="flex items-start justify-between gap-3"><div><h3 className="font-semibold text-ink dark:text-white">{indicator.label}</h3><p className="mt-1 text-xs text-stone-500">{indicator.latest.date.slice(0, 7)} · {indicator.frequency} · {freshness}</p></div><EvidenceLabel label={indicator.evidenceLabel} /></div>
    <div className="mt-5 flex items-end justify-between gap-4"><div><p className="text-2xl font-semibold">{format(indicator.latest.value)}</p><p className="mt-1 text-xs text-stone-500">{indicator.unit}</p></div><div className="text-right"><p className="inline-flex items-center gap-1 text-sm font-semibold"><Arrow size={15} />{format(change)} over 3 months</p><p className="mt-1 text-xs text-stone-500">{indicator.latest.momentum}</p></div></div>
    <div className="mt-3"><IndicatorSparkline indicator={indicator} years={10} /></div>
    <div className="mt-3"><HistoricalRangeBar indicator={indicator} /></div>
    <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-stone-500"><span>{indicator.latest.historicalPercentile?.toFixed(0) ?? 'n/a'}th full-history percentile</span><span>{indicator.latest.percentileSince2000?.toFixed(0) ?? 'n/a'}th since 2000</span><span>{format(indicator.latest.distanceFromMedian)} from median</span></div>
    <div className="mt-4 flex items-center justify-between gap-3"><span className="border-l-2 border-signal pl-3 text-sm font-semibold">{indicator.interpretationLabel}</span><button type="button" onClick={(event) => { event.stopPropagation(); onExpand() }} className="flex h-9 items-center gap-2 border border-stone-300 px-3 text-xs font-semibold dark:border-stone-700" aria-label={`Open full history for ${indicator.label}`}><Expand size={14} />History</button></div>
  </article>
}
