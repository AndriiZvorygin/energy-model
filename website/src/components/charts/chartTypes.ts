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
  datasets: { id: string; file: string; legacyFile: string; title: string }[]
  indicators: { id: string; file: string; label: string; layer: string; latestDate: string; evidenceLabel: string }[]
  layers: { id: string; label: string; indicatorFields: string[]; interpretation: string; confidence: string }[]
  shared: string[]
}
