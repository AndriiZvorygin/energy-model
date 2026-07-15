import { EvidenceLabel } from '../components/EvidenceLabel'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'

const fmt = (value: number | null) => value === null ? 'Not available' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)

export function CurrentState() {
  const grouped = researchData.systemResponse.currentState.reduce<Record<string, typeof researchData.systemResponse.currentState[number][]>>((result, row) => {
    (result[row.layer] ??= []).push(row)
    return result
  }, {})
  return <><PageHeader eyebrow="Latest observations" title="Current state by evidence layer" description="Each reading retains its own date, frequency, interpretation, confirming evidence, conflicts, and confidence. There is no aggregate red or green verdict." /><PageBody>
    <div className="space-y-12">{Object.entries(grouped).map(([layer, rows]) => <section key={layer}><div className="mb-4 flex items-end justify-between gap-4 border-b border-stone-300 pb-3 dark:border-stone-700"><h2 className="text-xl font-semibold">{layer}</h2><span className="text-xs text-stone-500">{rows?.length ?? 0} indicators</span></div><div className="grid gap-4 xl:grid-cols-2">{rows?.map((row) => <article key={row.indicator_id} className="border border-stone-200 bg-white p-5 dark:border-stone-800 dark:bg-[#18201d]"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-ink dark:text-white">{row.indicator}</h3><p className="mt-1 text-xs text-stone-500">Through {row.source_date} · {row.update_frequency}</p></div><EvidenceLabel label={row.evidence_label} /></div><div className="mt-5 grid grid-cols-3 gap-3"><div><p className="text-xs text-stone-500">Latest</p><p className="mt-1 font-semibold">{fmt(row.latest_value)}</p></div><div><p className="text-xs text-stone-500">Change</p><p className="mt-1 font-semibold">{fmt(row.change)}</p></div><div><p className="text-xs text-stone-500">Percentile</p><p className="mt-1 font-semibold">{fmt(row.historical_percentile)}</p></div></div><p className="mt-4 text-sm leading-6 text-stone-600 dark:text-stone-300">{row.interpretation}</p><dl className="mt-4 grid gap-2 text-xs"><div><dt className="font-semibold">Confirm with</dt><dd className="text-stone-500">{row.confirming_indicators}</dd></div><div><dt className="font-semibold">Conflicts</dt><dd className="text-stone-500">{row.conflicting_indicators}</dd></div></dl><p className="mt-4 text-xs font-semibold uppercase text-stone-500">Confidence: {row.confidence_level}</p></article>)}</div></section>)}</div>
  </PageBody></>
}
