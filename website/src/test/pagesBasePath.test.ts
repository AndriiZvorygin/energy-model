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
    expect(pagesScript).toContain("'canada/regimes'")
    expect(pagesScript).toContain("'canada/symptoms'")
    expect(pagesScript).toContain("'affordability/food'")
    expect(pagesScript).toContain("'affordability/housing'")
    expect(pagesScript).toContain("'compare/food'")
    expect(pagesScript).toContain("'compare/canada-us'")
    expect(pagesScript).toContain("'owen-sound/affordability'")
    expect(pagesScript).toContain("'owen-sound/food'")
    expect(pagesScript).toContain("'owen-sound/housing'")
    expect(pagesScript).toContain("resolve(routeDirectory, 'index.html')")
  })
})
