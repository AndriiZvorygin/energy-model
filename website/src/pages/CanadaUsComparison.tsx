import { useMemo } from 'react'
import { CanadaGeographyControls } from '../components/CanadaGeographyControls'
import { LayerHistoryChart } from '../components/charts/LayerHistoryChart'
import type { GeneratedManifest, IndicatorDataset } from '../components/charts/chartTypes'
import { useGeneratedJson, useGeneratedManifest, useIndicatorDatasets } from '../components/charts/useChartData'
import { PageBody, PageHeader } from '../components/PageHeader'

type CanadaManifest = { indicators: Array<{ id: string; file: string }> }
type Comparison = { note: string; datasets: Array<{ id: string; title: string; canadaLabel: string; unitedStatesLabel: string; definitionDifference: string; canadaPercentile: number | null; sources: string[] }> }
const mappings: Record<string, [string, string]> = { unemployment: ['canada-unemployment-rate', 'unemployment-rate'], 'energy-cpi': ['canada-energy-cpi-yoy', 'energy-cpi-yoy'], 'real-gdp': ['canada-real-gdp-growth', 'real-gdp-growth'], 'policy-rate': ['canada-policy-rate', 'fed-funds-rate'] }

export function CanadaUsComparison() {
  const { data: canadian } = useGeneratedJson<CanadaManifest>('canada/manifest.json')
  const { data: comparison } = useGeneratedJson<Comparison>('canada/canada-us-comparison.json')
  const { manifest: us } = useGeneratedManifest()
  const files = useMemo(() => comparison?.datasets.flatMap((item) => {
    const mapping = mappings[item.id]
    const ca = canadian?.indicators.find((entry) => entry.id === mapping?.[0])
    const usa = us?.indicators.find((entry) => entry.id === mapping?.[1])
    return [ca ? `canada/${ca.file}` : '', usa?.file ?? ''].filter(Boolean)
  }) ?? [], [comparison, canadian, us])
  const { indicators } = useIndicatorDatasets(files)
  const byId = new Map(indicators.map((item) => [item.id, item]))
  return <><PageHeader eyebrow="Country comparison" title="Canada and United States evidence" description="Comparable indicators retain native definitions and separate historical distributions. Similar values need not imply the same economic condition." /><PageBody><CanadaGeographyControls /><p className="mt-8 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{comparison?.note ?? 'Loading comparison metadata…'} Canada and the United States differ in energy production, trade, currencies, housing systems, population growth and industrial structure.</p><div className="mt-10 space-y-14">{comparison?.datasets.map((item) => {
    const mapping = mappings[item.id]
    const rows = mapping?.map((id, index) => {
      const indicator = byId.get(id)
      if (!indicator) return undefined
      return { ...indicator, label: index === 0 ? item.canadaLabel : item.unitedStatesLabel }
    }).filter((entry): entry is IndicatorDataset => Boolean(entry)) ?? []
    return <section key={item.id}><h2 className="text-2xl font-semibold">{item.title}</h2><p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">{item.definitionDifference}</p>{rows.length === 2 ? <><div className="mt-4 flex flex-wrap gap-5 text-sm"><span><strong>Canada:</strong> P{rows[0].latest.historicalPercentile?.toFixed(0) ?? 'n/a'} in its own history</span><span><strong>United States:</strong> P{rows[1].latest.historicalPercentile?.toFixed(0) ?? 'n/a'} in its own history</span></div><div className="mt-5"><LayerHistoryChart indicators={rows} /></div></> : <p className="mt-5 text-sm text-stone-500">Loading both native histories…</p>}<p className="mt-3 text-xs text-stone-500">Each line is standardized against its own fixed history; country percentiles are not pooled. Sources: {item.sources.join('; ')}.</p></section>
  })}</div></PageBody></>
}
