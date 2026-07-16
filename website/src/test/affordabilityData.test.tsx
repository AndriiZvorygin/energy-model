import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Affordability } from '../pages/Affordability'

const generated = resolve(import.meta.dirname, '../../public/generated')

describe('affordability evidence', () => {
  afterEach(() => vi.restoreAllMocks())

  it('publishes chart-ready global, Canadian, and U.S. data without classifier activation', () => {
    const global = JSON.parse(readFileSync(resolve(generated, 'global/indicators/fao-food-price-index.json'), 'utf8'))
    const canada = JSON.parse(readFileSync(resolve(generated, 'canada/indicators/new-housing-price-index.json'), 'utf8'))
    const us = JSON.parse(readFileSync(resolve(generated, 'us/indicators/us-food-at-home-cpi.json'), 'utf8'))
    for (const payload of [global, canada, us]) {
      expect(payload.observations.length).toBeGreaterThan(24)
      expect(payload.futureClassifierMetadata.status).toBe('metadata_only_not_scored')
      expect(payload.sourceDate).toBeTruthy()
      expect(payload.retrievalDate).toBeTruthy()
    }
  })

  it('keeps property purchase prices separate from shelter services', () => {
    const chart = JSON.parse(readFileSync(resolve(generated, 'affordability-canada-housing-costs.json'), 'utf8'))
    expect(chart.series.map((item: { key: string }) => item.key)).toEqual(['NHPI_YoY', 'Rent_YoY', 'Mortgage_interest_YoY', 'Shelter_YoY'])
    expect(chart.availableTransformations).toContain('indexed')
  })

  it('renders the affordability observatory entry point', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    render(<MemoryRouter><Affordability /></MemoryRouter>)
    expect(screen.getByText('Food and housing affordability')).toBeInTheDocument()
    expect(screen.getByText('Global current evidence')).toBeInTheDocument()
    expect(screen.getByText('Food-price evidence')).toBeInTheDocument()
    expect(screen.getByText('Housing-price evidence')).toBeInTheDocument()
  })
})
