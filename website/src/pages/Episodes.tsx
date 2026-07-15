import { useState } from 'react'
import { ChartViewer } from '../components/ChartViewer'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'

const fields = [
  ['initiating_conditions', 'Initiating conditions'], ['physical_energy_indicators', 'Physical energy'], ['financial_conditions', 'Financial conditions'],
  ['energy_burden', 'Energy burden'], ['inflation_response', 'Inflation'], ['industrial_and_gdp_response', 'Industry and GDP'],
  ['labour_response', 'Labour'], ['household_response', 'Households'], ['oil_price_peak_and_collapse', 'Oil peak and collapse'],
  ['approximate_lag_sequence', 'Lag sequence'], ['alternative_explanations', 'Alternative explanations'],
] as const

export function Episodes() {
  const episodes = researchData.systemResponse.episodes
  const [first, setFirst] = useState<string>(episodes[3]?.episode ?? episodes[0]?.episode)
  const [second, setSecond] = useState<string>(episodes[5]?.episode ?? episodes[1]?.episode)
  const selected = [episodes.find((row) => row.episode === first), episodes.find((row) => row.episode === second)]
  return <><PageHeader eyebrow="Historical analogues" title="Compare energy-stress episodes" description="The same visible sequence can have different initiating causes. Episode comparisons organize evidence; they do not establish a reusable causal template." /><PageBody><div className="grid gap-3 sm:grid-cols-2">{[first, second].map((value, index) => <select key={index} value={value} onChange={(event) => index === 0 ? setFirst(event.target.value) : setSecond(event.target.value)} className="h-11 border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]">{episodes.map((row) => <option key={row.episode}>{row.episode}</option>)}</select>)}</div><div className="mt-8 overflow-x-auto"><table className="min-w-[760px] w-full border-collapse text-left text-sm"><thead><tr className="border-b border-stone-300 dark:border-stone-700"><th className="w-44 py-3 pr-4">Dimension</th>{selected.map((row, index) => <th key={index} className="py-3 pr-6">{row?.episode}</th>)}</tr></thead><tbody>{fields.map(([key, label]) => <tr key={key} className="border-b border-stone-200 align-top dark:border-stone-800"><th className="py-4 pr-4 font-semibold">{label}</th>{selected.map((row, index) => <td key={index} className="py-4 pr-6 leading-6 text-stone-600 dark:text-stone-300">{row?.[key]}</td>)}</tr>)}</tbody></table></div><div className="mt-12"><ChartViewer src="/charts/historical_episode_comparison.png" alt="Comparison of oil prices industrial production and unemployment across historical episodes" title="Historical episode comparison" description="Normalized paths expose common sequencing and important differences around episode starts." source="WTI, FRED industrial production, unemployment and project episode windows." /></div></PageBody></>
}
