import { ReferenceArea } from 'recharts'
import type { ChartRegime } from './chartTypes'

export function RecessionOverlay({ recessions }: { recessions: ChartRegime[] }) {
  return <>{recessions.map((period) => <ReferenceArea key={period.id} x1={period.start} x2={period.end} fill="var(--chart-neutral)" fillOpacity={0.17} strokeOpacity={0} ifOverflow="hidden" />)}</>
}
