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
const indicatorRequired = ['schemaVersion', 'id', 'label', 'description', 'unit', 'frequency', 'status', 'interpretationDirection', 'source', 'sourceUrl', 'startDate', 'endDate', 'latest', 'referenceRanges', 'observations', 'evidenceLabel']
for (const entry of manifest.indicators ?? []) {
  let indicator
  try {
    indicator = JSON.parse(await readFile(resolve(generatedRoot, entry.file), 'utf8'))
  } catch (error) {
    failures.push(`${entry.file}: ${error.message}`)
    continue
  }
  const missing = indicatorRequired.filter((field) => !(field in indicator))
  if (missing.length) failures.push(`${entry.file}: missing ${missing.join(', ')}`)
  if (indicator.schemaVersion !== 1) failures.push(`${entry.file}: unsupported indicator schema version`)
  const dates = (indicator.observations ?? []).map((row) => row.date)
  if (dates.some((date, index) => index > 0 && date <= dates[index - 1])) failures.push(`${entry.file}: dates must be strictly increasing and unique`)
  if ((indicator.observations ?? []).some((row) => row.value !== null && typeof row.value !== 'number')) failures.push(`${entry.file}: values must be numeric or null`)
  const range = indicator.referenceRanges ?? {}
  const ordered = ['minimum', 'p10', 'p25', 'historicalMedian', 'p75', 'p90', 'maximum'].map((key) => range[key]).filter((value) => value !== null && value !== undefined)
  if (ordered.some((value, index) => index > 0 && value < ordered[index - 1])) failures.push(`${entry.file}: invalid historical range ordering`)
  if (!indicator.interpretationDirection || !indicator.interpretationLabel) failures.push(`${entry.file}: missing interpretation metadata`)
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
console.log(`Validated ${manifest.datasets.length} chart datasets, ${manifest.indicators?.length ?? 0} indicators, and ${manifest.shared.length} shared files (schema ${manifest.schemaVersion}).`)
