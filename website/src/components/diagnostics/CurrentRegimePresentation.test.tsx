import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { CurrentClassification } from '../charts/chartTypes'
import { ClassificationSummary } from './ClassificationSummary'
import { buildPlainLanguageSummary, CurrentRegimeNarrative } from './CurrentRegimeNarrative'
import { RegimeScoreChart } from './RegimeScoreChart'

const classification = JSON.parse(readFileSync(resolve(import.meta.dirname, '../../../public/generated/current-classification.json'), 'utf8')) as CurrentClassification

describe('current regime presentation', () => {
  it('derives the plain-language interpretation from existing regime scores', () => {
    const summary = buildPlainLanguageSummary(classification)
    expect(summary.find((item) => item.label === 'Physical oil market')?.text).toContain('support a physical-tightening interpretation')
    expect(summary.find((item) => item.label === 'Production and labour')?.text).toContain('not yet supported')
    expect(summary.find((item) => item.label === 'Demand and price collapse')?.text).toContain('not supported')
  })

  it.each([390, 768, 1440])('renders the mixed-state evidence at %ipx', (width) => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: width })
    const view = render(<MemoryRouter><ClassificationSummary classification={classification} /><CurrentRegimeNarrative classification={classification} /><RegimeScoreChart scores={classification.allRegimeScores} /></MemoryRouter>)
    expect(screen.getByText('Quarterly-aligned state')).toBeInTheDocument()
    expect(screen.getByText('Retrospective quarterly classification using revised data')).toBeInTheDocument()
    expect(screen.getByText('Evidence for Physical tightening')).toBeInTheDocument()
    expect(screen.getByText('Evidence qualifying Energy affordability stress')).toBeInTheDocument()
    expect(screen.getByText(/Physical tightness appears to be re-emerging/)).toBeInTheDocument()
    view.unmount()
  })
})
