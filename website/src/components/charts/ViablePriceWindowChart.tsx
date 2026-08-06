import { useState } from 'react'
import { EvidenceLabel } from '../EvidenceLabel'
import { useGeneratedJson } from './useChartData'

type PriceWindowState = { id: string; label: string; producerFloor: number; consumerCeiling: number; interpretation: string }
type PriceWindowData = { title: string; evidenceLabel: string; plainLanguageSummary: string; sourceNotes: string[]; citations?: { label: string; url: string; role: string }[]; methodology: { formula: string; limitations: string[] }; states: PriceWindowState[] }

export function ViablePriceWindowChart() {
  const { data, error } = useGeneratedJson<PriceWindowData>('viable-price-window.json')
  const [selected, setSelected] = useState(0)
  if (error) return <p className="border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">Conceptual price-window data could not be loaded: {error}</p>
  if (!data) return <div className="flex h-64 items-center justify-center border border-stone-200 text-sm text-stone-500 dark:border-stone-800">Loading conceptual scenario…</div>
  const state = data.states[selected] ?? data.states[0]
  const squeeze = state.consumerCeiling - state.producerFloor
  return <section className="border border-stone-200 p-5 dark:border-stone-800" aria-label={data.title}>
    <div className="flex flex-wrap items-center gap-2"><h3 className="text-lg font-semibold">{data.title}</h3><EvidenceLabel label={data.evidenceLabel} /></div>
    <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">{data.plainLanguageSummary}</p>
    <div className="mt-5 flex flex-wrap gap-2" role="tablist" aria-label="Conceptual price-window states">
      {data.states.map((item, index) => <button key={item.id} type="button" role="tab" aria-selected={selected === index} onClick={() => setSelected(index)} className={`border px-3 py-2 text-xs font-semibold ${selected === index ? 'border-petroleum bg-petroleum text-white' : 'border-stone-300 dark:border-stone-700'}`}>{item.label}</button>)}
    </div>
    <div className="mt-6" role="img" aria-label={`${state.label}: producer viability floor ${state.producerFloor} and consumer affordability ceiling ${state.consumerCeiling} on a normalized conceptual scale`}>
      <div className="relative h-20 border-y border-stone-200 dark:border-stone-700">
        <div className="absolute inset-x-0 top-9 h-2 bg-stone-200 dark:bg-stone-700" />
        {squeeze > 0 && <div className="absolute top-8 h-4 bg-emerald-500/70" style={{ left: `${state.producerFloor}%`, width: `${squeeze}%` }} />}
        <div className="absolute top-2 h-16 w-0.5 bg-petroleum" style={{ left: `${state.producerFloor}%` }}><span className="absolute left-1 top-0 w-28 text-xs font-semibold text-petroleum">Producer viability floor</span></div>
        <div className="absolute top-2 h-16 w-0.5 bg-signal" style={{ left: `${state.consumerCeiling}%` }}><span className="absolute right-1 top-8 w-28 -translate-x-full text-right text-xs font-semibold text-signal">Consumer affordability ceiling</span></div>
      </div>
      <div className="mt-2 flex justify-between text-[11px] text-stone-500"><span>0 · lower normalized boundary</span><span>100 · higher normalized boundary</span></div>
    </div>
    <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
      <p><span className="block text-xs uppercase text-stone-500">Producer floor</span><strong>{state.producerFloor}</strong></p>
      <p><span className="block text-xs uppercase text-stone-500">Consumer ceiling</span><strong>{state.consumerCeiling}</strong></p>
      <p><span className="block text-xs uppercase text-stone-500">Conceptual window</span><strong>{squeeze > 0 ? `${squeeze} points` : 'none'}</strong></p>
    </div>
    <p className="mt-4 text-sm leading-6 text-stone-600 dark:text-stone-300">{state.interpretation}</p>
    <details className="mt-5 border-t border-stone-200 pt-4 text-sm dark:border-stone-800"><summary className="cursor-pointer font-semibold">Concept details and limitations</summary><div className="mt-3 space-y-3 text-stone-600 dark:text-stone-300"><p><strong>Calculation:</strong> {data.methodology.formula}</p><ul className="list-disc space-y-1 pl-5">{data.methodology.limitations.map((item) => <li key={item}>{item}</li>)}</ul><p><strong>Sources:</strong> {data.sourceNotes.join(' ')}</p>{data.citations && <div><strong>Interpretive citations:</strong><ul className="mt-1 list-disc space-y-1 pl-5">{data.citations.map((citation) => <li key={citation.url}><a className="underline decoration-petroleum underline-offset-2" href={citation.url} target="_blank" rel="noreferrer">{citation.label}</a><span> — {citation.role}</span></li>)}</ul></div>}</div></details>
    <div className="mt-5 overflow-x-auto"><table className="min-w-full text-left text-xs"><caption className="sr-only">Conceptual viable price-window states</caption><thead><tr className="border-b border-stone-200 dark:border-stone-800"><th className="p-2">State</th><th className="p-2">Producer floor</th><th className="p-2">Consumer ceiling</th><th className="p-2">Interpretation</th></tr></thead><tbody>{data.states.map((item) => <tr key={item.id} className="border-b border-stone-200 dark:border-stone-800"><th className="p-2 font-medium">{item.label}</th><td className="p-2">{item.producerFloor}</td><td className="p-2">{item.consumerCeiling}</td><td className="p-2">{item.interpretation}</td></tr>)}</tbody></table></div>
  </section>
}
