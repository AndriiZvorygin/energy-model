import type { ChartDataset } from './chartTypes'
import { ConceptExplainerChart, type ConceptType } from './ConceptExplainerChart'

export type ChartDetailsData = Pick<ChartDataset, 'plainLanguageSummary' | 'description' | 'howToRead' | 'calculation' | 'patternsToWatch' | 'limitations' | 'sourceNotes' | 'transformation'> & Partial<Pick<ChartDataset, 'series' | 'availableTransformations'>>

const observationRange = (dataset: ChartDetailsData) => {
  const dated = (dataset.series ?? []).map((series) => `${series.label}: ${series.finalObservationDate ?? 'not available'}`)
  return dated.join('; ')
}

export function ChartDetails({ dataset }: { dataset: ChartDetailsData }) {
  const reference = dataset.transformation.referenceStart && dataset.transformation.referenceEnd
    ? `${dataset.transformation.referenceStart.slice(0, 7)} to ${dataset.transformation.referenceEnd.slice(0, 7)}`
    : 'not applicable'
  const formula = dataset.calculation.formula.toLowerCase()
  const explainer: ConceptType | null = formula.includes('residual') ? 'residual' : formula.includes('corr') || formula.includes('correlation') ? 'correlation' : formula.includes('lag') || formula.includes('t-') ? 'lag' : dataset.availableTransformations?.includes('zscore') ? 'zscore' : dataset.availableTransformations?.includes('indexed') ? 'indexed' : formula.includes('yoy') || formula.includes('year-over-year') ? 'yoy' : null
  return <div className="mt-5">
    <p className="max-w-4xl border-l-2 border-petroleum pl-4 text-sm leading-6 text-stone-700 dark:text-stone-200">{dataset.plainLanguageSummary}</p>
    <details className="mt-4 border-y border-stone-200 py-4 dark:border-stone-800">
      <summary className="cursor-pointer text-sm font-semibold">Chart details and calculations</summary>
      <div className="mt-5 grid gap-5 text-sm leading-6 text-stone-600 md:grid-cols-2 dark:text-stone-300">
        <section><h3 className="font-semibold text-ink dark:text-white">What this chart shows</h3><p className="mt-1">{dataset.description}</p></section>
        <section><h3 className="font-semibold text-ink dark:text-white">How to read it</h3><p className="mt-1">{dataset.howToRead}</p></section>
        <section><h3 className="font-semibold text-ink dark:text-white">How it was calculated</h3><p className="mt-1 font-mono text-xs">{dataset.calculation.formula}</p><p className="mt-2">{dataset.calculation.explanation}</p><p className="mt-2"><strong>Example:</strong> {dataset.calculation.example}</p>{dataset.availableTransformations?.includes('zscore') && <p className="mt-2"><strong>Z-score baseline:</strong> z = (observation - historical mean) / historical standard deviation. The fixed reference period is {reference}; changing the visible range does not change this baseline.</p>}</section>
        <section><h3 className="font-semibold text-ink dark:text-white">What patterns to look for</h3><ul className="mt-1 list-disc space-y-1 pl-5">{dataset.patternsToWatch.map((item) => <li key={item}>{item}</li>)}</ul></section>
        <section><h3 className="font-semibold text-ink dark:text-white">Limitations and alternative explanations</h3><ul className="mt-1 list-disc space-y-1 pl-5">{dataset.limitations.map((item) => <li key={item}>{item}</li>)}</ul></section>
        <section><h3 className="font-semibold text-ink dark:text-white">Data sources and observation dates</h3><ul className="mt-1 list-disc space-y-1 pl-5">{dataset.sourceNotes.map((item) => <li key={item}>{item}</li>)}</ul>{dataset.series?.length ? <p className="mt-2 text-xs">Latest observations: {observationRange(dataset)}.</p> : null}</section>
      </div>
      {explainer && <div className="mt-6"><h3 className="mb-3 text-sm font-semibold">Visual calculation example</h3><ConceptExplainerChart concept={explainer} /></div>}
    </details>
  </div>
}
