import { describe, expect, it } from 'vitest'
import type { ChartDataset, ChartObservation, ChartSeries } from './chartTypes'
import { chartStateSearch, parseChartState, rowsToCsv, shiftSeries, transformObservations, validateDataset } from './chartUtils'

const series: ChartSeries[] = [{ key: 'price', label: 'Price', unit: 'USD', source: 'Test source', status: 'measured', defaultVisible: true, finalObservationDate: '2021-01-01', frequency: 'monthly' }]
const observations: ChartObservation[] = Array.from({ length: 13 }, (_, index) => ({ date: `${2020 + Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}-01`, price: 100 + index }))
const details = { plainLanguageSummary: 'Summary', howToRead: 'Read it', calculation: { formula: 'x', explanation: 'Calculation', example: 'x=1' }, patternsToWatch: ['Pattern'], limitations: ['Limit'], sourceNotes: ['Source'], transformation: { type: 'raw' as const, referenceStart: '2020-01-01', referenceEnd: '2020-12-01', mean: null, standardDeviation: null } }

describe('chart transformations', () => {
  it('calculates index, percentage change, YoY, and z-score without mutating source rows', () => {
    expect(transformObservations(observations, series, 'indexed')[12].price).toBe(112)
    expect(transformObservations(observations, series, 'pct_change')[1].price).toBeCloseTo(1)
    expect(transformObservations(observations, series, 'yoy')[12].price).toBeCloseTo(12)
    const standardized = transformObservations(observations, series, 'zscore').map((row) => Number(row.price))
    expect(standardized.reduce((sum, item) => sum + item, 0)).toBeCloseTo(0)
    expect(observations[0].price).toBe(100)
  })

  it('shifts a predictor backward in source time for a positive lead', () => {
    const shifted = shiftSeries(observations, 'price', 2, 'lead')
    expect(shifted[1].lead).toBeNull()
    expect(shifted[2].lead).toBe(100)
    expect(shifted[2].__sourceDate_lead).toBe('2020-01-01')
  })

  it('preserves a fixed z-score baseline when the visible range changes', () => {
    const full = transformObservations(observations, series, 'zscore', observations)
    const subset = transformObservations(observations.slice(6), series, 'zscore', observations)
    expect(subset[0].price).toBeCloseTo(Number(full[6].price))
    expect(subset[0].__raw_price).toBe(106)
  })
})

describe('chart state and downloads', () => {
  it('round-trips compact URL chart state', () => {
    const defaults = { series: ['price'], transformation: 'raw' as const, range: 'all', lag: 5 }
    const parsed = parseChartState(`?${chartStateSearch({ ...defaults, transformation: 'zscore', range: '10y', lag: 4 })}`, defaults)
    expect(parsed).toMatchObject({ series: ['price'], transformation: 'zscore', range: '10y', lag: 4 })
    expect(parseChartState('', defaults).lag).toBe(5)
  })

  it('writes units and missing values to CSV', () => {
    const csv = rowsToCsv([{ date: '2020-01-01', price: null }, { date: '2020-02-01', price: 12 }], series)
    expect(csv).toContain('Price (USD)')
    expect(csv).toContain('2020-01-01,')
    expect(csv).toContain('2020-02-01,12')
  })
})

describe('schema validation', () => {
  const dataset: ChartDataset = { schemaVersion: '1.1.0', id: 'test', title: 'Test', description: 'Test data', ...details, frequency: 'monthly', dateRange: { start: '2020-01-01', end: '2021-01-01' }, series, observations, annotations: [], availableTransformations: ['raw'], evidenceLabel: 'Contextual indicator', methodology: {}, staticFigure: 'test.png', generatedAt: '2026-01-01' }
  it('accepts ordered observations and rejects duplicates or missing units', () => {
    expect(validateDataset(dataset)).toEqual([])
    expect(validateDataset({ ...dataset, observations: [...observations, observations[12]] })).toContain('Dates must be strictly increasing and unique')
    expect(validateDataset({ ...dataset, series: [{ ...series[0], unit: '' }] })).toContain('Missing unit for price')
  })
})
