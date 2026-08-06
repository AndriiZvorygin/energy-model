import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EvidenceLabel } from '../EvidenceLabel'
import { AccessibleChartTable } from './AccessibleChartTable'
import { ChartDetails } from './ChartDetails'
import { ChartDownloadMenu } from './ChartDownloadMenu'
import { SeriesControls } from './SeriesControls'
import type { ChartDataset, ChartObservation, ChartSeries } from './chartTypes'
import { referenceStatistics, transformObservations } from './chartUtils'
import { useChartContext, useChartDataset } from './useChartData'

function formatValue(value: unknown) {
  return typeof value === 'number' ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value) : 'Missing'
}

function PanelTooltip({ active, label, payload, dataset, stats }: { active?: boolean; label?: string; payload?: Array<{ dataKey?: string; name?: string; value?: number; color?: string; payload?: ChartObservation }>; dataset: ChartDataset; stats: ReturnType<typeof referenceStatistics> }) {
  if (!active || !label || !payload?.length) return null
  return <div className="max-w-80 border border-stone-200 bg-white p-3 text-xs shadow-lg dark:border-stone-700 dark:bg-[#18201d]">
    <p className="font-semibold">{label.slice(0, 4)}{dataset.frequency === 'annual' ? '' : `-${label.slice(5, 7)}`}</p>
    {payload.map((item) => {
      const key = String(item.dataKey)
      const stat = stats[key]
      return <div key={key} className="mt-2 border-t border-stone-100 pt-2 first:border-0 first:pt-0 dark:border-stone-700">
        <p className="flex justify-between gap-4"><span style={{ color: item.color }}>{item.name}</span><strong>{formatValue(item.value)} z</strong></p>
        <p>Raw observation: {formatValue(item.payload?.[`__raw_${key}`])}</p>
        <p>Reference mean / standard deviation: {formatValue(stat?.mean)} / {formatValue(stat?.standardDeviation)}</p>
        <p>Fixed reference: {dataset.transformation.referenceStart?.slice(0, 7)} to {dataset.transformation.referenceEnd?.slice(0, 7)}</p>
      </div>
    })}
  </div>
}

export function AlignedResearchPanels({ file }: { file: string }) {
  const { dataset, error } = useChartDataset(file)
  const { events, regimes, recessions } = useChartContext()
  const [visible, setVisible] = useState<Set<string> | null>(null)
  const [focused, setFocused] = useState<string | null>(null)

  const prepared = useMemo(() => {
    if (!dataset) return { rows: [] as ChartObservation[], stats: {}, series: [] as ChartSeries[] }
    const stats = referenceStatistics(dataset.observations, dataset.series, dataset.transformation.referenceStart, dataset.transformation.referenceEnd)
    const rows = transformObservations(dataset.observations, dataset.series, 'zscore', dataset.observations, stats)
    return { rows, stats, series: dataset.series }
  }, [dataset])

  if (error) return <p className="border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">Interactive panels could not be loaded: {error}</p>
  if (!dataset) return <div className="flex h-80 items-center justify-center border border-stone-200 text-sm text-stone-500 dark:border-stone-800">Loading synchronized research panels…</div>

  const activeKeys = visible ?? new Set(prepared.series.filter((item) => item.defaultVisible).map((item) => item.key))
  const activeSeries = prepared.series.filter((item) => activeKeys.has(item.key))
  const panels = [...new Set(prepared.series.map((item) => item.panel ?? 'All measures'))]
  const activeEvents = events.filter((event) => dataset.annotations.includes(event.id))
  const updateSeries = (key: string) => setVisible((current) => {
    const next = new Set(current ?? prepared.series.filter((item) => item.defaultVisible).map((item) => item.key))
    if (next.has(key)) next.delete(key)
    else next.add(key)
    return next
  })
  const displaySeries = activeSeries.map((item) => ({ ...item, unit: 'fixed-reference z-score' }))

  return <section className="border-y border-stone-200 py-6 dark:border-stone-800" aria-label={dataset.title}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><div className="flex flex-wrap items-center gap-2"><h2 className="text-xl font-semibold">{dataset.title}</h2><EvidenceLabel label={dataset.evidenceLabel} /></div><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">{dataset.description}</p></div>
      <ChartDownloadMenu dataset={dataset} displayedRows={prepared.rows} visibleSeries={displaySeries} />
    </div>
    <ChartDetails dataset={dataset} />
    <div className="mt-6"><SeriesControls series={prepared.series} visible={activeKeys} focused={focused} onToggle={updateSeries} onFocus={setFocused} /></div>
    <p className="mt-4 text-xs text-stone-500">Each panel uses a fixed reference-period z-score. Recessions and project regimes are shaded; their overlap with the lines is descriptive, not proof of causation.</p>
    <div className="mt-5 space-y-5">
      {panels.map((panel, panelIndex) => {
        const panelSeries = activeSeries.filter((item) => (item.panel ?? 'All measures') === panel)
        return <section key={panel} aria-label={panel} className="border border-stone-200 p-3 dark:border-stone-800">
          <h3 className="mb-2 text-sm font-semibold">{panel}</h3>
          <div className="h-[250px] w-full" tabIndex={0} aria-label={`${panel} chart. Use the accessible data table for exact values.`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={prepared.rows} margin={{ top: 8, right: 12, left: 4, bottom: panelIndex === panels.length - 1 ? 8 : 0 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.55} />
                <XAxis dataKey="date" minTickGap={36} tickFormatter={(date) => String(date).slice(0, 7)} fontSize={11} hide={panelIndex !== panels.length - 1} />
                <YAxis width={54} fontSize={11} label={{ value: 'z-score', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                <Tooltip content={<PanelTooltip dataset={dataset} stats={prepared.stats} />} />
                {recessions.map((period) => <ReferenceArea key={`recession-${period.id}`} x1={period.start} x2={period.end} fill="var(--chart-neutral)" fillOpacity={0.15} strokeOpacity={0} ifOverflow="hidden" />)}
                {regimes.map((period) => <ReferenceArea key={`regime-${period.id}`} x1={period.start} x2={period.end} fill={period.color} fillOpacity={0.1} strokeOpacity={0} ifOverflow="hidden" />)}
                {activeEvents.map((event) => <ReferenceArea key={`event-${event.id}`} x1={event.start} x2={event.end} fill="var(--chart-3)" fillOpacity={0.06} strokeOpacity={0} ifOverflow="hidden" />)}
                {panelSeries.map((item, index) => <Line key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={item.color ?? `var(--chart-${(index % 4) + 1})`} strokeWidth={focused === item.key ? 3 : 2} strokeOpacity={focused && focused !== item.key ? 0.22 : 1} dot={false} connectNulls={false} />)}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      })}
    </div>
    <div className="mt-5"><AccessibleChartTable rows={prepared.rows} series={displaySeries} /></div>
  </section>
}
