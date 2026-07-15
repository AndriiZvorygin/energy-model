import type { ChartObservation, ChartSeries } from './chartTypes'

const format = (value: unknown) => typeof value === 'number' ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value) : 'Not available'

export function AccessibleChartTable({ rows, series }: { rows: ChartObservation[]; series: ChartSeries[] }) {
  return <details className="border-t border-stone-200 pt-4 dark:border-stone-800"><summary className="cursor-pointer text-sm font-semibold">Accessible data table</summary><div className="mt-4 max-h-96 overflow-auto"><table className="min-w-full text-left text-xs"><thead className="sticky top-0 bg-white dark:bg-[#18201d]"><tr><th className="p-2">Date</th>{series.map((item) => <th key={item.key} className="p-2">{item.label}<span className="block font-normal text-stone-500">{item.unit}</span></th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.date} className="border-t border-stone-200 dark:border-stone-800"><th className="p-2 font-medium">{row.date}</th>{series.map((item) => <td key={item.key} className="p-2">{format(row[item.key])}</td>)}</tr>)}</tbody></table></div></details>
}
