import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const generated = resolve(import.meta.dirname, '../../public/generated')

describe('Canadian generated data', () => {
  const manifest = JSON.parse(readFileSync(resolve(generated, 'canada/manifest.json'), 'utf8'))

  it('keeps Canada as a separate provisionally classified default geography', () => {
    expect(manifest.defaultGeography).toBe('Canada')
    expect(manifest.classificationImplemented).toBe(true)
    const core = manifest.indicators.filter((item: { core: boolean; geography: string }) => item.core && ['Canada', 'Global'].includes(item.geography))
    expect(core).toHaveLength(25)
  })

  it('publishes Canadian symptoms, clocks, regional evidence, and household missing data', () => {
    const current = JSON.parse(readFileSync(resolve(generated, 'canada/current-classification.json'), 'utf8'))
    const symptoms = JSON.parse(readFileSync(resolve(generated, 'canada/symptom-evaluations.json'), 'utf8'))
    const regimes = JSON.parse(readFileSync(resolve(generated, 'canada/regime-scores.json'), 'utf8'))
    expect(current.provisionalClassification.requiredIndicatorAvailability).toBeGreaterThanOrEqual(0.70)
    expect(current.provisionalClassification.freshnessAdjustedCoverage).toBeTypeOf('number')
    expect(current.regionalDivergence.ontarioTransmission).toBeTruthy()
    expect(current.regionalDivergence.albertaProducerConditions).toBeTruthy()
    expect(symptoms.evaluations.find((item: { id: string }) => item.id === 'household_stress').status).toBe('insufficient_data')
    expect(regimes.scores).toHaveLength(8)
  })

  it('preserves geography, units, source dates, and provincial missing-data boundaries', () => {
    const canada = JSON.parse(readFileSync(resolve(generated, 'canada/indicators/canada-unemployment-rate.json'), 'utf8'))
    const ontario = JSON.parse(readFileSync(resolve(generated, 'canada/indicators/ontario-unemployment-rate.json'), 'utf8'))
    expect(canada.geography).toBe('Canada')
    expect(ontario.geography).toBe('Ontario')
    expect(canada.unit).toBe('percent')
    expect(canada.observations.every((row: { sourceDate?: string }) => Boolean(row.sourceDate))).toBe(true)
    expect(ontario.observations.every((row: { value: number | null }) => row.value === null || typeof row.value === 'number')).toBe(true)
  })

  it('loads through the GitHub Pages generated-data path', () => {
    const source = readFileSync(resolve(import.meta.dirname, '../components/charts/useChartData.ts'), 'utf8')
    expect(source).toContain('import.meta.env.BASE_URL')
    expect(source).toContain('generated/${file}')
  })
})
