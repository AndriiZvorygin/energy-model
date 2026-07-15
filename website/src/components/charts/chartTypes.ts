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
