import { useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import { EvidenceLabel } from '../components/EvidenceLabel'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'

export function Indicators() {
  const [query, setQuery] = useState('')
  const [layer, setLayer] = useState('All layers')
  const layers = ['All layers', ...new Set(researchData.systemResponse.indicatorCatalogue.map((row) => row.layer))]
  const rows = useMemo(() => researchData.systemResponse.indicatorCatalogue.filter((row) => {
    const text = `${row.indicator} ${row.exact_definition} ${row.source} ${row.alternative_explanations}`.toLowerCase()
    return (layer === 'All layers' || row.layer === layer) && text.includes(query.toLowerCase())
  }), [layer, query])
  return <><PageHeader eyebrow="Variable reference" title="Indicator catalogue" description="Definitions, provenance, revisions, expected stress direction, likely lag, alternatives, limitations, and evidence status for every implemented or proposed variable." /><PageBody>
    <div className="grid gap-3 border-y border-stone-200 py-5 sm:grid-cols-[1fr_280px] dark:border-stone-800"><label className="relative"><Search className="absolute left-3 top-3 text-stone-400" size={17} /><span className="sr-only">Search indicators</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search definitions or sources" className="h-11 w-full border border-stone-300 bg-white pl-10 pr-3 text-sm outline-none focus:border-petroleum dark:border-stone-700 dark:bg-[#18201d]" /></label><label><span className="sr-only">Filter by layer</span><select value={layer} onChange={(event) => setLayer(event.target.value)} className="h-11 w-full border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]">{layers.map((item) => <option key={item}>{item}</option>)}</select></label></div>
    <p className="mt-4 text-sm text-stone-500">{rows.length} indicators</p>
    <div className="mt-4 divide-y divide-stone-200 border-y border-stone-200 dark:divide-stone-800 dark:border-stone-800">{rows.map((row) => <article key={row.indicator_id} className="py-6"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-petroleum">{row.layer}</p><h2 className="mt-1 text-lg font-semibold">{row.indicator}</h2><p className="mt-1 text-sm text-stone-500">{row.unit} · {row.frequency} · {row.geography}</p></div><EvidenceLabel label={row.evidence_label} /></div><p className="mt-4 max-w-4xl leading-7 text-stone-700 dark:text-stone-300">{row.exact_definition}</p><dl className="mt-5 grid gap-4 text-sm md:grid-cols-2 xl:grid-cols-4"><div><dt className="font-semibold">Source and coverage</dt><dd className="mt-1 text-stone-500">{row.source}<br />{row.date_coverage}</dd></div><div><dt className="font-semibold">Stress direction and lag</dt><dd className="mt-1 text-stone-500">{row.expected_direction_during_energy_stress}; {row.likely_lag}</dd></div><div><dt className="font-semibold">Alternative explanations</dt><dd className="mt-1 text-stone-500">{row.alternative_explanations}</dd></div><div><dt className="font-semibold">Limitations and revisions</dt><dd className="mt-1 text-stone-500">{row.data_quality_limitations} {row.revisions}</dd></div></dl></article>)}</div>
  </PageBody></>
}
