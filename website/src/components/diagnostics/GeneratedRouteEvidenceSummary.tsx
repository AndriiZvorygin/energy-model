import { useLocation } from 'react-router-dom'
import { useGeneratedJson } from '../charts/useChartData'
import { GeneratedEvidenceSummary } from './GeneratedEvidenceSummary'

type PresentationRoute = {
  route: string
  evidenceTopic: string
  interpretation: string
  confidence: string
  coverage: number | null
  oldestObservationDate: string | null
  newestObservationDate: string | null
}

type PresentationManifest = {
  schemaVersion: number
  refineryVersion: string
  generatedAt: string
  policy: { includeStatusesInDiagnosticSummary: Array<'supporting' | 'mixed' | 'contradicting' | 'insufficient'> }
  routes: Record<string, PresentationRoute>
}

export function resolvePresentationRoute(manifest: PresentationManifest, pathname: string) {
  return manifest.routes[pathname.replace(/\/$/, '') || '/']
}

export function GeneratedRouteEvidenceSummary({ title = 'Diagnostic summary' }: { title?: string }) {
  const location = useLocation()
  const { data, error } = useGeneratedJson<PresentationManifest>('presentation-manifest.json')
  if (error) return <p className="border-y border-amber-500 py-4 text-sm text-amber-700">Refinery presentation unavailable: {error}</p>
  if (!data) return <p className="border-y border-stone-300 py-6 text-sm text-stone-500 dark:border-stone-700">Loading refinery interpretation…</p>
  const route = resolvePresentationRoute(data, location.pathname)
  if (!route) return <p className="border-y border-amber-500 py-4 text-sm text-amber-700">No refinery presentation contract exists for {location.pathname}.</p>
  return <GeneratedEvidenceSummary topic={route.evidenceTopic} title={title} includeStatuses={data.policy.includeStatusesInDiagnosticSummary} />
}
