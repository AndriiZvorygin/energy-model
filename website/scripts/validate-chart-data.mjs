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
const canadaManifest = JSON.parse(await readFile(resolve(generatedRoot, 'canada/manifest.json'), 'utf8'))
const canadaCurrentState = JSON.parse(await readFile(resolve(generatedRoot, 'canada/current-state.json'), 'utf8'))
const canadaUsComparison = JSON.parse(await readFile(resolve(generatedRoot, 'canada/canada-us-comparison.json'), 'utf8'))
const canadaClassification = JSON.parse(await readFile(resolve(generatedRoot, 'canada/current-classification.json'), 'utf8'))
const canadaSymptoms = JSON.parse(await readFile(resolve(generatedRoot, 'canada/symptom-evaluations.json'), 'utf8'))
const canadaRegimes = JSON.parse(await readFile(resolve(generatedRoot, 'canada/regime-scores.json'), 'utf8'))
const globalAffordabilityManifest = JSON.parse(await readFile(resolve(generatedRoot, 'global/manifest.json'), 'utf8'))
const usAffordabilityManifest = JSON.parse(await readFile(resolve(generatedRoot, 'us/manifest.json'), 'utf8'))
const evidenceSummary = JSON.parse(await readFile(resolve(generatedRoot, 'evidence-summary.json'), 'utf8'))
const presentationManifest = JSON.parse(await readFile(resolve(generatedRoot, 'presentation-manifest.json'), 'utf8'))
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
if (canadaManifest.defaultGeography !== 'Canada' || canadaManifest.classificationImplemented !== true || !Array.isArray(canadaManifest.indicators)) failures.push('canada/manifest.json: invalid geography or classifier status')
const canadaCore = canadaManifest.indicators.filter((item) => item.core && ['Global', 'Canada'].includes(item.geography))
if (canadaCore.length < 15 || canadaCore.length > 25) failures.push(`canada/manifest.json: expected 15-25 core indicators, received ${canadaCore.length}`)
if (canadaCurrentState.status !== 'Canadian diagnostic status: provisional transparent classification available.') failures.push('canada/current-state.json: invalid diagnostic status')
for (const dataset of canadaUsComparison.datasets ?? []) {
  if (!dataset.canadaLabel || !dataset.unitedStatesLabel) failures.push(`canada/canada-us-comparison.json: ${dataset.id} is missing country-specific labels`)
  if (dataset.canadaLabel && !/(Canada|Canadian|Bank of Canada)/.test(dataset.canadaLabel)) failures.push(`canada/canada-us-comparison.json: ${dataset.id} has an ambiguous Canadian label`)
  if (dataset.unitedStatesLabel && !/^(U\.S\.|United States)/.test(dataset.unitedStatesLabel)) failures.push(`canada/canada-us-comparison.json: ${dataset.id} has an ambiguous U.S. label`)
}
if (!canadaClassification.scope?.startsWith('Canadian energy-economic conditions') || !canadaClassification.provisionalClassification || !canadaClassification.quarterlyAlignedClassification) failures.push('canada/current-classification.json: incomplete classifier output')
if (canadaClassification.provisionalClassification?.requiredIndicatorAvailability < 0.70 || typeof canadaClassification.provisionalClassification?.freshnessAdjustedCoverage !== 'number') failures.push('canada/current-classification.json: invalid availability or freshness coverage')
if (canadaSymptoms.evaluations?.length !== 6 || canadaSymptoms.evaluations.some((item) => !allowedSymptomStatuses.has(item.status))) failures.push('canada/symptom-evaluations.json: expected six valid symptom evaluations')
const household = canadaSymptoms.evaluations?.find((item) => item.id === 'household_stress')
if (household?.status !== 'insufficient_data') failures.push('canada/symptom-evaluations.json: household stress must remain insufficient data')
if (canadaRegimes.scores?.length !== 8 || canadaRegimes.scores.some((item) => typeof item.score !== 'number' || item.score < 0 || item.score > 1)) failures.push('canada/regime-scores.json: expected eight normalized regime scores')
for (const entry of canadaManifest.indicators ?? []) {
  let indicator
  try {
    indicator = JSON.parse(await readFile(resolve(generatedRoot, 'canada', entry.file), 'utf8'))
  } catch (error) {
    failures.push(`canada/${entry.file}: ${error.message}`)
    continue
  }
  const required = ['id', 'label', 'unit', 'frequency', 'geography', 'geographyLevel', 'domesticOrExternal', 'directlyComparableAcrossCountries', 'comparisonLimitations', 'seasonalAdjustment', 'nominalOrReal', 'sourceIdentifier', 'latest', 'observations']
  const missing = required.filter((field) => !(field in indicator))
  if (missing.length) failures.push(`canada/${entry.file}: missing ${missing.join(', ')}`)
  const dates = (indicator.observations ?? []).map((row) => row.date)
  if (dates.some((date, index) => index > 0 && date <= dates[index - 1])) failures.push(`canada/${entry.file}: dates must be chronological and unique`)
  if ((indicator.observations ?? []).some((row) => !row.sourceDate)) failures.push(`canada/${entry.file}: missing source dates`)
  if (indicator.layer === 'Canadian purchasing power') {
    for (const field of ['calculation', 'components', 'futureClassifierMetadata']) {
      if (!(field in indicator)) failures.push(`canada/${entry.file}: missing purchasing-power field ${field}`)
    }
    if (indicator.futureClassifierMetadata?.status !== 'Not yet evaluated') failures.push(`canada/${entry.file}: purchasing-power classifier metadata must remain not evaluated`)
    if (indicator.frequency === 'quarterly' && dates.some((date) => !['01', '04', '07', '10'].includes(date.slice(5, 7)))) failures.push(`canada/${entry.file}: quarterly observations are not aligned to quarter starts`)
  }
}
for (const [namespace, namespaceManifest] of [['global', globalAffordabilityManifest], ['us', usAffordabilityManifest]]) {
  if (!Array.isArray(namespaceManifest.indicators) || !namespaceManifest.indicators.length) failures.push(`${namespace}/manifest.json: no indicators`)
  for (const entry of namespaceManifest.indicators ?? []) {
    let indicator
    try {
      indicator = JSON.parse(await readFile(resolve(generatedRoot, namespace, entry.file), 'utf8'))
    } catch (error) {
      failures.push(`${namespace}/${entry.file}: ${error.message}`)
      continue
    }
    const required = ['id', 'definition', 'geography', 'source', 'sourceDate', 'retrievalDate', 'revisionStatus', 'frequency', 'unit', 'seasonalAdjustment', 'nominalOrReal', 'latest', 'observations', 'transformations', 'futureClassifierMetadata']
    const missing = required.filter((field) => !(field in indicator))
    if (missing.length) failures.push(`${namespace}/${entry.file}: missing ${missing.join(', ')}`)
    const dates = (indicator.observations ?? []).map((row) => row.date)
    if (dates.some((date, index) => index > 0 && date <= dates[index - 1])) failures.push(`${namespace}/${entry.file}: dates must be chronological and unique`)
    if (indicator.futureClassifierMetadata?.status !== 'metadata_only_not_scored') failures.push(`${namespace}/${entry.file}: classifier metadata must remain inactive`)
  }
}

const evidenceStatuses = ['supporting', 'mixed', 'contradicting', 'insufficient']
const requiredEvidenceTopics = ['current_state_us', 'current_state_canada', 'regimes_us', 'regimes_canada', 'symptoms_us', 'symptoms_canada', 'affordability', 'food', 'housing', 'canada']
if (evidenceSummary.schemaVersion !== 1 || !evidenceSummary.generatedAt || !evidenceSummary.topics) failures.push('evidence-summary.json: missing schema metadata or topics')
for (const topicName of requiredEvidenceTopics) {
  const topic = evidenceSummary.topics?.[topicName]
  if (!topic?.interpretation || !topic?.confidence || !('coverage' in (topic ?? {}))) failures.push(`evidence-summary.json: incomplete topic ${topicName}`)
  for (const status of evidenceStatuses) {
    const rows = topic?.[status]
    if (!Array.isArray(rows)) {
      failures.push(`evidence-summary.json: ${topicName}.${status} must be an array`)
      continue
    }
    for (const row of rows) {
      if (!row.indicator || !row.label || row.status !== status || !row.reason || !row.group) failures.push(`evidence-summary.json: invalid ${topicName}.${status} row`)
      if (row.indicatorFile) {
        try {
          await readFile(resolve(generatedRoot, row.indicatorFile), 'utf8')
        } catch (error) {
          failures.push(`evidence-summary.json: missing indicator file ${row.indicatorFile}: ${error.message}`)
        }
      }
    }
  }
}
for (const status of evidenceStatuses) {
  if (!evidenceSummary.statusDefinitions?.[status]) failures.push(`evidence-summary.json: missing status definition ${status}`)
}
const requiredPresentationRoutes = ['/canada', '/current-state', '/canada/current-state', '/canada/regimes', '/canada/symptoms', '/current-state/us', '/regimes', '/symptoms', '/affordability', '/affordability/food', '/affordability/housing']
if (presentationManifest.schemaVersion !== 1 || !presentationManifest.refineryVersion || !presentationManifest.generatedAt || !presentationManifest.regenerationCommand) failures.push('presentation-manifest.json: incomplete refinery metadata')
if (!Array.isArray(presentationManifest.inputs) || presentationManifest.inputs.some((input) => !input.file || !/^[a-f0-9]{64}$/.test(input.sha256))) failures.push('presentation-manifest.json: invalid input provenance')
for (const route of requiredPresentationRoutes) {
  const presentation = presentationManifest.routes?.[route]
  if (!presentation?.evidenceTopic || !presentation?.interpretation || !presentation?.confidence || !presentation?.provenance?.length) failures.push(`presentation-manifest.json: incomplete route ${route}`)
  if (presentation?.evidenceTopic && !evidenceSummary.topics?.[presentation.evidenceTopic]) failures.push(`presentation-manifest.json: ${route} references missing topic ${presentation.evidenceTopic}`)
  if ((presentation?.evidenceCounts?.insufficient ?? 0) > 0 && presentationManifest.policy?.excludeStatusesFromDiagnosticSummary?.includes('insufficient') !== true) failures.push(`presentation-manifest.json: ${route} exposes insufficient evidence without an explicit policy`)
}

if (failures.length) {
  throw new Error(`Chart-data validation failed:\n- ${failures.join('\n- ')}`)
}
console.log(`Validated ${manifest.datasets.length} chart datasets, ${manifest.indicators?.length ?? 0} indicators, and ${manifest.shared.length} shared files (schema ${manifest.schemaVersion}).`)
