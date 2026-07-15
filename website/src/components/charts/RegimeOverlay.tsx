import { ReferenceArea } from 'recharts'
import type { ChartRegime } from './chartTypes'

export function RegimeOverlay({ regimes }: { regimes: ChartRegime[] }) {
  return <>{regimes.map((regime) => <ReferenceArea key={regime.id} x1={regime.start} x2={regime.end} fill={regime.color} fillOpacity={0.09} strokeOpacity={0} ifOverflow="hidden" />)}</>
}
