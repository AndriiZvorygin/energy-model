import { describe, expect, it } from 'vitest'
import { resolvePresentationRoute } from './GeneratedRouteEvidenceSummary'

const manifest = {
  schemaVersion: 1,
  refineryVersion: '1.0.0',
  generatedAt: '2026-07-16T00:00:00Z',
  policy: { includeStatusesInDiagnosticSummary: ['supporting', 'mixed', 'contradicting'] as Array<'supporting' | 'mixed' | 'contradicting'> },
  routes: {
    '/canada': { route: '/canada', evidenceTopic: 'canada', interpretation: 'Current Canadian state', confidence: 'moderate', coverage: 1, oldestObservationDate: '2026-01-01', newestObservationDate: '2026-06-01' },
  },
}

describe('resolvePresentationRoute', () => {
  it('resolves canonical and trailing-slash routes from the generated contract', () => {
    expect(resolvePresentationRoute(manifest, '/canada')?.evidenceTopic).toBe('canada')
    expect(resolvePresentationRoute(manifest, '/canada/')?.evidenceTopic).toBe('canada')
  })

  it('does not invent a presentation for an unconfigured route', () => {
    expect(resolvePresentationRoute(manifest, '/unknown')).toBeUndefined()
  })
})
