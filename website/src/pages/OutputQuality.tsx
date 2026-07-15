import { EnergyOutputCorrelationChart } from '../components/charts/EnergyOutputCorrelationChart'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { PageBody, PageHeader } from '../components/PageHeader'

export function OutputQuality() {
  return <><PageHeader eyebrow="Economic output quality" title="What Kind of Economic Growth Is This?" description="A multi-lens view of measured production, net productive capacity, household command over essentials, and financialization or asset valuation." /><PageBody>
    <div className="max-w-4xl space-y-4 text-sm leading-6 text-stone-600 dark:text-stone-300"><p>GDP measures production during a period rather than the economy's total stock of wealth. Real GDP adjusts that production for inflation, while official net domestic product accounts for capital consumption.</p><p>Household prosperity can diverge from aggregate GDP, and financial claims or asset valuations can diverge from productive capacity. Those differences are questions to inspect, not evidence that finance, real estate, or service output is inherently valueless.</p></div>
    <section className="mt-12"><h2 className="text-2xl font-semibold">Headline GDP</h2><div className="mt-5"><ResearchTimeSeriesChart file="output-quality-headline.json" initialTransformation="indexed" syncUrl={false} /></div></section>
    <section className="mt-12"><h2 className="text-2xl font-semibold">GDP versus net output per person</h2><div className="mt-5"><ResearchTimeSeriesChart file="output-quality-net-output.json" initialTransformation="indexed" syncUrl={false} /></div></section>
    <section className="mt-12"><h2 className="text-2xl font-semibold">Net productive capacity</h2><div className="mt-5"><ResearchTimeSeriesChart file="output-quality-capacity.json" initialTransformation="zscore" syncUrl={false} /></div></section>
    <section className="mt-12"><h2 className="text-2xl font-semibold">Household prosperity</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">The household-command series is experimental. Its median-income and average-cost components remain visible and no combined prosperity score is published.</p><div className="mt-5"><ResearchTimeSeriesChart file="output-quality-household.json" initialTransformation="indexed" syncUrl={false} /></div></section>
    <section className="mt-12"><h2 className="text-2xl font-semibold">Financialization and valuation</h2><div className="mt-5"><ResearchTimeSeriesChart file="output-quality-financial.json" initialTransformation="raw" syncUrl={false} /></div></section>
    <section className="mt-12"><EnergyOutputCorrelationChart /></section>
  </PageBody></>
}
