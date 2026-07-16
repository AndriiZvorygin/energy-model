import { useEffect, useMemo, useState } from 'react'
import { CurrentStateIndicatorCard } from '../components/CurrentStateIndicatorCard'
import { ChartModal } from '../components/charts/ChartModal'
import { IndicatorHistoryChart } from '../components/charts/IndicatorHistoryChart'
import { LayerHistoryChart } from '../components/charts/LayerHistoryChart'
import type { GeneratedManifest, IndicatorDataset } from '../components/charts/chartTypes'
import { useGeneratedManifest, useIndicatorDatasets } from '../components/charts/useChartData'
import { PageBody, PageHeader } from '../components/PageHeader'

const formatMonth = (date: string) => new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T00:00:00Z`))
const formatSnapshotDate = (date: string) => new Intl.DateTimeFormat('en-US', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(date))

function EvidenceGroup({ title, tone, entries, onSelect }: {
  title: string
  tone: 'supportive' | 'stressful' | 'other'
  entries: GeneratedManifest['currentState']['groups']['supportive']
  onSelect: (id: string) => void
}) {
  const border = tone === 'supportive' ? 'border-emerald-600' : tone === 'stressful' ? 'border-rose-600' : 'border-stone-400 dark:border-stone-600'
  return <div className={`border-t-2 ${border} pt-3`}><h3 className="text-sm font-semibold">{title} <span className="text-stone-500">({entries.length})</span></h3><ul className="mt-3 space-y-3">{entries.map((entry) => <li key={entry.id} className="text-sm"><button type="button" onClick={() => onSelect(entry.id)} className="text-left font-medium underline decoration-stone-300 underline-offset-2 hover:text-petroleum dark:decoration-stone-700">{entry.label}</button><p className="mt-0.5 text-xs text-stone-500">{entry.interpretationLabel} · historical percentile {entry.historicalPercentile?.toFixed(0) ?? 'n/a'} · {formatMonth(entry.latestDate)}</p></li>)}</ul></div>
}

export function CurrentState() {
  const { manifest, error: manifestError } = useGeneratedManifest()
  const files = useMemo(() => manifest?.indicators.map((item) => item.file) ?? [], [manifest])
  const { indicators, error } = useIndicatorDatasets(files)
  const [selected, setSelected] = useState<IndicatorDataset | null>(null)
  const fieldLookup = useMemo(() => new Map(indicators.map((item) => [item.field, item])), [indicators])
  const idLookup = useMemo(() => new Map(indicators.map((item) => [item.id, item])), [indicators])
  useEffect(() => {
    if (!indicators.length || selected) return
    const requested = new URLSearchParams(window.location.search).get('indicator')
    if (requested) setSelected(indicators.find((item) => item.id === requested) ?? null)
  }, [indicators, selected])
  const selectIndicator = (indicator: IndicatorDataset | null) => {
    setSelected(indicator)
    const query = indicator ? `?indicator=${encodeURIComponent(indicator.id)}` : ''
    window.history.replaceState(null, '', `${window.location.pathname}${query}`)
  }
  const selectById = (id: string) => selectIndicator(idLookup.get(id) ?? null)
  const schemaError = manifest && !manifest.currentState ? 'The generated current-state manifest is out of date. Reload the page to request the latest research snapshot.' : null
  if (manifestError || error || schemaError) return <><PageHeader eyebrow="Latest observations" title="Current state by evidence layer" description="Historical indicator data could not be loaded." /><PageBody><p className="text-sm text-amber-700">{manifestError ?? error ?? schemaError}</p></PageBody></>
  return <><PageHeader eyebrow="Latest observations" title="Current state in historical context" description="Every reading is placed against its own history, source date, frequency, confirming evidence, and conflicts. There is no aggregate red or green verdict." /><PageBody>
    {!manifest || !indicators.length ? <div className="flex h-64 items-center justify-center text-sm text-stone-500">Loading indicator histories…</div> : <>
      <section className="border-y border-stone-300 py-6 dark:border-stone-700"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-petroleum">System-state summary</p><h2 className="mt-2 text-2xl font-semibold">Evidence remains mixed across the transmission chain</h2></div><div className="border-l-2 border-petroleum pl-3 text-xs leading-5 text-stone-500"><p><strong className="text-ink dark:text-white">Snapshot generated:</strong> {formatSnapshotDate(manifest.currentState.asOf)} UTC</p><p><strong className="text-ink dark:text-white">Observation vintages:</strong> {formatMonth(manifest.currentState.oldestLatestObservationDate)} to {formatMonth(manifest.currentState.latestObservationDate)}</p></div></div><p className="mt-3 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{manifest.currentState.groups.supportive.length} indicators are currently supportive under their documented direction metadata, {manifest.currentState.groups.stressful.length} show stressful evidence, and {manifest.currentState.groups.other.length} remain neutral, mixed, historically unusual, or context-dependent. This count is descriptive: direction metadata and layer evidence matter more than a mechanical total.</p><div className="mt-4 max-w-5xl text-xs leading-5 text-stone-500"><p>{manifest.currentState.classificationMethod}</p><p>{manifest.currentState.anomalyMethod} Every evidence list and diagnostic layer below is ordered from most anomalous to least anomalous.</p></div><div className="mt-6 grid gap-6 xl:grid-cols-3"><EvidenceGroup title="Supportive evidence" tone="supportive" entries={manifest.currentState.groups.supportive} onSelect={selectById} /><EvidenceGroup title="Stressful evidence" tone="stressful" entries={manifest.currentState.groups.stressful} onSelect={selectById} /><EvidenceGroup title="Other or context-dependent evidence" tone="other" entries={manifest.currentState.groups.other} onSelect={selectById} /></div></section>
      <div className="mt-12 space-y-16">{manifest.layers.map((layer) => {
        const rows = layer.indicatorFields.map((field) => fieldLookup.get(field)).filter((item): item is IndicatorDataset => Boolean(item))
        const supporting = rows.filter((row) => row.interpretationLabel === 'Supportive')
        const stressful = rows.filter((row) => row.interpretationLabel === 'Stressful')
        return <section key={layer.id}><div className="grid gap-4 border-b border-stone-300 pb-5 md:grid-cols-[1fr_260px] dark:border-stone-700"><div><p className="text-xs font-semibold uppercase text-petroleum">Diagnostic layer</p><h2 className="mt-1 text-2xl font-semibold">{layer.label}</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">{layer.interpretation}</p></div><div className="text-sm"><p><strong>Supporting:</strong> {supporting.map((item) => item.label).join(', ') || 'No clear signal'}</p><p className="mt-2"><strong>Stressful:</strong> {stressful.map((item) => item.label).join(', ') || 'No clear signal'}</p><p className="mt-2 text-xs uppercase text-stone-500">Confidence: {layer.confidence}</p></div></div>
          <div className="mt-6"><LayerHistoryChart indicators={rows} /></div>
          <div className="mt-6 grid gap-4 xl:grid-cols-2">{rows.map((indicator) => <CurrentStateIndicatorCard key={indicator.id} indicator={indicator} onExpand={() => selectIndicator(indicator)} />)}</div>
        </section>
      })}</div>
    </>}
    <ChartModal open={Boolean(selected)} title={selected?.label ?? 'Indicator history'} onClose={() => selectIndicator(null)}>{selected && <IndicatorHistoryChart indicator={selected} onSelectIndicator={selectById} />}</ChartModal>
  </PageBody></>
}
