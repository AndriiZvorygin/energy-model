import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { ResearchNavigation } from '../components/ResearchNavigation'

describe('research navigation', () => {
  it('groups destinations and exposes Owen Sound affordability pages', () => {
    render(
      <MemoryRouter initialEntries={['/owen-sound/affordability']}>
        <ResearchNavigation />
      </MemoryRouter>,
    )

    expect(screen.getByRole('button', { name: 'Affordability' })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('link', { name: 'Owen Sound overview' })).toHaveAttribute('href', '/owen-sound/affordability')
    expect(screen.getByRole('link', { name: 'Owen Sound food' })).toHaveAttribute('href', '/owen-sound/food')
    expect(screen.getByRole('link', { name: 'Owen Sound housing' })).toHaveAttribute('href', '/owen-sound/housing')

    fireEvent.click(screen.getByRole('button', { name: 'Oil and markets' }))
    expect(screen.getByRole('link', { name: 'Global liquidity' })).toBeVisible()
    expect(screen.queryByRole('link', { name: 'Owen Sound overview' })).not.toBeInTheDocument()
  })
})
