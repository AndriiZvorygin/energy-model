import { useEffect, useMemo, useState } from 'react'
import { CurrentStateIndicatorCard } from '../components/CurrentStateIndicatorCard'
import { ChartModal } from '../components/charts/ChartModal'
import { IndicatorHistoryChart } from '../components/charts/IndicatorHistoryChart'
import { LayerHistoryChart } from '../components/charts/LayerHistoryChart'
import type { IndicatorDataset } from '../components/charts/chartTypes'
import { useGeneratedManifest, useIndicatorDatasets } from '../components/charts/useChartData'
import { PageBody, PageHeader } from '../components/PageHeader'

const signalGroups = (rows: IndicatorDataset[]) => ({
  supporting: rows.filter((row) => row.interpretationLabel === 'Supportive'),
  conflicting: rows.filter((row) => row.interpretationLabel === 'Stressful'),
  mixed: rows.filter((row) => !['Supportive', 'Stressful'].includes(row.interpretationLabel)),
})

export function CurrentState() {
  const { manifest, error: manifestError } = useGeneratedManifest()
  const files = useMemo(() => manifest?.indicators.map((item) => item.file) ?? [], [manifest])
  const { indicators, error } = useIndicatorDatasets(files)
  const [selected, setSelected] = useState<IndicatorDataset | null>(null)
  const fieldLookup = useMemo(() => new Map(indicators.map((item) => [item.field, item])), [indicators])
  const overall = signalGroups(indicators)
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
  if (manifestError || error) return <><PageHeader eyebrow="Latest observations" title="Current state by evidence layer" description="Historical indicator data could not be loaded." /><PageBody><p className="text-sm text-amber-700">{manifestError ?? error}</p></PageBody></>
  return <><PageHeader eyebrow="Latest observations" title="Current state in historical context" description="Every reading is placed against its own history, source date, frequency, confirming evidence, and conflicts. There is no aggregate red or green verdict." /><PageBody>
    {!manifest || !indicators.length ? <div className="flex h-64 items-center justify-center text-sm text-stone-500">Loading indicator histories…</div> : <>
      <section className="border-y border-stone-300 py-6 dark:border-stone-700"><p className="text-xs font-semibold uppercase text-petroleum">System-state summary</p><h2 className="mt-2 text-2xl font-semibold">Evidence remains mixed across the transmission chain</h2><p className="mt-3 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{overall.supporting.length} indicators are currently supportive under their documented direction metadata, {overall.conflicting.length} show stressful evidence, and {overall.mixed.length} remain neutral, mixed, historically unusual, or context-dependent. This count is descriptive: direction metadata and layer evidence matter more than a mechanical total.</p></section>
      <div className="mt-12 space-y-16">{manifest.layers.map((layer) => {
        const rows = layer.indicatorFields.map((field) => fieldLookup.get(field)).filter((item): item is IndicatorDataset => Boolean(item))
        const signals = signalGroups(rows)
        return <section key={layer.id}><div className="grid gap-4 border-b border-stone-300 pb-5 md:grid-cols-[1fr_260px] dark:border-stone-700"><div><p className="text-xs font-semibold uppercase text-petroleum">Diagnostic layer</p><h2 className="mt-1 text-2xl font-semibold">{layer.label}</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">{layer.interpretation}</p></div><div className="text-sm"><p><strong>Supporting:</strong> {signals.supporting.map((item) => item.label).join(', ') || 'No clear signal'}</p><p className="mt-2"><strong>Conflicting:</strong> {signals.conflicting.map((item) => item.label).join(', ') || 'No clear signal'}</p><p className="mt-2 text-xs uppercase text-stone-500">Confidence: {layer.confidence}</p></div></div>
          <div className="mt-6"><LayerHistoryChart indicators={rows} /></div>
          <div className="mt-6 grid gap-4 xl:grid-cols-2">{rows.map((indicator) => <CurrentStateIndicatorCard key={indicator.id} indicator={indicator} onExpand={() => selectIndicator(indicator)} />)}</div>
        </section>
      })}</div>
    </>}
    <ChartModal open={Boolean(selected)} title={selected?.label ?? 'Indicator history'} onClose={() => selectIndicator(null)}>{selected && <IndicatorHistoryChart indicator={selected} />}</ChartModal>
  </PageBody></>
}
