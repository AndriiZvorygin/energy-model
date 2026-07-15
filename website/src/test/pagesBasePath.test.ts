import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('GitHub Pages configuration', () => {
  it('keeps the energy-model base path and direct-route fallback', () => {
    const root = resolve(import.meta.dirname, '../..')
    expect(readFileSync(resolve(root, 'vite.config.ts'), 'utf8')).toContain("base: '/energy-model/'")
    expect(readFileSync(resolve(root, 'scripts/prepare-pages.mjs'), 'utf8')).toContain('dist/404.html')
  })
})
