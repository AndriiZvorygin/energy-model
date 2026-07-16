import { ReferenceLine } from 'recharts'
import type { ChartEvent } from './chartTypes'

export function EventAnnotations({ events, enabled = true }: { events: ChartEvent[]; enabled?: boolean }) {
  if (!enabled) return null
  return <>{events.map((event) => <ReferenceLine key={event.id} x={event.start} stroke="var(--chart-8)" strokeWidth={1.5} strokeDasharray="3 4" strokeOpacity={0.9} ifOverflow="hidden" />)}</>
}
