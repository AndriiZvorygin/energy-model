import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { foodPageGeographies } from '../pages/FoodAffordability'
import { housingPageGeographies } from '../pages/HousingAffordability'

const generated = resolve(import.meta.dirname, '../../public/generated')

function evidenceFiles(key: string) {
  const payload = JSON.parse(readFileSync(resolve(generated, 'evidence-summary.json'), 'utf8'))
  return ['supporting', 'mixed', 'contradicting'].flatMap((status) => payload.evidence[key][status].map((row: { indicatorFile: string | null }) => row.indicatorFile).filter(Boolean))
}

describe('evidence geography boundaries', () => {
  it('keeps primary food and housing content scoped by geography', () => {
    expect(foodPageGeographies.global.primaryIndicatorFiles.every((file) => file.startsWith('global/'))).toBe(true)
    expect(foodPageGeographies.canada.primaryIndicatorFiles.every((file) => file.startsWith('canada/'))).toBe(true)
    expect(foodPageGeographies['owen-sound'].primaryIndicatorFiles).toEqual([])
    expect(housingPageGeographies.global.primaryIndicatorFiles.every((file) => file.startsWith('global/'))).toBe(true)
    expect(housingPageGeographies.canada.primaryIndicatorFiles.every((file) => file.startsWith('canada/'))).toBe(true)
    expect(housingPageGeographies['owen-sound'].primaryIndicatorFiles).toEqual([])
  })

  it('keeps generated Canada and Owen Sound evidence from leaking global or U.S. files', () => {
    for (const key of ['canada:food', 'canada:housing', 'canada:affordability']) {
      expect(evidenceFiles(key).every((file) => file.startsWith('canada/'))).toBe(true)
    }
    for (const key of ['owen-sound:affordability', 'owen-sound:food', 'owen-sound:housing']) {
      expect(evidenceFiles(key)).toEqual([])
    }
    expect(evidenceFiles('global:food').every((file) => file.startsWith('global/'))).toBe(true)
    expect(evidenceFiles('global:housing').every((file) => file.startsWith('global/'))).toBe(true)
  })

  it('keeps page copy and primary data contracts explicit about geography', () => {
    expect(foodPageGeographies.global.title).toMatch(/Global/)
    expect(foodPageGeographies.canada.title).toMatch(/Canadian/)
    expect(foodPageGeographies['owen-sound'].title).toMatch(/Owen Sound/)
    expect(foodPageGeographies.canada.primaryIndicatorFiles.every((file) => !file.startsWith('global/') && !file.startsWith('us/'))).toBe(true)
    expect(foodPageGeographies['owen-sound'].description).toMatch(/Owen Sound/)
    expect(housingPageGeographies.global.title).toMatch(/Global/)
    expect(housingPageGeographies.canada.title).toMatch(/Canadian/)
    expect(housingPageGeographies['owen-sound'].title).toMatch(/Owen Sound/)
    expect(housingPageGeographies.canada.primaryIndicatorFiles.every((file) => !file.startsWith('global/') && !file.startsWith('us/'))).toBe(true)
    expect(housingPageGeographies['owen-sound'].description).toMatch(/Owen Sound/)
  })

  it('keeps presentation route metadata aligned with the displayed geography', () => {
    const manifest = JSON.parse(readFileSync(resolve(generated, 'presentation-manifest.json'), 'utf8'))
    expect(manifest.routes['/global/food-prices']).toMatchObject({ geography: 'global', topic: 'food', evidenceKey: 'global:food' })
    expect(manifest.routes['/global/housing']).toMatchObject({ geography: 'global', topic: 'housing', evidenceKey: 'global:housing' })
    expect(manifest.routes['/canada/food']).toMatchObject({ geography: 'canada', topic: 'food', evidenceKey: 'canada:food' })
    expect(manifest.routes['/owen-sound/food']).toMatchObject({ geography: 'owen-sound', topic: 'food', evidenceKey: 'owen-sound:food' })
    expect(manifest.routes['/owen-sound/housing']).toMatchObject({ geography: 'owen-sound', topic: 'housing', evidenceKey: 'owen-sound:housing' })
  })
})
