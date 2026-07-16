import type { ClassificationClock, CurrentClassification } from '../charts/chartTypes'

const month = (value: string | null) => value ? new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value.slice(0, 10)}T00:00:00Z`)) : 'Unavailable'
const pct = (value: number) => `${(100 * value).toFixed(0)}%`

function Clock({ title, clock }: { title: string; clock: ClassificationClock }) {
  const unclassified = clock.classification === 'Unclassified'
  return <article className="border-t-2 border-petroleum pt-4">
    <p className="text-xs font-semibold uppercase text-stone-500">{title}</p>
    <h3 className={`mt-2 text-xl font-semibold ${unclassified ? 'text-amber-700 dark:text-amber-300' : ''}`}>{clock.classification}</h3>
    <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
      <div><dt className="text-stone-500">Classification date</dt><dd className="font-medium">{month(clock.classificationDate)}</dd></div>
      <div><dt className="text-stone-500">Confidence</dt><dd className="font-medium capitalize">{clock.confidence}</dd></div>
      <div><dt className="text-stone-500">Evidence coverage</dt><dd className="font-medium">{pct(clock.coverage)}</dd></div>
      <div><dt className="text-stone-500">Observation range</dt><dd className="font-medium">{month(clock.oldestRequiredObservationDate)} to {month(clock.newestObservationDate)}</dd></div>
    </dl>
  </article>
}

export function ClassificationSummary({ classification, compact = false }: { classification: CurrentClassification; compact?: boolean }) {
  return <section className="border-y border-stone-300 py-6 dark:border-stone-700">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-petroleum">Current diagnostic interpretation · Experimental transparent classifier</p><h2 className="mt-2 text-2xl font-semibold">Two clocks, one transparent evidence set</h2></div><p className="max-w-md text-xs leading-5 text-stone-500"><strong className="text-ink dark:text-white">Scope:</strong> {classification.scope}</p></div>
    <div className={`mt-6 grid gap-7 ${compact ? 'lg:grid-cols-2' : 'xl:grid-cols-2'}`}><Clock title="Provisional monthly nowcast" clock={classification.provisionalClassification} /><Clock title="Confirmed quarterly state" clock={classification.confirmedClassification} /></div>
    <p className="mt-5 text-sm text-stone-600 dark:text-stone-300">Monthly candidate persistence: <strong>{classification.monthlyPersistence.consecutiveUpdates} of {classification.monthlyPersistence.requiredUpdates} required updates</strong> ({classification.monthlyPersistence.confirmationStatus.replaceAll('_', ' ')}). The monthly reading remains provisional; the quarterly clock is the confirmed state.</p>
    {classification.provisionalClassification.partialPeriodIndicators.length > 0 && <p className="mt-3 text-xs leading-5 text-stone-500">Partial-period evidence: {classification.provisionalClassification.partialPeriodIndicators.map((item) => `${item.label} (${month(item.sourceDate)})`).join(', ')}. These observations receive freshness metadata but remain provisional until the period closes.</p>}
    {classification.exceptionalTransition && <p className="mt-3 border-l-2 border-amber-500 pl-3 text-sm text-amber-700 dark:text-amber-300">Exceptional transition review: {classification.exceptionalTransition.fromRegime} to {classification.exceptionalTransition.toRegime}. {classification.exceptionalTransition.note}</p>}
    <p className="mt-5 text-xs leading-5 text-amber-700 dark:text-amber-300">{classification.dataVintageWarning}</p>
  </section>
}
