import type { ChartObservation, ChartSeries } from './chartTypes'

const format = (value: unknown) => typeof value === 'number' ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value) : 'Missing'

export function LatestValuesPanel({ rows, series }: { rows: ChartObservation[]; series: ChartSeries[] }) {
  return <div className="grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 lg:grid-cols-4 dark:border-stone-800 dark:bg-stone-800">{series.map((item) => { const row = [...rows].reverse().find((candidate) => typeof candidate[item.key] === 'number'); return <div key={item.key} className="bg-white p-3 dark:bg-[#18201d]"><p className="text-xs text-stone-500">{item.label}</p><p className="mt-1 font-semibold">{format(row?.[item.key])} <span className="text-xs font-normal text-stone-500">{item.unit}</span></p><p className="mt-1 text-xs text-stone-400">{row?.date ?? 'No observation'}</p></div> })}</div>
}
