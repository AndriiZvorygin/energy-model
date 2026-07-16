import { readFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const websiteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const generatedRoot = resolve(websiteRoot, 'public/generated')
const manifest = JSON.parse(await readFile(resolve(generatedRoot, 'manifest.json'), 'utf8'))

const requiredMetadata = ['schemaVersion', 'id', 'title', 'description', 'plainLanguageSummary', 'howToRead', 'calculation', 'patternsToWatch', 'limitations', 'sourceNotes', 'transformation', 'frequency', 'dateRange', 'series', 'observations', 'methodology', 'generatedAt', 'evidenceLabel']
const failures = []

if (!manifest.schemaVersion || !Array.isArray(manifest.datasets) || !manifest.datasets.length) failures.push('manifest.json is missing schemaVersion or datasets')
if (!manifest.currentState?.asOf || !manifest.currentState?.latestObservationDate || !manifest.currentState?.oldestLatestObservationDate) failures.push('manifest.json is missing current-state as-of metadata')
if (!manifest.currentState?.classificationMethod || !manifest.currentState?.anomalyMethod) failures.push('manifest.json is missing current-state methodology')
for (const group of ['supportive', 'stressful', 'other']) {
  const entries = manifest.currentState?.groups?.[group]
  if (!Array.isArray(entries)) failures.push(`manifest.json is missing current-state group ${group}`)
  if ((entries ?? []).some((entry) => !entry.id || !entry.field || !entry.label || !entry.latestDate || !entry.interpretationLabel)) failures.push(`manifest.json has incomplete current-state ${group} entries`)
  const scores = (entries ?? []).map((entry) => entry.anomalyScore).filter((score) => score !== null)
  if (scores.some((score, index) => index > 0 && score > scores[index - 1])) failures.push(`manifest.json current-state ${group} entries are not ordered by anomaly`)
}
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
const indicatorRequired = ['schemaVersion', 'id', 'label', 'description', 'unit', 'frequency', 'status', 'interpretationDirection', 'source', 'sourceUrl', 'startDate', 'endDate', 'latest', 'referenceRanges', 'observations', 'evidenceLabel', 'evidenceChecks']
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
  if ((indicator.evidenceChecks ?? []).some((check) => !check.label || !['confirms', 'conflicts', 'unclear'].includes(check.status) || !check.explanation)) failures.push(`${entry.file}: invalid evidence check`)
}
for (const file of manifest.shared ?? []) {
  try {
    await readFile(resolve(generatedRoot, file), 'utf8')
  } catch (error) {
    failures.push(`${file}: ${error.message}`)
  }
}

const currentClassification = JSON.parse(await readFile(resolve(generatedRoot, 'current-classification.json'), 'utf8'))
const symptomEvaluations = JSON.parse(await readFile(resolve(generatedRoot, 'symptom-evaluations.json'), 'utf8'))
const regimeScores = JSON.parse(await readFile(resolve(generatedRoot, 'regime-scores.json'), 'utf8'))
const regimeHistory = JSON.parse(await readFile(resolve(generatedRoot, 'regime-history.json'), 'utf8'))
const requiredCurrent = ['scope', 'classificationDate', 'asOfDate', 'provisionalClassification', 'confirmedClassification', 'primaryRegime', 'secondaryRegime', 'confidence', 'evidenceCoverage', 'allRegimeScores', 'activeSymptoms', 'emergingSymptoms', 'fadingSymptoms', 'supportingIndicators', 'conflictingIndicators', 'staleIndicators', 'missingIndicators', 'historicalAnalogues', 'ruleVersion', 'dataVintageWarning']
const missingCurrent = requiredCurrent.filter((field) => !(field in currentClassification))
if (missingCurrent.length) failures.push(`current-classification.json: missing ${missingCurrent.join(', ')}`)
if (!currentClassification.scope?.includes('United States energy-economic conditions')) failures.push('current-classification.json: missing formal classification scope')
for (const clock of ['provisionalClassification', 'confirmedClassification']) {
  const value = currentClassification[clock]
  if (!value?.classificationDate || !value?.classification || typeof value.coverage !== 'number') failures.push(`current-classification.json: incomplete ${clock}`)
}
const allowedSymptomStatuses = new Set(['active', 'emerging', 'fading', 'inactive', 'insufficient_data'])
if (symptomEvaluations.evaluations?.length !== 6) failures.push('symptom-evaluations.json: expected six documented symptoms')
for (const symptom of symptomEvaluations.evaluations ?? []) {
  if (!symptom.id || !allowedSymptomStatuses.has(symptom.status) || !symptom.evaluationDate || !Array.isArray(symptom.requiredConditionResults)) failures.push(`symptom-evaluations.json: invalid evaluation ${symptom.id ?? '<unknown>'}`)
}
if (regimeScores.scores?.length !== 8 || regimeScores.scores.some((row) => typeof row.score !== 'number' || row.score < 0 || row.score > 1)) failures.push('regime-scores.json: expected eight normalized scores')
const regimeDates = (regimeHistory.rows ?? []).map((row) => row.date)
if (!regimeDates.length || regimeDates.some((date, index) => index > 0 && date <= regimeDates[index - 1])) failures.push('regime-history.json: dates must be strictly increasing and unique')

if (failures.length) {
  throw new Error(`Chart-data validation failed:\n- ${failures.join('\n- ')}`)
}
console.log(`Validated ${manifest.datasets.length} chart datasets, ${manifest.indicators?.length ?? 0} indicators, and ${manifest.shared.length} shared files (schema ${manifest.schemaVersion}).`)
