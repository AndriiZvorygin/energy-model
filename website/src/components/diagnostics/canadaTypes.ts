import type { DiagnosticCondition, RegimeScore, SymptomEvaluation } from '../charts/chartTypes'

export type CanadianCondition = DiagnosticCondition & {
  geography?: string
  evidenceScope?: string
  indicatorId?: string
}

export type CanadianSymptom = SymptomEvaluation & {
  statusLabel: string
  regionalContribution: Record<string, unknown>
  limitations: string[]
}

export type CanadianClock = {
  classification: string
  classificationDate: string
  generationDate: string
  requiredIndicatorAvailability: number
  freshnessAdjustedCoverage: number
  newestObservationDate: string | null
  oldestRequiredObservationDate: string | null
  observationRange: { oldest: string | null; newest: string | null }
  staleIndicators: Array<{ indicator: string; label: string; lastAvailableDate?: string }>
  missingIndicators: Array<{ indicator: string; label: string }>
  partialPeriodIndicators: Array<{ indicator: string; label: string; observationDate: string; ageMonths: number }>
  revisedDataWarning: string
  confidence: string
  margin: number
  primaryRegime: RegimeScore
  secondaryRegime: RegimeScore
  decisionRules: { minimumEvidenceCoverage: number; minimumTopRegimeScore: number; minimumMargin: number }
}

export type RegionalSide = {
  score: number
  coverage: number
  evidence: CanadianCondition[]
  conflicts: CanadianCondition[]
  missing: Array<{ indicator: string; label: string; reason?: string }>
  contractionScore?: number
}

export type RegionalDivergence = {
  status: string
  active: boolean
  date: string
  ontarioTransmission: RegionalSide
  albertaProducerConditions: RegionalSide
  explanation: string
}

export type CanadianClassification = {
  schemaVersion: number
  scope: string
  evidenceScopes: string[]
  date: string
  asOfDate: string
  status: string
  summary: string
  provisionalClassification: CanadianClock
  quarterlyAlignedClassification: CanadianClock
  primaryState: RegimeScore
  secondaryState: RegimeScore
  confidence: string
  coverage: number
  freshnessAdjustedCoverage: number
  supportingEvidence: CanadianCondition[]
  conflictingEvidence: CanadianCondition[]
  missingEvidence: CanadianCondition[]
  activeSymptoms: CanadianSymptom[]
  emergingSymptoms: CanadianSymptom[]
  regionalDivergence: RegionalDivergence
  historicalAnalogues: Array<{ episode: string; similarity: number; commonIndicators: number; comparisonDate: string }>
  limitations: string[]
}

export type CanadianSymptomPayload = {
  schemaVersion: number
  scope: string
  date: string
  generationDate: string
  clock: CanadianClock
  evaluations: CanadianSymptom[]
}

export type CanadianRegimePayload = {
  schemaVersion: number
  scope: string
  date: string
  status: string
  scores: RegimeScore[]
  decision: { classification: string; confidence: string; coverage: number; margin: number }
}
