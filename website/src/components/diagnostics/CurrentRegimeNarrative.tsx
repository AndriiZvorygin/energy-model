import { Link } from 'react-router-dom'
import type { CurrentClassification, DiagnosticCondition, RegimeScore } from '../charts/chartTypes'

const slug = (field: string) => field.toLowerCase().replaceAll('_', '-')
const sourceMonth = (date: string | null) => date?.slice(0, 7) ?? 'unavailable'
const scorePct = (value: number) => `${(100 * value).toFixed(1)}%`

function regime(classification: CurrentClassification, id: string) {
  return classification.allRegimeScores.find((item) => item.id === id)
}

function clearsThreshold(item: RegimeScore | undefined, classification: CurrentClassification) {
  return Boolean(item && item.score >= classification.provisionalClassification.decisionRules.minimumTopRegimeScore)
}

export function buildPlainLanguageSummary(classification: CurrentClassification) {
  const physical = regime(classification, 'B')
  const affordability = regime(classification, 'C')
  const production = regime(classification, 'D')
  const labour = regime(classification, 'G')
  const destruction = regime(classification, 'E')
  const collapse = regime(classification, 'F')
  const physicalSignals = physical?.supportingEvidence.map((item) => item.label).join(', ') || 'the available physical indicators'
  return [
    { label: 'Physical oil market', text: clearsThreshold(physical, classification) ? `${physicalSignals} support a physical-tightening interpretation.` : 'Physical oil indicators do not jointly clear the physical-tightening threshold.' },
    { label: 'Affordability', text: clearsThreshold(affordability, classification) ? 'Energy affordability pressure is present: oil and energy-price growth are elevated while real income and wage evidence are weak.' : 'The combined affordability evidence does not clear its regime threshold.' },
    { label: 'Production and labour', text: !clearsThreshold(production, classification) && !clearsThreshold(labour, classification) ? 'Broad production and labour transmission are not yet supported as current regimes.' : 'Some production or labour transmission evidence clears its regime threshold.' },
    { label: 'Demand and price collapse', text: !clearsThreshold(destruction, classification) && !clearsThreshold(collapse, classification) ? 'Demand destruction and price collapse are not supported by the current rule scores.' : 'Demand-destruction or price-collapse evidence currently clears its regime threshold.' },
  ]
}

function IndicatorEvidence({ item }: { item: DiagnosticCondition }) {
  return <li className="py-3"><Link to={`/current-state?indicator=${slug(item.indicator)}`} className="font-medium underline decoration-stone-300 underline-offset-2 hover:text-petroleum dark:decoration-stone-700">{item.label}</Link><p className="mt-1 text-xs leading-5 text-stone-500">{item.value === null ? 'Value unavailable' : `${item.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}${item.unit ? ` ${item.unit}` : ''}`} · expected {item.expectedDirection} · source {sourceMonth(item.sourceDate)} · strength {scorePct(item.strength)}</p></li>
}

function EvidenceColumn({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><h3 className="text-lg font-semibold">{title}</h3><div className="mt-3 border-y border-stone-200 dark:border-stone-800">{children}</div></div>
}

function RegimeEvidence({ item, classification }: { item: RegimeScore; classification: CurrentClassification }) {
  const partialFields = new Set(classification.provisionalClassification.partialPeriodIndicators.map((entry) => entry.indicator))
  const partial = item.indicatorEvidence.filter((entry) => partialFields.has(entry.indicator))
  const inactiveExpected = item.expectedSymptoms.filter((entry) => !['active', 'emerging'].includes(entry.status))
  const activeConflicts = item.conflictingSymptoms.filter((entry) => ['active', 'emerging'].includes(entry.status))
  const sourceDates = [...new Set(item.indicatorEvidence.map((entry) => entry.sourceDate).filter(Boolean))]
  const hasQualifiers = item.conflictingEvidence.length > 0 || partial.length > 0 || inactiveExpected.length > 0 || activeConflicts.length > 0 || sourceDates.length > 1
  return <div className="grid gap-8 lg:grid-cols-2">
    <EvidenceColumn title={`Evidence for ${item.name}`}><ul className="divide-y divide-stone-200 text-sm dark:divide-stone-800">{item.supportingEvidence.map((entry) => <IndicatorEvidence key={entry.indicator} item={entry} />)}{item.expectedSymptoms.filter((entry) => ['active', 'emerging'].includes(entry.status)).map((entry) => <li key={entry.id} className="py-3"><span className="font-medium">Symptom: {entry.name}</span><p className="mt-1 text-xs text-stone-500">{entry.status} · symptom score {scorePct(entry.score)}</p></li>)}</ul></EvidenceColumn>
    <EvidenceColumn title={`Evidence qualifying ${item.name}`}>{hasQualifiers ? <ul className="divide-y divide-stone-200 text-sm dark:divide-stone-800">{item.conflictingEvidence.map((entry) => <IndicatorEvidence key={entry.indicator} item={entry} />)}{partial.map((entry) => <li key={`partial-${entry.indicator}`} className="py-3"><span className="font-medium">{entry.label} is a partial-period observation</span><p className="mt-1 text-xs text-stone-500">Its {sourceMonth(entry.sourceDate)} reading is provisional until the period closes.</p></li>)}{inactiveExpected.map((entry) => <li key={entry.id} className="py-3"><span className="font-medium">Expected symptom is {entry.status.replaceAll('_', ' ')}</span><p className="mt-1 text-xs text-stone-500">{entry.name}</p></li>)}{activeConflicts.map((entry) => <li key={entry.id} className="py-3"><span className="font-medium">Conflicting symptom is {entry.status}</span><p className="mt-1 text-xs text-stone-500">{entry.name}</p></li>)}{sourceDates.length > 1 && <li className="py-3"><span className="font-medium">Observation dates differ</span><p className="mt-1 text-xs text-stone-500">This regime combines evidence dated {sourceDates.sort().map(sourceMonth).join(', ')}.</p></li>}</ul> : <p className="py-3 text-sm text-stone-500">No strong conflicting indicator is recorded in the existing evaluation.</p>}</EvidenceColumn>
  </div>
}

export function CurrentRegimeNarrative({ classification }: { classification: CurrentClassification }) {
  const summaries = buildPlainLanguageSummary(classification)
  const primary = classification.primaryRegime
  const secondary = classification.secondaryRegime
  return <section className="mt-12"><p className="text-xs font-semibold uppercase text-petroleum">Plain-language reading</p><h2 className="mt-2 text-2xl font-semibold">What the current evidence says</h2><div className="mt-5 grid gap-4 md:grid-cols-2">{summaries.map((item) => <div key={item.label} className="border-t-2 border-stone-400 pt-3"><h3 className="text-sm font-semibold">{item.label}</h3><p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">{item.text}</p></div>)}</div>
    {classification.provisionalClassification.classification.startsWith('Mixed transition:') && <div className="mt-12 space-y-12"><RegimeEvidence item={primary} classification={classification} /><RegimeEvidence item={secondary} classification={classification} /></div>}
  </section>
}
