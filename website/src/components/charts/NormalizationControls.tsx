import type { Transformation } from './chartTypes'

const labels: Record<Transformation, string> = { raw: 'Raw', yoy: 'YoY', indexed: 'Index 100', zscore: 'Z-score', pct_change: '% change' }

export function NormalizationControls({ available, selected, onChange }: { available: Transformation[]; selected: Transformation; onChange: (value: Transformation) => void }) {
  return <fieldset><legend className="mb-2 text-xs font-semibold uppercase text-stone-500">View</legend><div className="inline-flex flex-wrap border border-stone-300 dark:border-stone-700">{available.map((item) => <button key={item} type="button" onClick={() => onChange(item)} className={`px-3 py-2 text-xs font-semibold ${selected === item ? 'bg-petroleum text-white' : ''}`}>{labels[item]}</button>)}</div></fieldset>
}
