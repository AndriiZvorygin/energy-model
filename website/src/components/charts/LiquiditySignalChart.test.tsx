import { fireEvent, render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LiquiditySignalChart } from './LiquiditySignalChart'

const { chart } = vi.hoisted(() => ({ chart: vi.fn() }))

vi.mock('./ResearchTimeSeriesChart', () => ({
  ResearchTimeSeriesChart: (props: { file: string; initialTransformation: string; zeroLine?: boolean; primaryControls?: ReactNode }) => {
    chart(props)
    return <><div data-testid="research-chart">{props.file} · {props.initialTransformation} · {props.zeroLine ? 'zero line' : 'no zero line'}</div>{props.primaryControls}</>
  },
}))

describe('LiquiditySignalChart', () => {
  beforeEach(() => chart.mockClear())

  it('switches between actual, standardized, and locked-model residual views', () => {
    render(<LiquiditySignalChart />)
    expect(screen.getByTestId('research-chart')).toHaveTextContent('gm2-oil-lead.json · zscore')

    fireEvent.click(screen.getByRole('tab', { name: 'Raw YoY' }))
    expect(screen.getByTestId('research-chart')).toHaveTextContent('gm2-oil-lead.json · raw')

    fireEvent.click(screen.getByRole('tab', { name: 'Residuals (GM2 removed)' }))
    expect(screen.getByTestId('research-chart')).toHaveTextContent('oil-residual-ci.json · raw · zero line')
    expect(screen.getByText(/actual oil YoY minus the liquidity-implied YoY path/)).toBeInTheDocument()
  })
})
