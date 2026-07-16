import type { IndicatorDataset } from './chartTypes'

export function ChartTable({ indicator, rows }: { indicator: IndicatorDataset; rows: IndicatorDataset['observations'] }) {
  return <details className="border-t border-stone-200 pt-4 dark:border-stone-800"><summary className="cursor-pointer text-sm font-semibold">Accessible data table</summary><div className="mt-4 max-h-96 overflow-auto"><table className="min-w-full text-left text-xs"><thead className="sticky top-0 bg-white dark:bg-[#18201d]"><tr><th className="p-2">Date</th><th className="p-2">{indicator.label}<span className="block font-normal text-stone-500">{indicator.unit}</span></th></tr></thead><tbody>{rows.map((row) => <tr key={row.date} className="border-t border-stone-200 dark:border-stone-800"><th className="p-2 font-medium">{row.date}</th><td className="p-2">{row.value === null ? 'Not available' : row.value.toLocaleString('en-US', { maximumFractionDigits: 3 })}</td></tr>)}</tbody></table></div></details>
}
