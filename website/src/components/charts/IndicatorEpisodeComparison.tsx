import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { IndicatorDataset } from './chartTypes'

const presets = [
  { id: 'gfc', label: '2008', start: '2007-07-01', end: '2009-12-01' },
  { id: 'shale', label: '2014-2016', start: '2014-01-01', end: '2016-12-01' },
  { id: 'covid', label: '2020', start: '2019-07-01', end: '2021-06-01' },
  { id: 'reopening', label: '2021-2022', start: '2021-01-01', end: '2022-12-01' },
]

export function IndicatorEpisodeComparison({ indicator }: { indicator: IndicatorDataset }) {
  const [first, setFirst] = useState('gfc')
  const [second, setSecond] = useState('covid')
  const [mode, setMode] = useState<'indexed' | 'zscore'>('zscore')
  const [customStart, setCustomStart] = useState('2023-01-01')
  const options = [...presets, { id: 'custom', label: 'User-selected', start: customStart, end: indicator.endDate }]
  const data = useMemo(() => {
    const values = indicator.observations.filter((row) => row.value !== null).map((row) => Number(row.value))
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length
    const std = Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length)
    const paths = [first, second].map((id) => {
      const period = options.find((item) => item.id === id)!
      const rows = indicator.observations.filter((row) => row.date >= period.start && row.date <= period.end && row.value !== null)
      const base = Number(rows[0]?.value)
      return { label: period.label, rows: rows.map((row, elapsed) => ({ elapsed, value: mode === 'indexed' ? (base ? 100 * Number(row.value) / base : null) : std ? (Number(row.value) - mean) / std : null, date: row.date })) }
    })
    const length = Math.max(...paths.map((path) => path.rows.length), 0)
    return { labels: paths.map((path) => path.label), rows: Array.from({ length }, (_, elapsed) => ({ elapsed, [paths[0]?.label ?? 'first']: paths[0]?.rows[elapsed]?.value ?? null, [paths[1]?.label ?? 'second']: paths[1]?.rows[elapsed]?.value ?? null })) }
  }, [customStart, first, indicator, mode, second])
  return <section className="mt-8 border-t border-stone-200 pt-6 dark:border-stone-800"><h3 className="font-semibold">Compare historical episodes</h3><p className="mt-1 text-xs leading-5 text-stone-500">Paths are aligned by elapsed observation. Z-scores use the full published history and do not change with the selected period; indexed mode starts each path at 100.</p><div className="mt-4 flex flex-wrap gap-3">{[first, second].map((selected, index) => <select key={index} value={selected} onChange={(event) => index ? setSecond(event.target.value) : setFirst(event.target.value)} className="h-10 border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]">{options.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select>)}<select value={mode} onChange={(event) => setMode(event.target.value as 'indexed' | 'zscore')} className="h-10 border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]"><option value="zscore">Z-score</option><option value="indexed">Indexed to 100</option></select>{[first, second].includes('custom') && <input type="date" value={customStart} onChange={(event) => setCustomStart(event.target.value)} className="h-10 border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]" aria-label="Custom comparison start date" />}</div><div className="mt-4 h-64"><ResponsiveContainer><LineChart data={data.rows}><CartesianGrid opacity={0.2} /><XAxis dataKey="elapsed" label={{ value: 'Elapsed observations', position: 'bottom' }} /><YAxis /><Tooltip />{data.labels.map((label, index) => <Line key={label} dataKey={label} stroke={index ? '#2563eb' : '#0f766e'} strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />)}</LineChart></ResponsiveContainer></div></section>
}
