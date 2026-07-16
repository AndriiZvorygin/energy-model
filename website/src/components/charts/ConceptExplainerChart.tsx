import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'

export type ConceptType = 'zscore' | 'yoy' | 'lag' | 'correlation' | 'residual' | 'indexed'

const raw = [82, 85, 84, 89, 92, 94, 91, 96, 101, 99, 104, 108, 112]
const labels = raw.map((_, index) => `M${index + 1}`)

export function ConceptExplainerChart({ concept }: { concept: ConceptType }) {
  const [control, setControl] = useState(concept === 'lag' ? 5 : concept === 'zscore' ? 108 : 0)
  const [correlation, setCorrelation] = useState<'positive' | 'weak' | 'negative'>('positive')
  const data = useMemo(() => raw.map((value, index) => ({ month: labels[index], value, earlier: index === 0 ? null : raw[index - 1], indexed: 100 * value / raw[0] })), [])
  if (concept === 'correlation') {
    const points = Array.from({ length: 12 }, (_, index) => ({ x: index + 1, y: correlation === 'positive' ? index * 1.2 + (index % 3 - 1) : correlation === 'negative' ? 14 - index * 1.1 + (index % 3 - 1) : 6 + ((index * 7) % 5) }))
    return <div className="border border-stone-200 p-4 dark:border-stone-800"><div className="flex flex-wrap gap-2">{(['positive', 'weak', 'negative'] as const).map((item) => <button key={item} type="button" onClick={() => setCorrelation(item)} className={`border px-3 py-2 text-xs font-semibold ${correlation === item ? 'bg-petroleum text-white' : 'dark:border-stone-700'}`}>{item[0].toUpperCase() + item.slice(1)}</button>)}</div><div className="mt-3 h-44"><ResponsiveContainer><ScatterChart><CartesianGrid opacity={0.55} /><XAxis dataKey="x" /><YAxis dataKey="y" /><Tooltip /><Scatter data={points} fill="var(--chart-1)" /></ScatterChart></ResponsiveContainer></div><p className="text-xs leading-5 text-stone-500">Correlation summarizes co-movement. Changing the pattern changes the sign and strength, but none of these plots establishes causation.</p></div>
  }
  if (concept === 'residual') {
    const actual = 34; const implied = 21; const residual = actual - implied
    return <div className="border border-stone-200 p-4 dark:border-stone-800"><div className="grid grid-cols-3 gap-3 text-center"><div><p className="text-xs text-stone-500">Actual oil YoY</p><p className="mt-1 text-xl font-semibold">{actual}%</p></div><div><p className="text-xs text-stone-500">Model-implied</p><p className="mt-1 text-xl font-semibold">{implied}%</p></div><div><p className="text-xs text-stone-500">Residual</p><p className="mt-1 text-xl font-semibold text-signal">{residual} pp</p></div></div><div className="mt-4 h-3 bg-stone-200 dark:bg-stone-700"><div className="h-full bg-petroleum" style={{ width: `${implied / actual * 100}%` }} /></div><p className="mt-3 text-xs text-stone-500">Residual = actual - model-implied = {actual} - {implied} = {residual} percentage points.</p></div>
  }
  const mean = raw.reduce((sum, value) => sum + value, 0) / raw.length
  const std = Math.sqrt(raw.reduce((sum, value) => sum + (value - mean) ** 2, 0) / raw.length)
  const selected = concept === 'zscore' ? control : raw[raw.length - 1]
  const z = (selected - mean) / std
  const lag = concept === 'lag' ? control : 0
  const title = concept === 'zscore' ? `z = (${selected.toFixed(1)} - ${mean.toFixed(1)}) / ${std.toFixed(1)} = ${z.toFixed(2)}` : concept === 'yoy' ? `YoY = 100 × (${raw[12]} / ${raw[0]} - 1) = ${(100 * (raw[12] / raw[0] - 1)).toFixed(1)}%` : concept === 'lag' ? `GM2 month M1 is compared with oil month M${lag + 1}` : 'All series equal 100 at the selected starting observation.'
  return <div className="border border-stone-200 p-4 dark:border-stone-800">
    {(concept === 'zscore' || concept === 'lag') && <label className="block text-xs font-semibold">{concept === 'zscore' ? 'Selected observation' : 'Selected lag'} <input type="range" min={concept === 'zscore' ? 75 : 0} max={concept === 'zscore' ? 120 : 12} value={control} onChange={(event) => setControl(Number(event.target.value))} className="mx-3 align-middle" />{control}{concept === 'lag' ? ' months' : ''}</label>}
    <p className="mt-3 font-mono text-xs">{title}</p>
    <div className="mt-3 h-44"><ResponsiveContainer><LineChart data={data}><CartesianGrid opacity={0.55} /><XAxis dataKey="month" /><YAxis domain={['auto', 'auto']} /><Tooltip />{concept === 'zscore' && <ReferenceLine y={mean} label="Mean" stroke="var(--chart-neutral)" strokeWidth={1.5} strokeDasharray="4 3" />}{concept === 'yoy' && <><ReferenceLine x="M1" stroke="var(--chart-3)" strokeWidth={2} /><ReferenceLine x="M13" stroke="var(--chart-1)" strokeWidth={2} /></>}<Line dataKey={concept === 'indexed' ? 'indexed' : 'value'} stroke="var(--chart-1)" strokeWidth={2.5} dot /></LineChart></ResponsiveContainer></div>
    <p className="text-xs leading-5 text-stone-500">{concept === 'zscore' ? 'Zero is the fixed-reference historical mean; +1 and -1 are one standard deviation above and below it. Changing the visible range does not recalculate the baseline.' : concept === 'yoy' ? 'The current month is compared with the same month one year earlier, using 13 monthly observations including both endpoints.' : concept === 'lag' ? 'Visually moving an earlier GM2 value to a later comparison date does not use future information. It is alignment, not proof of prediction or causation.' : 'Indexing removes incompatible starting levels and compares relative paths; it does not make the underlying units equivalent.'}</p>
  </div>
}
