import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('GitHub Pages configuration', () => {
  it('keeps the energy-model base path and direct-route fallback', () => {
    const root = resolve(import.meta.dirname, '../..')
    expect(readFileSync(resolve(root, 'vite.config.ts'), 'utf8')).toContain("base: '/energy-model/'")
    const pagesScript = readFileSync(resolve(root, 'scripts/prepare-pages.mjs'), 'utf8')
    expect(pagesScript).toContain("resolve(distRoot, '404.html')")
    expect(pagesScript).toContain("'output-quality'")
    expect(pagesScript).toContain("'canada/current-state'")
    expect(pagesScript).toContain("'compare/canada-us'")
    expect(pagesScript).toContain("resolve(routeDirectory, 'index.html')")
  })
})
