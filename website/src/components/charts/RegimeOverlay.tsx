import { ReferenceArea } from 'recharts'
import type { ChartRegime } from './chartTypes'
import { chartColor } from './chartPalette'

export function RegimeOverlay({ regimes }: { regimes: ChartRegime[] }) {
  return <>{regimes.map((regime) => <ReferenceArea key={regime.id} x1={regime.start} x2={regime.end} fill={chartColor(regime.color)} fillOpacity={0.13} strokeOpacity={0} ifOverflow="hidden" />)}</>
}
