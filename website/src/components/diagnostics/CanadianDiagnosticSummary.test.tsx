import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { CanadianDiagnosticSummary } from './CanadianDiagnosticSummary'
import type { CanadianClassification } from './canadaTypes'

describe('CanadianDiagnosticSummary', () => {
  it('renders both clocks, regional evidence, coverage, and the generated summary', () => {
    const classification = JSON.parse(readFileSync(resolve(import.meta.dirname, '../../../public/generated/canada/current-classification.json'), 'utf8')) as CanadianClassification
    render(<MemoryRouter><CanadianDiagnosticSummary classification={classification} /></MemoryRouter>)
    expect(screen.getByText('Provisional monthly Canadian nowcast')).toBeInTheDocument()
    expect(screen.getByText('Quarterly-aligned Canadian state')).toBeInTheDocument()
    expect(screen.getByText('Ontario transmission')).toBeInTheDocument()
    expect(screen.getByText('Alberta producer conditions')).toBeInTheDocument()
    expect(screen.getByText(/Canadian energy affordability pressure is active/)).toBeInTheDocument()
    expect(screen.getByText(/Resource-producing-region expansion is active/)).toBeInTheDocument()
    expect(screen.queryByText(/inactive/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/insufficient/i)).not.toBeInTheDocument()
  })
})
