import { PublicationFigure } from '../components/charts/PublicationFigure'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import type { CurrentClassification, RegimeHistoryPayload } from '../components/charts/chartTypes'
import { useGeneratedJson } from '../components/charts/useChartData'
import { ClassificationSummary } from '../components/diagnostics/ClassificationSummary'
import { CurrentRegimeNarrative } from '../components/diagnostics/CurrentRegimeNarrative'
import { GeneratedRouteEvidenceSummary } from '../components/diagnostics/GeneratedRouteEvidenceSummary'
import { RegimeHistoryChart } from '../components/diagnostics/RegimeHistoryChart'
import { RegimeScoreChart } from '../components/diagnostics/RegimeScoreChart'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'

export function Regimes() {
  const { data: current, error } = useGeneratedJson<CurrentClassification>('current-classification.json')
  const { data: history } = useGeneratedJson<RegimeHistoryPayload>('regime-history.json')
  return <><PageHeader eyebrow="Live classification and historical framework" title="Current regime evidence" description="A transparent rule classifier compares the latest evidence with eight documented states. It can return mixed or unclassified when coverage, score, or separation is inadequate." /><PageBody>
    {error && <p className="border-y border-amber-500 py-4 text-sm text-amber-700 dark:text-amber-300">{error}</p>}
    {!current ? <p className="py-20 text-sm text-stone-500">Loading current classification…</p> : <>
      <GeneratedRouteEvidenceSummary title="Current regime evidence map" />
      <div className="mt-8">
      <ClassificationSummary classification={current} />
      </div>
      <CurrentRegimeNarrative classification={current} />
      <section className="mt-12"><p className="text-xs font-semibold uppercase text-petroleum">Candidate comparison</p><h2 className="mt-2 text-2xl font-semibold">All regime scores</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-500">The leading score is a candidate, not automatically the published classification. Coverage must reach 70%, the leading score 60%, and the margin over second place 10 percentage points.</p><div className="mt-6"><RegimeScoreChart scores={current.allRegimeScores} /></div></section>
      <section className="mt-12"><h2 className="text-xl font-semibold">Historical analogues</h2><p className="mt-2 text-sm text-stone-500">Similarity compares available indicator percentiles at historical episode endpoints. It supports comparison, not causal identification.</p><div className="mt-4 grid gap-4 md:grid-cols-3">{current.historicalAnalogues.map((item) => <div key={item.episode} className="border-t-2 border-stone-400 pt-3"><p className="font-semibold">{item.episode}</p><p className="mt-2 text-sm text-stone-500">Similarity {(item.similarity * 100).toFixed(0)}% across {item.commonIndicators} common indicators · comparison {item.comparisonDate.slice(0, 7)}</p></div>)}</div></section>
    </>}
    {history && <section className="mt-14"><p className="text-xs font-semibold uppercase text-petroleum">Walk-forward robustness</p><h2 className="mt-2 text-2xl font-semibold">How candidate scores changed through history</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-500">Each quarter uses observations available on or before that evaluation date and expanding historical percentiles. It uses revised data, so it is retrospective rather than a reconstruction of every original release vintage.</p><div className="mt-6"><RegimeHistoryChart history={history} /></div><div className="mt-7 grid gap-4 border-y border-stone-300 py-5 text-sm sm:grid-cols-2 xl:grid-cols-4 dark:border-stone-700"><div><p className="text-stone-500">Unclassified quarters</p><p className="mt-1 text-xl font-semibold">{(100 * Number(history.validation.unclassifiedRate)).toFixed(0)}%</p></div><div><p className="text-stone-500">Quarter-to-quarter stability</p><p className="mt-1 text-xl font-semibold">{(100 * Number(history.validation.transitionStability)).toFixed(0)}%</p></div><div><p className="text-stone-500">Control-period stress flags</p><p className="mt-1 text-xl font-semibold">{(100 * Number(history.validation.controlPeriodStressFlagRate)).toFixed(0)}%</p></div><div><p className="text-stone-500">Event-period misses</p><p className="mt-1 text-xl font-semibold">{(100 * Number(history.validation.eventPeriodMissRate)).toFixed(0)}%</p></div></div><p className="mt-3 text-xs leading-5 text-stone-500">These diagnostics show that the classifier is experimental and revision-prone. Control and event windows are descriptive checks, not independently labelled truth, so they are not formal false-positive or false-negative rates.</p></section>}
    <section className="mt-14"><p className="text-xs font-semibold uppercase text-petroleum">Framework states</p><h2 className="mt-2 text-2xl font-semibold">How a system can move through stress and recovery</h2><div className="mt-4 max-w-4xl"><ResearchText text={researchData.systemResponse.content.regimes} /></div></section>
    <section className="mt-10"><p className="text-xs font-semibold uppercase text-petroleum">Historical diagnostic</p><h2 className="mt-2 text-2xl font-semibold">Demand-destruction patterns across past observations</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">This historical chart supplies context for the classifier. Event labels identify comparison windows and are not proof of causation.</p><div className="mt-6"><ResearchTimeSeriesChart file="demand-destruction.json" initialTransformation="zscore" inspectCrossLayer /></div></section>
    <div className="mt-12 space-y-6"><PublicationFigure src="/charts/regime_timeline.png" alt="Timeline of historical energy and economic regimes" title="Historical regime timeline" description="Episode boundaries provide comparison windows for the live evidence." source="Project-defined historical episodes using EIA, FRED, BEA and BLS observations." /><PublicationFigure src="/charts/demand_destruction_cycle.png" alt="Demand destruction sequence around oil price peaks" title="Demand destruction cycle" description="A falling oil price can be part of worsening conditions when activity and demand are contracting." source="WTI, petroleum consumption, industrial production and NBER recession periods." /></div>
  </PageBody></>
}
