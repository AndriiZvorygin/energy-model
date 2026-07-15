import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ResearchTimeSeriesChart } from './ResearchTimeSeriesChart'

const dataset = { schemaVersion: '1.1.0', id: 'partial', title: 'Partial observations', description: 'A partial-data fixture.', plainLanguageSummary: 'A plain summary.', howToRead: 'Read the line.', calculation: { formula: 'x', explanation: 'Fixture.', example: 'x=1' }, patternsToWatch: ['Changes'], limitations: ['Partial data'], sourceNotes: ['Fixture'], transformation: { type: 'raw', referenceStart: '2020-01-01', referenceEnd: '2020-03-01', mean: null, standardDeviation: null }, frequency: 'monthly', dateRange: { start: '2020-01-01', end: '2020-03-01' }, series: [{ key: 'oil', label: 'Oil', unit: 'USD', source: 'Fixture', status: 'measured', defaultVisible: true, finalObservationDate: '2020-03-01', color: '#0f766e' }], observations: [{ date: '2020-01-01', oil: 50 }, { date: '2020-02-01', oil: null }, { date: '2020-03-01', oil: 55 }], annotations: [], availableTransformations: ['raw', 'zscore'], evidenceLabel: 'Contextual indicator', methodology: {}, staticFigure: 'fallback.png', generatedAt: '2026-01-01' }

describe('research time-series chart', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { value: 390, configurable: true })
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({
      ok: true,
      json: () => Promise.resolve(url.includes('partial') ? dataset : url.includes('events') ? { events: [] } : { regimes: [], recessions: [] }),
    })))
  })
  it('renders partial data, mobile-safe controls, and the table alternative', async () => {
    render(<ResearchTimeSeriesChart file="partial.json" syncUrl={false} />)
    await waitFor(() => expect(screen.getByText('Partial observations')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Oil' })).toBeChecked())
    expect(screen.getByRole('button', { name: /5y/i })).toBeInTheDocument()
    expect(screen.getByText('Accessible data table')).toBeInTheDocument()
    expect(screen.getByText('A plain summary.')).toBeInTheDocument()
    expect(screen.getByText('Chart details and calculations')).toBeInTheDocument()
    expect(screen.getByText('Not available')).toBeInTheDocument()
  })
})
