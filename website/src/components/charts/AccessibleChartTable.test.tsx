import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AccessibleChartTable } from './AccessibleChartTable'

describe('accessible chart table', () => {
  it('renders units and explicit missing-value indicators', () => {
    render(<AccessibleChartTable rows={[{ date: '2020-01-01', oil: null }, { date: '2020-02-01', oil: 52.25 }]} series={[{ key: 'oil', label: 'WTI', unit: 'USD per barrel', source: 'FRED', status: 'measured', defaultVisible: true, finalObservationDate: '2020-02-01' }]} />)
    expect(screen.getByText('USD per barrel')).toBeInTheDocument()
    expect(screen.getByText('Not available')).toBeInTheDocument()
    expect(screen.getByText('52.25')).toBeInTheDocument()
  })
})
