import { copyFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const websiteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')

await copyFile(resolve(websiteRoot, 'dist/index.html'), resolve(websiteRoot, 'dist/404.html'))
console.log('Created dist/404.html for GitHub Pages route fallback.')
