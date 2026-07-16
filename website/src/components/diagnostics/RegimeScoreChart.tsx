import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { RegimeScore } from '../charts/chartTypes'

export function RegimeScoreChart({ scores }: { scores: RegimeScore[] }) {
  const rows = [...scores].sort((a, b) => b.score - a.score).map((item) => ({ ...item, shortName: `${item.id}. ${item.name}` }))
  return <div>
    <div className="h-[420px]" role="img" aria-label="Current score for each candidate energy-economic regime"><ResponsiveContainer><BarChart data={rows} layout="vertical" margin={{ left: 18, right: 24 }}><CartesianGrid strokeDasharray="3 3" opacity={0.45} /><XAxis type="number" domain={[0, 1]} tickFormatter={(value) => Number(value).toFixed(1)} /><YAxis type="category" dataKey="shortName" width={205} tick={{ fontSize: 11 }} /><ReferenceLine x={0.6} stroke="#be123c" strokeDasharray="5 4" label={{ value: 'classification threshold', position: 'insideTopRight', fontSize: 10 }} /><Tooltip formatter={(value, name, item) => name === 'score' ? [`${(Number(value) * 100).toFixed(1)}%`, `Score · coverage ${(Number(item.payload.coverage) * 100).toFixed(0)}%`] : [value, name]} /><Bar dataKey="score" fill="#0f766e" isAnimationActive={false} /></BarChart></ResponsiveContainer></div>
    <p className="mt-2 text-xs leading-5 text-stone-500">Scores combine equally normalized evidence layers, symptom agreement, reliability and freshness, then subtract contradiction and missing-data penalties. A top score below 0.60 remains unclassified; close leaders may be reported as a mixed transition.</p>
  </div>
}
