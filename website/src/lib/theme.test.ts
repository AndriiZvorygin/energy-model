import { describe, expect, it } from 'vitest'
import { isLocalNight, resolveTheme } from './theme'

describe('client-side theme resolution', () => {
  it('uses dark theme during local nighttime hours', () => {
    expect(isLocalNight(new Date(2026, 6, 15, 5, 59))).toBe(true)
    expect(isLocalNight(new Date(2026, 6, 15, 19, 0))).toBe(true)
  })

  it('uses light theme during local daytime hours', () => {
    expect(isLocalNight(new Date(2026, 6, 15, 7, 0))).toBe(false)
    expect(isLocalNight(new Date(2026, 6, 15, 18, 59))).toBe(false)
  })

  it('honours explicit preferences instead of local time', () => {
    const noon = new Date(2026, 6, 15, 12, 0)
    const midnight = new Date(2026, 6, 15, 0, 0)
    expect(resolveTheme('dark', noon)).toBe('dark')
    expect(resolveTheme('light', midnight)).toBe('light')
    expect(resolveTheme('auto', noon)).toBe('light')
    expect(resolveTheme('auto', midnight)).toBe('dark')
  })
})
