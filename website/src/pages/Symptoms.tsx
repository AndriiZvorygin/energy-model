import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { EvidenceLabel } from '../components/EvidenceLabel'
import { LayerHistoryChart } from '../components/charts/LayerHistoryChart'
import type { DiagnosticCondition, IndicatorDataset, SymptomEvaluationsPayload } from '../components/charts/chartTypes'
import { useGeneratedJson, useGeneratedManifest, useIndicatorDatasets } from '../components/charts/useChartData'
import { PageBody, PageHeader } from '../components/PageHeader'

const statusTone: Record<string, string> = {
  active: 'border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200',
  emerging: 'border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200',
  fading: 'border-sky-500 bg-sky-50 text-sky-800 dark:bg-sky-950/40 dark:text-sky-200',
  inactive: 'border-stone-400 bg-stone-50 text-stone-700 dark:bg-stone-900 dark:text-stone-200',
  insufficient_data: 'border-stone-400 bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-300',
}
const pretty = (value: string) => value.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase())
const month = (value: string) => new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))

function Conditions({ title, rows, idByField }: { title: string; rows: DiagnosticCondition[]; idByField: Map<string, string> }) {
  return <div><h4 className="text-sm font-semibold">{title}</h4>{rows.length ? <ul className="mt-2 divide-y divide-stone-200 border-y border-stone-200 text-sm dark:divide-stone-800 dark:border-stone-800">{rows.map((row) => {
    const symbol = !row.available ? '~' : row.met ? '✓' : '×'
    const id = idByField.get(row.indicator)
    return <li key={`${row.indicator}-${row.transformation}`} className="grid gap-2 py-3 sm:grid-cols-[28px_1fr_auto]"><span className={`font-bold ${symbol === '✓' ? 'text-emerald-700 dark:text-emerald-300' : symbol === '×' ? 'text-rose-700 dark:text-rose-300' : 'text-stone-500'}`}>{symbol}</span><div>{id ? <Link className="font-medium underline decoration-stone-300 underline-offset-2 hover:text-petroleum" to={`/current-state/us?indicator=${id}`}>{row.label}</Link> : <span className="font-medium">{row.label}</span>}<p className="mt-1 text-xs text-stone-500">{pretty(row.transformation)} · expected {row.expectedDirection} · source {row.sourceDate?.slice(0, 7) ?? 'missing'}</p></div><span className="text-xs text-stone-500">{row.historicalPercentile === null ? 'n/a' : `P${row.historicalPercentile.toFixed(0)}`}</span></li>
  })}</ul> : <p className="mt-2 text-sm text-stone-500">None recorded.</p>}</div>
}

export function Symptoms() {
  const { data, error } = useGeneratedJson<SymptomEvaluationsPayload>('symptom-evaluations.json')
  const { manifest } = useGeneratedManifest()
  const files = useMemo(() => manifest?.indicators.map((item) => item.file) ?? [], [manifest])
  const { indicators } = useIndicatorDatasets(files)
  const byField = useMemo(() => new Map(indicators.map((item) => [item.field, item])), [indicators])
  const idByField = useMemo(() => new Map(indicators.map((item) => [item.field, item.id])), [indicators])
  if (error) return <><PageHeader eyebrow="Live diagnostic" title="Symptom evaluation" description="The generated evaluation could not be loaded." /><PageBody><p>{error}</p></PageBody></>
  return <><PageHeader eyebrow="Live diagnostic" title="Which documented symptoms are showing now?" description="Each status is evaluated from version-controlled rules and refreshed indicator histories. It is evidence about a pattern, not proof of a cause." /><PageBody>{!data ? <p className="py-20 text-sm text-stone-500">Loading symptom evaluations…</p> : <>
    <section className="border-y border-stone-300 py-5 text-sm dark:border-stone-700"><p><strong>Scope:</strong> {data.scope}</p><p className="mt-2 text-stone-500">Evaluation date {month(data.clock.classificationDate)} · generated {new Date(data.generationDate).toLocaleDateString()} · coverage {(data.clock.coverage * 100).toFixed(0)}% · retrospective revised data</p></section>
    <div className="mt-10 space-y-10">{data.evaluations.map((item) => {
      const fields = [...new Set([...item.requiredConditionResults, ...item.confirmingEvidence, ...item.conflictingEvidence].map((row) => row.indicator))]
      const chartIndicators = fields.map((field) => byField.get(field)).filter((indicator): indicator is IndicatorDataset => Boolean(indicator))
      return <article key={item.id} className="border-t border-stone-300 pt-6 dark:border-stone-700"><div className="flex flex-wrap items-start justify-between gap-4"><div><span className={`inline-flex border-l-4 px-3 py-1 text-xs font-semibold uppercase ${statusTone[item.status]}`}>{pretty(item.status)}</span><h2 className="mt-3 text-2xl font-semibold">{item.name}</h2></div><EvidenceLabel label={item.evidenceLabel} /></div><p className="mt-3 max-w-4xl leading-7 text-stone-700 dark:text-stone-300">{item.plainLanguageMeaning}</p><div className="mt-4 flex flex-wrap gap-5 text-xs text-stone-500"><span>Evaluation {month(item.evaluationDate)}</span><span>Confidence {item.confidence}</span><span>Coverage {(item.coverage * 100).toFixed(0)}%</span><span>Persistence {item.persistence.consecutiveUpdates}/{item.persistence.requiredForActive} updates</span><span>Score {(item.score * 100).toFixed(0)}%</span></div>
        <details className="mt-6 border-y border-stone-200 py-4 dark:border-stone-800"><summary className="cursor-pointer font-semibold">Evidence, history, and rule details</summary><div className="mt-6 space-y-7"><Conditions title="Required evidence" rows={item.requiredConditionResults} idByField={idByField} /><div className="grid gap-7 lg:grid-cols-2"><Conditions title="Confirming evidence currently met" rows={item.confirmingEvidence} idByField={idByField} /><Conditions title="Conflicting evidence currently met" rows={item.conflictingEvidence} idByField={idByField} /></div>{chartIndicators.length > 0 && <div><h4 className="text-sm font-semibold">Interactive indicator history</h4><LayerHistoryChart indicators={chartIndicators} /></div>}<div className="grid gap-7 text-sm lg:grid-cols-3"><div><h4 className="font-semibold">Historical analogues</h4><p className="mt-2 text-stone-500">{item.historicalAnalogues.join(', ') || 'None documented'}</p></div><div><h4 className="font-semibold">Alternative explanations</h4><ul className="mt-2 space-y-1 text-stone-500">{item.alternativeExplanations.map((text) => <li key={text}>{text}</li>)}</ul></div><div><h4 className="font-semibold">Threshold sensitivity</h4><ul className="mt-2 space-y-1 text-stone-500">{Object.entries(item.sensitivity).map(([threshold, status]) => <li key={threshold}>{threshold}: {pretty(status)}</li>)}</ul></div></div><details><summary className="cursor-pointer text-sm font-semibold">Machine-readable rule</summary><pre className="mt-3 overflow-x-auto bg-stone-100 p-4 text-xs dark:bg-stone-900">{JSON.stringify(item.rule, null, 2)}</pre></details></div></details>
      </article>
    })}</div>
  </>}</PageBody></>
}
