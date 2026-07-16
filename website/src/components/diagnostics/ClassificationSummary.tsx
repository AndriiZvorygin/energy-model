import type { ClassificationClock, CurrentClassification } from '../charts/chartTypes'

const month = (value: string | null) => value ? new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value.slice(0, 10)}T00:00:00Z`)) : 'Unavailable'
const pct = (value: number) => `${(100 * value).toFixed(0)}%`

function Clock({ title, clock }: { title: string; clock: ClassificationClock }) {
  const unclassified = clock.classification === 'Unclassified'
  return <article className="border-t-2 border-petroleum pt-4">
    <p className="text-xs font-semibold uppercase text-stone-500">{title}</p>
    <h3 className={`mt-2 text-xl font-semibold ${unclassified ? 'text-amber-700 dark:text-amber-300' : ''}`}>{clock.classification}</h3>
    {title === 'Quarterly-aligned state' && clock.dataVintageStatus === 'retrospective_revised_data' && <p className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-300">Retrospective quarterly classification using revised data</p>}
    <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
      <div><dt className="text-stone-500">Classification date</dt><dd className="font-medium">{month(clock.classificationDate)}</dd></div>
      <div><dt className="text-stone-500">Confidence</dt><dd className="font-medium capitalize">{clock.confidence}</dd></div>
      <div><dt className="text-stone-500">Required-indicator availability</dt><dd className="font-medium">{pct(clock.coverage)}</dd></div>
      <div><dt className="text-stone-500">Observation range</dt><dd className="font-medium">{month(clock.oldestRequiredObservationDate)} to {month(clock.newestObservationDate)}</dd></div>
      <div><dt className="text-stone-500">Stale indicators</dt><dd className="font-medium">{clock.staleIndicators.length}</dd></div>
      <div><dt className="text-stone-500">Partial-period indicators</dt><dd className="font-medium">{clock.partialPeriodIndicators.length}</dd></div>
    </dl>
  </article>
}

export function ClassificationSummary({ classification, compact = false }: { classification: CurrentClassification; compact?: boolean }) {
  const clock = classification.provisionalClassification
  const topScore = clock.primaryRegime.score
  const threshold = clock.decisionRules.minimumTopRegimeScore
  const closeScores = clock.margin < clock.decisionRules.minimumMargin
  const preferredTransitionWording = Boolean(classification.exceptionalTransition && classification.exceptionalTransition.fromRegime === 'Energy affordability stress' && classification.exceptionalTransition.toRegime === 'Physical tightening' && clock.classification.startsWith('Mixed transition:') && clock.secondaryRegime.id === 'C')
  return <section className="border-y border-stone-300 py-6 dark:border-stone-700">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-petroleum">Current diagnostic interpretation · Experimental transparent classifier</p><h2 className="mt-2 text-2xl font-semibold">Two clocks, one transparent evidence set</h2></div><p className="max-w-md text-xs leading-5 text-stone-500"><strong className="text-ink dark:text-white">Scope:</strong> {classification.scope}</p></div>
    <div className={`mt-6 grid gap-7 ${compact ? 'lg:grid-cols-2' : 'xl:grid-cols-2'}`}><Clock title="Provisional monthly nowcast" clock={clock} /><Clock title="Quarterly-aligned state" clock={classification.confirmedClassification} /></div>
    <div className="mt-6 border-t border-stone-200 pt-5 dark:border-stone-800"><h3 className="text-sm font-semibold">Why confidence is {clock.confidence}</h3><ul className="mt-3 grid gap-2 text-sm leading-6 text-stone-600 md:grid-cols-2 dark:text-stone-300"><li>The top score, {pct(topScore)}, exceeds the {pct(threshold)} classification threshold.</li><li>{closeScores ? `The top two scores are only ${pct(clock.margin)} apart, below the required ${pct(clock.decisionRules.minimumMargin)} margin for one regime.` : `The top-two margin clears the required ${pct(clock.decisionRules.minimumMargin)} separation.`}</li><li>Monthly persistence is {classification.monthlyPersistence.consecutiveUpdates} of {classification.monthlyPersistence.requiredUpdates} required updates.</li><li>Underlying observation dates range from {month(clock.oldestRequiredObservationDate)} to {month(clock.newestObservationDate)}.</li><li>Latest-vintage revised data are used rather than a complete real-time vintage archive.</li></ul></div>
    {classification.provisionalClassification.partialPeriodIndicators.length > 0 && <p className="mt-3 text-xs leading-5 text-stone-500">Partial-period evidence: {classification.provisionalClassification.partialPeriodIndicators.map((item) => `${item.label} (${month(item.sourceDate)})`).join(', ')}. These observations receive freshness metadata but remain provisional until the period closes.</p>}
    {classification.exceptionalTransition && <p className="mt-3 border-l-2 border-amber-500 pl-3 text-sm text-amber-700 dark:text-amber-300">{preferredTransitionWording ? 'Physical tightness appears to be re-emerging while affordability pressure remains present. This resembles renewed tightening layered on an unresolved affordability phase.' : `The leading candidate moved from ${classification.exceptionalTransition.fromRegime} toward ${classification.exceptionalTransition.toRegime}. This is outside the usual configured sequence and should be reviewed alongside the underlying evidence.`}</p>}
    <p className="mt-5 text-xs leading-5 text-amber-700 dark:text-amber-300">{classification.dataVintageWarning}</p>
  </section>
}
