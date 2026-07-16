import { AlertCircle, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useGeneratedManifest } from './charts/useChartData'

const formatDate = (date: string) => new Intl.DateTimeFormat('en-US', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(date))
const formatMonth = (date: string) => new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T00:00:00Z`))

export function FrameworkStatusNotice({ subject }: { subject: 'regime' | 'symptom' }) {
  const { manifest } = useGeneratedManifest()
  const message = subject === 'regime'
    ? 'The project does not currently assign the latest data to one active regime. The states below are an interpretive framework and the shaded periods are historical comparison windows.'
    : 'The project does not currently mark these symptoms as active or inactive. They are historical diagnostic patterns to compare with the dated evidence on the Current State page.'
  return <section className="border-y border-amber-600 py-5" aria-label={`Current ${subject} classification status`}>
    <div className="flex items-start gap-3"><AlertCircle className="mt-0.5 shrink-0 text-amber-700 dark:text-amber-400" size={20} /><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300">Current status: not classified</p><h2 className="mt-1 text-xl font-semibold">No live {subject} label is being asserted</h2><p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{message}</p>{manifest?.currentState && <p className="mt-2 text-xs text-stone-500">Latest evidence snapshot generated {formatDate(manifest.currentState.asOf)} UTC; individual observation vintages span {formatMonth(manifest.currentState.oldestLatestObservationDate)} to {formatMonth(manifest.currentState.latestObservationDate)}.</p>}<Link to="/current-state/us" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">Inspect current dated U.S. evidence <ArrowRight size={15} /></Link></div></div>
  </section>
}
