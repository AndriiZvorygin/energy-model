import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { RegimeHistoryPayload } from '../charts/chartTypes'
import { chartPalette } from '../charts/chartPalette'

const names: Record<string, string> = { A: 'Expansion', B: 'Physical tightening', C: 'Affordability stress', D: 'Economic transmission', E: 'Demand destruction', F: 'Price collapse', G: 'Labour after-effects', H: 'Recovery / renewed tightening' }

export function RegimeHistoryChart({ history }: { history: RegimeHistoryPayload }) {
  return <div><div className="h-[380px]" role="img" aria-label="Walk-forward quarterly history of all regime scores"><ResponsiveContainer><LineChart data={history.rows}><CartesianGrid opacity={0.45} /><XAxis dataKey="date" minTickGap={45} tickFormatter={(value) => String(value).slice(0, 4)} /><YAxis domain={[0, 1]} width={45} /><Tooltip labelFormatter={(value) => String(value).slice(0, 7)} formatter={(value, key) => [`${(Number(value) * 100).toFixed(1)}%`, names[String(key).replace('scores.', '')] ?? key]} />{Object.keys(names).map((id, index) => <Line key={id} dataKey={`scores.${id}`} name={id} stroke={chartPalette[index % chartPalette.length]} dot={false} strokeWidth={1.8} isAnimationActive={false} />)}</LineChart></ResponsiveContainer></div><div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-stone-500">{Object.entries(names).map(([id, label], index) => <span key={id} style={{ color: chartPalette[index % chartPalette.length] }}>{id}: {label}</span>)}</div></div>
}
