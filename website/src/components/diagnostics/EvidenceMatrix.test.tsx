import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EvidenceMatrix, type EvidenceMatrixRow } from './EvidenceMatrix'

const rows: EvidenceMatrixRow[] = [
  { id: 'support', label: 'Energy CPI', disposition: 'supports', status: 'Required evidence · supporting', reason: 'The indicator is consistent with this interpretation.', value: 4.2, unit: 'percent', percentile: 81, direction: 'rising', sourceDate: '2026-05-01' },
  { id: 'mixed', label: 'Employment rate', disposition: 'mixed', status: 'Confirming evidence · mixed', reason: 'The indicator provides partial or ambiguous evidence.' },
  { id: 'conflict', label: 'Unemployment', disposition: 'contradicts', status: 'Conflicting evidence · contradicting', reason: 'The indicator moves against this interpretation.' },
  { id: 'missing', label: 'Household energy share', disposition: 'insufficient', status: 'Missing evidence · insufficient', reason: 'The available data cannot evaluate this indicator.' },
]

describe('EvidenceMatrix', () => {
  it('renders all four accessible evidence statuses and clickable counts', () => {
    render(<EvidenceMatrix interpretation="Energy affordability pressure" confidence="moderate" coverage={0.75} rows={rows} />)
    expect(screen.getByRole('heading', { name: 'Energy affordability pressure' })).toBeInTheDocument()
    expect(screen.getAllByText('Supports').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Mixed or unclear').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Contradicts').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Insufficient data').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: /Supports 1/ }))
    expect(screen.getByText('Energy CPI')).toBeInTheDocument()
    expect(screen.queryByText('Employment rate')).not.toBeInTheDocument()
  })

  it('expands evidence details with values, dates, and calculation context', () => {
    render(<EvidenceMatrix interpretation="Energy affordability pressure" confidence="moderate" coverage={0.75} rows={rows} />)
    const rowButton = screen.getByRole('button', { name: /Energy CPI/ })
    fireEvent.click(rowButton)
    expect(rowButton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('4.2 percent')).toBeInTheDocument()
    expect(screen.getByText('2026-05-01')).toBeInTheDocument()
    expect(screen.getByText('The indicator is consistent with this interpretation.')).toBeInTheDocument()
  })

  it('keeps the matrix usable at a mobile viewport', () => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 390 })
    render(<EvidenceMatrix interpretation="Current evidence" confidence="low" coverage={null} rows={rows} />)
    const table = screen.getByRole('table')
    expect(within(table).getByText('Household energy share')).toBeInTheDocument()
    expect(screen.getByText('Not published')).toBeInTheDocument()
  })
})
