import { describe, expect, it } from 'vitest'
import { geographyOptions, topicRoute } from '../components/diagnostics/EvidenceGeographySelector'

describe('evidence geography selector', () => {
  it('discovers same-topic geography routes from the presentation manifest', () => {
    const manifest = {
      routes: {
        '/affordability': {
          route: '/affordability',
          geography: 'canada',
          geographyLabel: 'Canada',
          topic: 'affordability',
          evidenceKey: 'canada:affordability',
        },
        '/owen-sound/affordability': {
          route: '/owen-sound/affordability',
          geography: 'owen-sound',
          geographyLabel: 'Owen Sound',
          topic: 'affordability',
          evidenceKey: 'owen-sound:affordability',
        },
        '/owen-sound/food': {
          route: '/owen-sound/food',
          geography: 'owen-sound',
          geographyLabel: 'Owen Sound',
          topic: 'food',
          evidenceKey: 'owen-sound:food',
        },
      },
    }

    expect(geographyOptions(manifest, '/owen-sound/affordability/').map((route) => route.evidenceKey)).toEqual([
      'canada:affordability',
      'owen-sound:affordability',
    ])
    expect(topicRoute(manifest, '/owen-sound/affordability', 'food', '/affordability/food')).toBe('/owen-sound/food')
  })
})
