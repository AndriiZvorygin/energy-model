import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { getVisibleNavigationRoutes, navigationAliases, ResearchNavigation } from '../components/ResearchNavigation'

describe('research navigation', () => {
  it('groups destinations and exposes Owen Sound affordability pages', () => {
    render(
      <MemoryRouter initialEntries={['/owen-sound/affordability']}>
        <ResearchNavigation />
      </MemoryRouter>,
    )

    expect(screen.getByRole('button', { name: 'Owen Sound' })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('link', { name: 'Owen Sound overview' })).toHaveAttribute('href', '/owen-sound/affordability')
    expect(screen.getByRole('link', { name: 'Owen Sound food' })).toHaveAttribute('href', '/owen-sound/food')
    expect(screen.getByRole('link', { name: 'Owen Sound housing' })).toHaveAttribute('href', '/owen-sound/housing')

    fireEvent.click(screen.getByRole('button', { name: 'Core model' }))
    expect(screen.getByRole('link', { name: 'System overview' })).toHaveAttribute('href', '/overview')
    expect(screen.getByRole('link', { name: 'Global liquidity' })).toBeVisible()
    expect(screen.queryByRole('link', { name: 'Owen Sound overview' })).not.toBeInTheDocument()
  })

  it('keeps every substantive App route visible or explicitly marked as an alias', () => {
    const app = readFileSync(resolve(import.meta.dirname, '../App.tsx'), 'utf8')
    const registered = [...app.matchAll(/<Route path="([^"]+)"/g)].map((match) => match[1]).filter((route) => route !== '/')
    const visible = getVisibleNavigationRoutes()
    const hidden = registered.filter((route) => !visible.has(route) && !navigationAliases.has(route))
    expect(hidden).toEqual([])
  })
})
