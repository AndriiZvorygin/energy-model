import { useMemo, useState } from 'react'
import { Brush, CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartControls } from './ChartControls'
import { ChartDetails, type ChartDetailsData } from './ChartDetails'
import { ChartTable } from './ChartTable'
import { EventAnnotations } from './EventAnnotations'
import { IndicatorEpisodeComparison } from './IndicatorEpisodeComparison'
import { RecessionOverlay } from './RecessionOverlay'
import type { IndicatorDataset } from './chartTypes'
import { useChartContext } from './useChartData'

const format = (value: number | null) => value === null ? 'Not available' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value)

export function IndicatorHistoryChart({ indicator }: { indicator: IndicatorDataset }) {
  const [range, setRange] = useState('all')
  const [lockedDate, setLockedDate] = useState<string | null>(null)
  const [showRecessions, setShowRecessions] = useState(true)
  const [showEvents, setShowEvents] = useState(true)
  const { events, recessions } = useChartContext()
  const rows = useMemo(() => {
    if (range === 'all') return indicator.observations
    const years = Number(range.replace('y', ''))
    const cutoff = new Date(`${indicator.latest.date}T00:00:00Z`)
    cutoff.setUTCFullYear(cutoff.getUTCFullYear() - years)
    return indicator.observations.filter((row) => row.date >= cutoff.toISOString().slice(0, 10))
  }, [indicator, range])
  const details: ChartDetailsData = {
    plainLanguageSummary: indicator.interpretation,
    description: indicator.description,
    howToRead: `Compare the latest ${indicator.unit} observation with the median, middle 50% range, recessions, and historical events. The direction is ${indicator.interpretationDirection.replaceAll('-', ' ')}.`,
    calculation: indicator.calculation,
    patternsToWatch: [`Current percentile: ${indicator.latest.historicalPercentile?.toFixed(1) ?? 'not available'}`, `Momentum is ${indicator.latest.momentum}; confirm with ${indicator.confirmingIndicators.join(', ') || 'other indicators in the same layer'}.`],
    limitations: indicator.limitations,
    sourceNotes: [`${indicator.source}. Latest observation: ${indicator.latest.date}.`],
    transformation: { type: 'raw', referenceStart: indicator.startDate, referenceEnd: indicator.endDate, mean: null, standardDeviation: null },
  }
  const downloadCsv = () => {
    const csv = ['date,value,unit', ...indicator.observations.map((row) => `${row.date},${row.value ?? ''},"${indicator.unit.replaceAll('"', '""')}"`)].join('\n')
    const href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    const link = document.createElement('a'); link.href = href; link.download = `${indicator.id}.csv`; link.click(); URL.revokeObjectURL(href)
  }
  const activeEvents = events.filter((event) => event.start <= indicator.endDate && event.end >= indicator.startDate)
  return <section aria-label={`Full history of ${indicator.label}`}>
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-petroleum">{indicator.interpretationLabel}</p><p className="mt-1 text-sm text-stone-500">{indicator.latest.date.slice(0, 7)} · {indicator.frequency} · {indicator.source}</p></div><button type="button" onClick={downloadCsv} className="border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700">Download CSV</button></div>
    <ChartDetails dataset={details} />
    <div className="mt-5 flex flex-wrap items-center justify-between gap-4"><ChartControls range={range} onRange={setRange} onReset={() => { setRange('all'); setLockedDate(null) }} /><div className="flex gap-4 text-xs"><label className="flex items-center gap-2"><input type="checkbox" checked={showRecessions} onChange={(event) => setShowRecessions(event.target.checked)} />Recessions</label><label className="flex items-center gap-2"><input type="checkbox" checked={showEvents} onChange={(event) => setShowEvents(event.target.checked)} />Events</label></div></div>
    <div className="mt-5 h-[390px] w-full" tabIndex={0} aria-label={`${indicator.label} interactive historical line chart`}>
      <ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{ top: 10, right: 14, left: 8, bottom: 8 }} onClick={(next: unknown) => { const point = next as { activeLabel?: string }; if (point.activeLabel) setLockedDate(point.activeLabel) }}>
        <CartesianGrid opacity={0.58} /><XAxis dataKey="date" minTickGap={40} tickFormatter={(date) => String(date).slice(0, 7)} fontSize={11} /><YAxis width={64} fontSize={11} label={{ value: indicator.unit, angle: -90, position: 'insideLeft', fontSize: 10 }} />
        {indicator.referenceRanges.p25 !== null && indicator.referenceRanges.p75 !== null && <ReferenceArea y1={indicator.referenceRanges.p25} y2={indicator.referenceRanges.p75} fill="var(--chart-1)" fillOpacity={0.14} />}
        {indicator.referenceRanges.historicalMedian !== null && <ReferenceLine y={indicator.referenceRanges.historicalMedian} stroke="var(--chart-neutral)" strokeWidth={1.5} strokeDasharray="4 3" label={{ value: 'Historical median', fontSize: 10 }} />}
        <RecessionOverlay recessions={showRecessions ? recessions : []} /><EventAnnotations events={activeEvents} enabled={showEvents} />
        <Tooltip content={({ active, label, payload }) => active && label && payload?.length ? <div className="border border-stone-200 bg-white p-3 text-xs shadow-lg dark:border-stone-700 dark:bg-[#18201d]"><p className="font-semibold">{String(label).slice(0, 7)}</p><p className="mt-2">{format(Number(payload[0].value))} {indicator.unit}</p><p className="mt-1 text-stone-500">Source date: {String(label)} · {indicator.source}</p><p className="mt-1 text-stone-500 sm:hidden">Tap the line to lock this value.</p></div> : null} />
        <Line type="monotone" dataKey="value" name={indicator.label} stroke="var(--chart-1)" strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false} />
        {rows.length > 36 && <Brush dataKey="date" height={23} travellerWidth={9} stroke="var(--chart-1)" />}
      </LineChart></ResponsiveContainer>
    </div>
    {lockedDate && <div className="mt-3 flex items-center justify-between border border-petroleum/30 bg-petroleum/5 p-3 text-sm"><span><strong>{lockedDate.slice(0, 7)}:</strong> {format(rows.find((row) => row.date === lockedDate)?.value ?? null)} {indicator.unit}</span><button type="button" className="text-xs font-semibold" onClick={() => setLockedDate(null)}>Clear</button></div>}
    <div className="mt-5 grid gap-4 text-sm md:grid-cols-2"><div><h3 className="font-semibold">Confirming indicators</h3><p className="mt-1 text-stone-500">{indicator.confirmingIndicators.join(', ') || 'No specific confirming series documented.'}</p></div><div><h3 className="font-semibold">Conflicting evidence to inspect</h3><p className="mt-1 text-stone-500">{indicator.conflictingIndicators.join(', ') || 'Review other indicators in this layer.'}</p></div></div>
    <IndicatorEpisodeComparison indicator={indicator} />
    <div className="mt-6"><ChartTable indicator={indicator} rows={rows} /></div>
  </section>
}
