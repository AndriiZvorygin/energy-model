import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

type LagPoint = { target: string; lag: number | null; correlation: number | null }

export function InteractiveLagChart({ data, convention }: { data: readonly LagPoint[]; convention: string }) {
  const targets = [...new Set(data.map((point) => point.target))]
  const [visible, setVisible] = useState(() => new Set(targets))
  const colors = ['#0f766e', '#d97706', '#be123c']
  const rows = useMemo(() => {
    const lags = [...new Set(data.map((point) => point.lag).filter((lag): lag is number => lag !== null))].sort((a, b) => a - b)
    return lags.map((lag) => Object.fromEntries([
      ['lag', lag],
      ...targets.map((target) => [target, data.find((point) => point.target === target && point.lag === lag)?.correlation ?? null]),
    ]))
  }, [data, targets])

  const toggle = (target: string) => setVisible((current) => {
    const next = new Set(current)
    if (next.has(target) && next.size > 1) next.delete(target)
    else next.add(target)
    return next
  })

  return (
    <div className="border-y border-stone-200 py-6 dark:border-stone-800">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-stone-600 dark:text-stone-400">Hover for values. Use the controls to compare series.</p>
        <div className="flex gap-2" aria-label="Series visibility">
          {targets.map((target, index) => <button key={target} type="button" onClick={() => toggle(target)} aria-pressed={visible.has(target)} className={`flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-semibold transition ${visible.has(target) ? 'border-stone-400 bg-white dark:bg-stone-800' : 'border-stone-200 text-stone-400 dark:border-stone-800'}`}><span className="h-2 w-2 rounded-full" style={{ backgroundColor: colors[index] }} />{target}</button>)}
        </div>
      </div>
      <div className="h-[330px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#a8a29e" opacity={0.25} />
            <XAxis dataKey="lag" tick={{ fontSize: 12 }} label={{ value: 'Lag (months)', position: 'insideBottom', offset: -3, fontSize: 12 }} />
            <YAxis domain={[-0.8, 0.8]} tick={{ fontSize: 12 }} width={44} />
            <Tooltip formatter={(value) => typeof value === 'number' ? value.toFixed(3) : value} labelFormatter={(value) => `Lag ${value} months`} />
            <ReferenceLine y={0} stroke="#78716c" />
            <ReferenceLine x={0} stroke="#78716c" strokeDasharray="4 4" />
            {targets.map((target, index) => visible.has(target) && <Line key={target} type="monotone" dataKey={target} stroke={colors[index]} strokeWidth={2.25} dot={false} activeDot={{ r: 4 }} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-stone-500">{convention}</p>
    </div>
  )
}
