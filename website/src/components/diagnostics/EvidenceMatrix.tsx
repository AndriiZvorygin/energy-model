import { Check, ChevronDown, CircleHelp, Expand, Minus, X } from 'lucide-react'
import { Fragment, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChartModal } from '../charts/ChartModal'
import { HistoricalRangeBar } from '../charts/HistoricalRangeBar'
import { IndicatorHistoryChart } from '../charts/IndicatorHistoryChart'
import { IndicatorSparkline } from '../charts/IndicatorSparkline'
import type { IndicatorDataset } from '../charts/chartTypes'

export type EvidenceDisposition = 'supports' | 'mixed' | 'contradicts' | 'insufficient'
export type AbsoluteAffordabilityStatus = 'affordable' | 'pressured' | 'unaffordable' | 'severe-shortfall' | 'insufficient'
export type AffordabilityDirection = 'worsening' | 'stable' | 'easing' | 'unclear'

export type EvidenceMatrixRow = {
  id: string
  label: string
  disposition: EvidenceDisposition
  status: string
  reason: string
  indicator?: IndicatorDataset
  value?: number | null
  unit?: string | null
  percentile?: number | null
  direction?: string | null
  absoluteStatus?: AbsoluteAffordabilityStatus | null
  source?: string | null
  sourceDate?: string | null
  calculation?: string | null
  limitations?: string[]
  evidenceGeography?: string | null
  evidenceRoute?: string | null
}

const labels: Record<EvidenceDisposition, string> = {
  supports: 'Supports', mixed: 'Mixed or unclear', contradicts: 'Contradicts', insufficient: 'Insufficient data',
}
const symbols: Record<EvidenceDisposition, string> = { supports: '✓', mixed: '~', contradicts: '✕', insufficient: '?' }
const tones: Record<EvidenceDisposition, string> = {
  supports: 'text-emerald-700 dark:text-emerald-300', mixed: 'text-amber-700 dark:text-amber-300',
  contradicts: 'text-rose-700 dark:text-rose-300', insufficient: 'text-stone-500',
}
const order: EvidenceDisposition[] = ['supports', 'mixed', 'contradicts', 'insufficient']
const format = (value: number | null | undefined) => value == null ? 'Unavailable' : new Intl.NumberFormat('en-CA', { maximumFractionDigits: 2 }).format(value)

function Symbol({ disposition }: { disposition: EvidenceDisposition }) {
  const Icon = disposition === 'supports' ? Check : disposition === 'mixed' ? Minus : disposition === 'contradicts' ? X : CircleHelp
  return <span className={`inline-flex items-center justify-center ${tones[disposition]}`}><Icon size={18} strokeWidth={2.6} aria-hidden="true" /><span className="sr-only">{labels[disposition]}</span></span>
}

export function EvidenceMatrix({ interpretation, confidence, coverage, rows, title = 'Diagnostic summary', absoluteStatus, direction }: {
  interpretation: string
  confidence: string
  coverage: number | null
  rows: EvidenceMatrixRow[]
  title?: string
  absoluteStatus?: AbsoluteAffordabilityStatus | null
  direction?: AffordabilityDirection | null
}) {
  const [filter, setFilter] = useState<EvidenceDisposition | 'all'>('all')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [history, setHistory] = useState<IndicatorDataset | null>(null)
  const counts = useMemo(() => Object.fromEntries(order.map((key) => [key, rows.filter((row) => row.disposition === key).length])) as Record<EvidenceDisposition, number>, [rows])
  const visible = filter === 'all' ? rows : rows.filter((row) => row.disposition === filter)
  return <section className="border-y border-stone-300 py-6 dark:border-stone-700" aria-label={title}>
    <div className="grid gap-5 lg:grid-cols-[1fr_auto]"><div><p className="text-xs font-semibold uppercase text-petroleum">{title}</p><h2 className="mt-2 text-2xl font-semibold">{interpretation}</h2>{absoluteStatus && direction && <p className="mt-2 text-sm text-stone-600 dark:text-stone-300"><span className="font-semibold capitalize">Absolute status: {absoluteStatus.replace('-', ' ')}</span><span aria-hidden="true"> · </span><span className="capitalize">Direction: {direction}</span></p>}</div><dl className="grid grid-cols-2 gap-x-7 gap-y-2 text-sm lg:min-w-64"><div><dt className="text-stone-500">Confidence</dt><dd className="font-semibold capitalize">{confidence}</dd></div><div><dt className="text-stone-500">Evidence coverage</dt><dd className="font-semibold">{coverage == null ? 'Not published' : `${(coverage * 100).toFixed(0)}%`}</dd></div></dl></div>
    <div className="mt-6"><p className="text-xs font-semibold uppercase text-stone-500">Evidence balance</p><div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => setFilter('all')} aria-pressed={filter === 'all'} className={`border px-3 py-2 text-xs font-semibold ${filter === 'all' ? 'border-petroleum bg-petroleum/10' : 'border-stone-300 dark:border-stone-700'}`}>All {rows.length}</button>{order.map((key) => <button key={key} type="button" onClick={() => setFilter(key)} aria-pressed={filter === key} className={`inline-flex items-center gap-2 border px-3 py-2 text-xs font-semibold ${filter === key ? 'border-petroleum bg-petroleum/10' : 'border-stone-300 dark:border-stone-700'}`}><Symbol disposition={key} />{labels[key]} {counts[key]}</button>)}</div></div>
    <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[720px] border-collapse text-left text-sm"><thead><tr className="border-b border-stone-300 text-xs uppercase text-stone-500 dark:border-stone-700"><th className="py-3 pr-4">Evidence</th><th className="w-20 text-center">Supports</th><th className="w-20 text-center">Mixed</th><th className="w-24 text-center">Contradicts</th><th className="w-48">Status</th></tr></thead><tbody>{visible.map((row) => {
      const open = expanded === row.id
      const indicator = row.indicator
      const statusText = row.absoluteStatus ? `${row.absoluteStatus.replace('-', ' ')} · ${row.direction ?? 'unclear'}` : row.status
      return <Fragment key={row.id}><tr className="border-b border-stone-200 align-top dark:border-stone-800"><td className="py-3 pr-4"><button type="button" onClick={() => setExpanded(open ? null : row.id)} aria-expanded={open} className="flex w-full items-start justify-between gap-3 text-left font-medium hover:text-petroleum"><span>{row.label}{row.evidenceGeography && <span className="ml-2 text-xs font-normal text-stone-500">{row.evidenceGeography}</span>}</span><ChevronDown size={16} className={`mt-0.5 shrink-0 transition ${open ? 'rotate-180' : ''}`} /></button></td><td className="w-20 py-3 text-center">{row.disposition === 'supports' && <Symbol disposition="supports" />}</td><td className="w-20 py-3 text-center">{row.disposition === 'mixed' && <Symbol disposition="mixed" />}</td><td className="w-24 py-3 text-center">{row.disposition === 'contradicts' && <Symbol disposition="contradicts" />}</td><td className="w-48 py-3 text-xs capitalize text-stone-500"><span className="inline-flex items-center gap-2">{row.disposition === 'insufficient' && <Symbol disposition="insufficient" />}{statusText}</span></td></tr>{open && <tr className="border-b border-stone-200 dark:border-stone-800"><td colSpan={5} className="pb-6 pt-2"><div className="border-l-2 border-petroleum bg-stone-50 p-5 dark:bg-stone-900/50"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className={`text-xs font-semibold uppercase ${tones[row.disposition]}`}><span aria-hidden="true">{symbols[row.disposition]}</span> {labels[row.disposition]}</p><h3 className="mt-2 text-lg font-semibold">Why this evidence is classified here</h3><p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{row.reason}</p>{row.evidenceRoute && row.evidenceGeography && <Link to={row.evidenceRoute} className="mt-3 inline-flex text-xs font-semibold text-petroleum underline underline-offset-4">Open {row.evidenceGeography} geography</Link>}</div>{indicator && <button type="button" onClick={() => setHistory(indicator)} className="inline-flex items-center gap-2 border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700"><Expand size={14} />Full history</button>}</div><dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4"><div><dt className="text-stone-500">Current value</dt><dd className="font-medium">{format(indicator?.latest.value ?? row.value)} {indicator?.unit ?? row.unit ?? ''}</dd></div><div><dt className="text-stone-500">Historical percentile</dt><dd className="font-medium">{format(indicator?.latest.historicalPercentile ?? row.percentile)}</dd></div><div><dt className="text-stone-500">Recent direction</dt><dd className="font-medium capitalize">{indicator?.latest.momentum ?? row.direction ?? 'Unavailable'}</dd></div><div><dt className="text-stone-500">Source date</dt><dd className="font-medium">{indicator?.latest.sourceDate?.slice(0, 10) ?? row.sourceDate?.slice(0, 10) ?? 'Unavailable'}</dd></div></dl>{indicator && <><div className="mt-5"><IndicatorSparkline indicator={indicator} years={10} /></div><div className="mt-3"><HistoricalRangeBar indicator={indicator} /></div></>}<div className="mt-5 grid gap-5 text-xs leading-5 text-stone-500 lg:grid-cols-3"><div><strong className="text-ink dark:text-white">Source</strong><p className="mt-1">{indicator?.source ?? row.source ?? 'Not linked to an indicator history'}</p></div><div><strong className="text-ink dark:text-white">Calculation</strong><p className="mt-1">{indicator?.calculation.formula ?? row.calculation ?? 'Published classifier or symptom evidence'}</p></div><div><strong className="text-ink dark:text-white">Limitations</strong><p className="mt-1">{(indicator?.limitations ?? row.limitations ?? []).join(' ') || 'No additional limitation published for this row.'}</p></div></div></div></td></tr>}</Fragment>
    })}</tbody></table>{visible.length === 0 && <p className="py-8 text-sm text-stone-500">No evidence rows match this filter.</p>}</div>
    <ChartModal open={Boolean(history)} title={history?.label ?? 'Evidence history'} onClose={() => setHistory(null)}>{history && <IndicatorHistoryChart indicator={history} />}</ChartModal>
  </section>
}
