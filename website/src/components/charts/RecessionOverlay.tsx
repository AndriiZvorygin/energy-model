import { ReferenceArea } from 'recharts'
import type { ChartRegime } from './chartTypes'

export function RecessionOverlay({ recessions }: { recessions: ChartRegime[] }) {
  return <>{recessions.map((period) => <ReferenceArea key={period.id} x1={period.start} x2={period.end} fill="#78716c" fillOpacity={0.12} strokeOpacity={0} ifOverflow="hidden" />)}</>
}
