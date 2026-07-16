import { useState } from 'react'
import { CurrentStateIndicatorCard } from '../CurrentStateIndicatorCard'
import { ChartModal } from '../charts/ChartModal'
import { IndicatorHistoryChart } from '../charts/IndicatorHistoryChart'
import type { IndicatorDataset } from '../charts/chartTypes'
import { useIndicatorDatasets } from '../charts/useChartData'

export function AffordabilityIndicatorGrid({ files }: { files: string[] }) {
  const { indicators, error } = useIndicatorDatasets(files)
  const [selected, setSelected] = useState<IndicatorDataset | null>(null)
  if (error) return <p className="mt-5 text-sm text-amber-700">{error}</p>
  if (!indicators.length) return <p className="mt-5 text-sm text-stone-500">Loading indicator histories…</p>
  return <><div className="mt-6 grid gap-4 xl:grid-cols-2">{indicators.map((indicator) => <CurrentStateIndicatorCard key={indicator.id} indicator={indicator} onExpand={() => setSelected(indicator)} showEvidenceContext />)}</div><ChartModal open={Boolean(selected)} title={selected?.label ?? 'Affordability indicator history'} onClose={() => setSelected(null)}>{selected && <IndicatorHistoryChart indicator={selected} />}</ChartModal></>
}
