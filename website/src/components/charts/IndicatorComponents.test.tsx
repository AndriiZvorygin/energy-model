import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { CurrentStateIndicatorCard } from '../CurrentStateIndicatorCard'
import { ChartModal } from './ChartModal'
import { IndicatorHistoryChart } from './IndicatorHistoryChart'
import type { IndicatorDataset } from './chartTypes'

const indicator: IndicatorDataset = {
  schemaVersion: 1, id: 'test-indicator', field: 'test', label: 'Test indicator', description: 'A test history.', unit: 'percent', frequency: 'monthly', status: 'derived', layer: 'Test layer', interpretationDirection: 'higher-generally-stressful', interpretationLabel: 'Stressful', interpretation: 'The latest reading is elevated and should be confirmed.', source: 'Test source', sourceUrl: 'https://example.com', startDate: '2020-01-01', endDate: '2025-01-01', latest: { date: '2025-01-01', value: 6, previousValue: 5, oneYearChange: 2, threeMonthChange: 1, fourQuarterChange: 2, historicalPercentile: 90, percentileSince2000: 90, distanceFromMedian: 3, momentum: 'accelerating' }, referenceRanges: { historicalMedian: 3, p10: 1, p25: 2, p75: 4, p90: 5, minimum: 0, maximum: 7 }, observations: Array.from({ length: 61 }, (_, index) => ({ date: `${2020 + Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}-01`, value: index === 4 ? null : index / 10 })), confirmingIndicators: ['Confirm A'], conflictingIndicators: ['Conflict B'], evidenceChecks: [{ label: 'Confirm A', status: 'confirms', targetIndicatorId: 'confirm-a', targetInterpretationLabel: 'Stressful', targetLatestDate: '2025-01-01', explanation: 'Same classification.' }], confidenceLevel: 'medium', evidenceLabel: 'Contextual indicator', calculation: { formula: 'value[t]', explanation: 'Published value.', example: '6 percent.' }, limitations: ['Fixture limitation.'], generatedAt: '2026-01-01',
}

function CardHarness() {
  const [open, setOpen] = useState(false)
  return <><CurrentStateIndicatorCard indicator={indicator} onExpand={() => setOpen(true)} /><ChartModal open={open} title={indicator.label} onClose={() => setOpen(false)}><IndicatorHistoryChart indicator={indicator} /></ChartModal></>
}

describe('current-state interactive indicator', () => {
  it('renders historical context and opens the expanded chart from a tap', () => {
    Object.defineProperty(window, 'innerWidth', { value: 390, configurable: true })
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({ ok: true, json: () => Promise.resolve(url.includes('events') ? { events: [] } : { regimes: [], recessions: [] }) })))
    render(<CardHarness />)
    expect(screen.getByText('90th full-history percentile')).toBeInTheDocument()
    expect(screen.getByText('Median 3')).toBeInTheDocument()
    const historyButton = screen.getAllByRole('button', { name: /open full history/i }).find((element) => element.tagName === 'BUTTON')
    expect(historyButton).toBeDefined()
    fireEvent.click(historyButton!)
    expect(screen.getByRole('dialog', { name: 'Test indicator' })).toBeInTheDocument()
    expect(screen.getByText('Accessible data table')).toBeInTheDocument()
    expect(screen.getByText('Compare historical episodes')).toBeInTheDocument()
    expect(screen.getAllByText(/Confirm A/).length).toBeGreaterThan(0)
  })

  it('uses interpretation metadata instead of inferring good or bad from the component', () => {
    render(<CurrentStateIndicatorCard indicator={indicator} onExpand={() => undefined} />)
    expect(screen.getByText('Stressful')).toBeInTheDocument()
    expect(screen.getByText('accelerating')).toBeInTheDocument()
  })
})
