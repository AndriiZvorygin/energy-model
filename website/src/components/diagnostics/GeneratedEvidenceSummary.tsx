import { useMemo } from 'react'
import { useGeneratedJson, useIndicatorDatasets } from '../charts/useChartData'
import type { EvidenceDisposition, EvidenceMatrixRow } from './EvidenceMatrix'
import { EvidenceMatrix } from './EvidenceMatrix'

type GeneratedEvidenceRow = {
  indicator: string
  label: string
  status: 'supporting' | 'mixed' | 'contradicting' | 'insufficient'
  reason: string
  chart: string | null
  indicatorFile: string | null
  group: string
  value: number | null
  unit: string | null
  historicalPercentile: number | null
  direction: string | null
  sourceDate: string | null
  calculation: string | null
  limitations: string[]
}
type GeneratedTopic = {
  topic: string
  interpretation: string
  confidence: string
  coverage: number | null
  scope: string | null
  supporting: GeneratedEvidenceRow[]
  mixed: GeneratedEvidenceRow[]
  contradicting: GeneratedEvidenceRow[]
  insufficient: GeneratedEvidenceRow[]
}
type EvidenceSummaryPayload = { schemaVersion: number; generatedAt: string; evidence: Record<string, GeneratedTopic> }

const disposition: Record<GeneratedEvidenceRow['status'], EvidenceDisposition> = {
  supporting: 'supports', mixed: 'mixed', contradicting: 'contradicts', insufficient: 'insufficient',
}

export function GeneratedEvidenceSummary({ evidenceKey, title = 'Diagnostic summary', includeStatuses = ['supporting', 'mixed', 'contradicting', 'insufficient'] }: { evidenceKey: string; title?: string; includeStatuses?: GeneratedEvidenceRow['status'][] }) {
  const { data, error } = useGeneratedJson<EvidenceSummaryPayload>('evidence-summary.json')
  const selected = data?.evidence[evidenceKey]
  const generatedRows = useMemo(() => selected ? includeStatuses.flatMap((status) => selected[status]) : [], [includeStatuses, selected])
  const files = useMemo(() => [...new Set(generatedRows.map((row) => row.indicatorFile).filter((file): file is string => Boolean(file)))], [generatedRows])
  const { indicators, error: indicatorError } = useIndicatorDatasets(files)
  const byFile = useMemo(() => new Map(files.map((file, index) => [file, indicators[index]])), [files, indicators])
  const rows: EvidenceMatrixRow[] = useMemo(() => generatedRows.map((row, index) => ({
    id: `${evidenceKey}-${row.indicator}-${index}`, label: row.label, disposition: disposition[row.status],
    status: `${row.group} · ${row.status}`, reason: row.reason,
    indicator: row.indicatorFile ? byFile.get(row.indicatorFile) : undefined,
    value: row.value, unit: row.unit, percentile: row.historicalPercentile, direction: row.direction,
    sourceDate: row.sourceDate, calculation: row.calculation, limitations: row.limitations,
  })), [byFile, evidenceKey, generatedRows])
  if (error || indicatorError) return <p className="border-y border-amber-500 py-4 text-sm text-amber-700">Diagnostic summary unavailable: {error ?? indicatorError}</p>
  if (!selected) return <p className="border-y border-stone-300 py-6 text-sm text-stone-500 dark:border-stone-700">Loading diagnostic summary…</p>
  return <EvidenceMatrix title={title} interpretation={selected.interpretation} confidence={selected.confidence} coverage={selected.coverage} rows={rows} />
}
