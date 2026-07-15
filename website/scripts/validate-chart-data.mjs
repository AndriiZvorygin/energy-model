import { readFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const websiteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const generatedRoot = resolve(websiteRoot, 'public/generated')
const manifest = JSON.parse(await readFile(resolve(generatedRoot, 'manifest.json'), 'utf8'))

const requiredMetadata = ['schemaVersion', 'id', 'title', 'description', 'plainLanguageSummary', 'howToRead', 'calculation', 'patternsToWatch', 'limitations', 'sourceNotes', 'transformation', 'frequency', 'dateRange', 'series', 'observations', 'methodology', 'generatedAt', 'evidenceLabel']
const failures = []

if (!manifest.schemaVersion || !Array.isArray(manifest.datasets) || !manifest.datasets.length) failures.push('manifest.json is missing schemaVersion or datasets')
for (const entry of manifest.datasets ?? []) {
  let dataset
  try {
    dataset = JSON.parse(await readFile(resolve(generatedRoot, entry.file), 'utf8'))
  } catch (error) {
    failures.push(`${entry.file}: ${error.message}`)
    continue
  }
  const missing = requiredMetadata.filter((field) => !(field in dataset))
  if (missing.length) failures.push(`${entry.file}: missing ${missing.join(', ')}`)
  if (!dataset.calculation?.formula || !dataset.calculation?.explanation || !dataset.calculation?.example) failures.push(`${entry.file}: incomplete calculation metadata`)
  if (!dataset.transformation?.referenceStart || !dataset.transformation?.referenceEnd) failures.push(`${entry.file}: missing fixed transformation reference period`)
  const keys = new Set()
  for (const series of dataset.series ?? []) {
    if (!series.key || !series.label || !series.unit || !series.source || !series.status || !series.finalObservationDate) failures.push(`${entry.file}: incomplete series metadata for ${series.key ?? '<unknown>'}`)
    if (keys.has(series.key)) failures.push(`${entry.file}: duplicate series key ${series.key}`)
    keys.add(series.key)
  }
  const dates = (dataset.observations ?? []).map((row) => row.date)
  if (dates.some((date) => !/^\d{4}-\d{2}-\d{2}$/.test(date))) failures.push(`${entry.file}: non-ISO observation date`)
  if (dates.some((date, index) => index > 0 && date <= dates[index - 1])) failures.push(`${entry.file}: dates must be strictly increasing and unique`)
}
for (const file of manifest.shared ?? []) {
  try {
    await readFile(resolve(generatedRoot, file), 'utf8')
  } catch (error) {
    failures.push(`${file}: ${error.message}`)
  }
}

if (failures.length) {
  throw new Error(`Chart-data validation failed:\n- ${failures.join('\n- ')}`)
}
console.log(`Validated ${manifest.datasets.length} chart datasets and ${manifest.shared.length} shared files (schema ${manifest.schemaVersion}).`)
