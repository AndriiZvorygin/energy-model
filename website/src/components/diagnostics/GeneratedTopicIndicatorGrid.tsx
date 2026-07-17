import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { AffordabilityIndicatorGrid } from '../affordability/AffordabilityIndicatorGrid'
import { useGeneratedJson } from '../charts/useChartData'
import { resolvePresentationRoute } from './GeneratedRouteEvidenceSummary'

type SummaryRow = { indicatorFile: string | null; group?: string }
type Summary = { supporting: SummaryRow[]; mixed: SummaryRow[]; contradicting: SummaryRow[]; insufficient: SummaryRow[] }
type EvidencePayload = { evidence: Record<string, Summary> }
type PresentationManifest = { routes: Record<string, { evidenceKey: string }> }

export function GeneratedTopicIndicatorGrid({ groups }: { groups?: string[] }) {
  const location = useLocation()
  const { data: presentation, error: presentationError } = useGeneratedJson<PresentationManifest>('presentation-manifest.json')
  const { data: evidence, error: evidenceError } = useGeneratedJson<EvidencePayload>('evidence-summary.json')
  const route = presentation ? resolvePresentationRoute(presentation as never, location.pathname) : undefined
  const files = useMemo(() => {
    const summary = route ? evidence?.evidence[route.evidenceKey] : undefined
    if (!summary) return []
    return [...new Set(['supporting', 'mixed', 'contradicting']
      .flatMap((status) => summary[status as keyof Summary])
      .filter((row) => !groups?.length || (row.group && groups.includes(row.group)))
      .map((row) => row.indicatorFile)
      .filter((file): file is string => Boolean(file)))]
  }, [evidence, groups, route])
  if (presentationError || evidenceError) return <p className="mt-6 text-sm text-amber-700">Indicator histories unavailable: {presentationError ?? evidenceError}</p>
  if (!files.length) return <p className="mt-6 text-sm text-stone-500">Loading annual indicator histories…</p>
  return <AffordabilityIndicatorGrid files={files} />
}
