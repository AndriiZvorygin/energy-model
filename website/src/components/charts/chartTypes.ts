export type Transformation = 'raw' | 'yoy' | 'indexed' | 'zscore' | 'pct_change'

export type ChartSeries = {
  key: string
  label: string
  unit: string
  source: string
  status: 'measured' | 'derived' | 'modelled' | 'experimental'
  defaultVisible: boolean
  finalObservationDate: string | null
  frequency?: string | null
  color?: string | null
  transformations?: Transformation[]
}

export type ChartObservation = {
  date: string
  [key: string]: string | number | null
}

export type ChartCalculation = {
  formula: string
  explanation: string
  example: string
}

export type TransformationMetadata = {
  type: 'raw' | 'yoy' | 'indexed' | 'zscore'
  referenceStart: string | null
  referenceEnd: string | null
  mean: number | null
  standardDeviation: number | null
  statistics?: Record<string, { mean: number | null; standardDeviation: number | null; n: number }>
}

export type ChartDataset = {
  schemaVersion: string
  id: string
  title: string
  description: string
  plainLanguageSummary: string
  howToRead: string
  calculation: ChartCalculation
  patternsToWatch: string[]
  limitations: string[]
  sourceNotes: string[]
  transformation: TransformationMetadata
  frequency: 'monthly' | 'quarterly' | 'annual'
  dateRange: { start: string | null; end: string | null }
  series: ChartSeries[]
  observations: ChartObservation[]
  annotations: string[]
  availableTransformations: Transformation[]
  evidenceLabel: string
  methodology: Record<string, unknown>
  staticFigure: string
  generatedAt: string
}

export type ChartEvent = {
  id: string
  name: string
  start: string
  end: string
  category: string
  explanation: string
  layers: string[]
}

export type ChartRegime = {
  id: string
  label: string
  start: string
  end: string
  color: string
}

export type ChartState = {
  series: string[]
  transformation: Transformation
  range: string
  from?: string
  to?: string
  lag?: number
}

export type IndicatorObservation = { date: string; value: number | null }

export type IndicatorDataset = {
  schemaVersion: 1
  id: string
  field: string
  label: string
  description: string
  unit: string
  frequency: string
  status: string
  layer: string
  interpretationDirection: 'higher-generally-supportive' | 'higher-generally-stressful' | 'context-dependent'
  interpretationLabel: 'Supportive' | 'Neutral' | 'Stressful' | 'Mixed' | 'Historically elevated' | 'Historically depressed' | 'Direction unclear'
  interpretation: string
  source: string
  sourceUrl: string
  startDate: string
  endDate: string
  latest: {
    date: string
    value: number
    previousValue: number | null
    oneYearChange: number | null
    threeMonthChange: number | null
    fourQuarterChange: number | null
    historicalPercentile: number | null
    percentileSince2000: number | null
    distanceFromMedian: number | null
    momentum: string
  }
  referenceRanges: {
    historicalMedian: number | null
    p10: number | null
    p25: number | null
    p75: number | null
    p90: number | null
    minimum: number | null
    maximum: number | null
  }
  observations: IndicatorObservation[]
  confirmingIndicators: string[]
  conflictingIndicators: string[]
  evidenceChecks: Array<{
    label: string
    status: 'confirms' | 'conflicts' | 'unclear'
    targetIndicatorId: string | null
    targetInterpretationLabel: IndicatorDataset['interpretationLabel'] | null
    targetLatestDate: string | null
    explanation: string
  }>
  confidenceLevel: string
  evidenceLabel: string
  calculation: ChartCalculation
  limitations: string[]
  generatedAt: string
}

export type GeneratedManifest = {
  schemaVersion: string
  indicatorSchemaVersion: number
  generatedAt: string
  currentState: {
    asOf: string
    latestObservationDate: string
    oldestLatestObservationDate: string
    classificationMethod: string
    anomalyMethod: string
    groups: Record<'supportive' | 'stressful' | 'other', Array<{
      id: string
      field: string
      label: string
      layer: string
      interpretationLabel: IndicatorDataset['interpretationLabel']
      latestDate: string
      historicalPercentile: number | null
      anomalyScore: number | null
    }>>
    indicatorOrder: string[]
  }
  datasets: { id: string; file: string; legacyFile: string; title: string }[]
  indicators: { id: string; file: string; label: string; layer: string; latestDate: string; evidenceLabel: string }[]
  layers: { id: string; label: string; indicatorFields: string[]; interpretation: string; confidence: string }[]
  shared: string[]
}

export type DiagnosticCondition = {
  indicator: string
  label: string
  transformation: string
  expectedDirection: string
  group: string
  available: boolean
  met: boolean
  strength: number
  value: number | null
  unit: string | null
  historicalPercentile: number | null
  sourceDate: string | null
  metricValue?: number | null
  threshold?: number | null
}

export type SymptomEvaluation = {
  id: string
  name: string
  plainLanguageMeaning: string
  status: 'active' | 'emerging' | 'fading' | 'inactive' | 'insufficient_data'
  score: number
  evaluationDate: string
  confidence: string
  coverage: number
  requiredConditionResults: DiagnosticCondition[]
  confirmingEvidence: DiagnosticCondition[]
  conflictingEvidence: DiagnosticCondition[]
  missingEvidence: DiagnosticCondition[]
  persistence: { consecutiveUpdates: number; requiredForActive: number; updateStepMonths: number }
  historicalAnalogues: string[]
  alternativeExplanations: string[]
  evidenceLabel: string
  sensitivity: Record<string, string>
  rule: Record<string, unknown>
}

export type RegimeScore = {
  id: string
  name: string
  score: number
  coverage: number
  layerScores: Record<string, { score: number; coverage: number }>
  supportingEvidence: DiagnosticCondition[]
  conflictingEvidence: DiagnosticCondition[]
  missingEvidence: DiagnosticCondition[]
}

export type ClassificationClock = {
  classification: string
  classificationDate: string
  generationDate: string
  newestObservationDate: string | null
  oldestRequiredObservationDate: string | null
  coverage: number
  status: string
  dataVintageStatus: string
  dataVintageWarning: string
  partialPeriodIndicators: Array<{ indicator: string; label: string; sourceDate: string }>
  confidence: string
  primaryRegime: RegimeScore
  secondaryRegime: RegimeScore
}

export type CurrentClassification = {
  schemaVersion: number
  scope: string
  classificationDate: string
  asOfDate: string
  provisionalClassification: ClassificationClock
  confirmedClassification: ClassificationClock
  primaryRegime: RegimeScore
  secondaryRegime: RegimeScore
  confidence: string
  evidenceCoverage: number
  allRegimeScores: RegimeScore[]
  activeSymptoms: SymptomEvaluation[]
  emergingSymptoms: SymptomEvaluation[]
  fadingSymptoms: SymptomEvaluation[]
  supportingIndicators: DiagnosticCondition[]
  conflictingIndicators: DiagnosticCondition[]
  staleIndicators: Array<{ indicator: string; label: string; lastAvailableDate?: string }>
  missingIndicators: Array<{ indicator: string; label: string }>
  historicalAnalogues: Array<{ episode: string; similarity: number; commonIndicators: number; comparisonDate: string }>
  ruleVersion: Record<string, string>
  dataVintageWarning: string
  monthlyPersistence: { consecutiveUpdates: number; requiredUpdates: number; confirmationStatus: string; note: string }
  exceptionalTransition: { fromRegime: string; toRegime: string; reasonRequired: boolean; documentedJumpConditions: string[]; note: string } | null
}

export type SymptomEvaluationsPayload = {
  schemaVersion: number
  scope: string
  generationDate: string
  clock: ClassificationClock
  thresholdSensitivity: Record<string, { classification: string; topScore: number }>
  evaluations: SymptomEvaluation[]
}

export type RegimeHistoryPayload = {
  schemaVersion: number
  scope: string
  frequency: string
  generatedAt: string
  rows: Array<{ date: string; classification: string; primaryRegimeId: string; primaryRegime: string; secondaryRegimeId: string; confidence: string; coverage: number; scores: Record<string, number>; activeSymptoms: string[] }>
  validation: Record<string, unknown>
}
