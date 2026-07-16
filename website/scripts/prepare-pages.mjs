import { copyFile, mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const websiteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const distRoot = resolve(websiteRoot, 'dist')
const routes = [
  'overview',
  'system-response',
  'current-state',
  'current-state/us',
  'canada',
  'canada/current-state',
  'canada/energy',
  'canada/economy',
  'canada/labour',
  'canada/households',
  'canada/ontario',
  'canada/regimes',
  'canada/symptoms',
  'compare/canada-us',
  'regimes',
  'symptoms',
  'indicators',
  'episodes',
  'energy-burden',
  'labour',
  'liquidity',
  'physical-market',
  'oil-prices',
  'equities',
  'economy',
  'output-quality',
  'methodology',
  'roadmap',
]

await copyFile(resolve(distRoot, 'index.html'), resolve(distRoot, '404.html'))

for (const route of routes) {
  const routeDirectory = resolve(distRoot, route)
  await mkdir(routeDirectory, { recursive: true })
  await copyFile(resolve(distRoot, 'index.html'), resolve(routeDirectory, 'index.html'))
}

console.log(`Created GitHub Pages entries for ${routes.length} routes and the 404 fallback.`)
