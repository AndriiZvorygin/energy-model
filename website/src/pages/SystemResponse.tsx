import { Link } from 'react-router-dom'
import { AlignedResearchPanels } from '../components/charts/AlignedResearchPanels'
import { PublicationFigure } from '../components/charts/PublicationFigure'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { ViablePriceWindowChart } from '../components/charts/ViablePriceWindowChart'
import { EvidenceLabel } from '../components/EvidenceLabel'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { TimelineDiagram } from '../components/TimelineDiagram'
import { researchData } from '../data/generated'

const links = [
  ['Liquidity', 'Energy demand'], ['Energy demand', 'Physical tightness'], ['Physical tightness', 'Oil price and burden'],
  ['Oil price and burden', 'Spending and investment'], ['Spending and investment', 'Industry and GDP'], ['Industry and GDP', 'Labour and households'],
]

export function SystemResponse() {
  const content = researchData.systemResponse.content
  return <><PageHeader eyebrow="Diagnostic framework" title="How energy stress moves through a system" description="A layered research framework for reading physical conditions, affordability, economic transmission, labour consequences, and later social symptoms without forcing them into one score." /><PageBody>
    <div className="max-w-4xl"><ResearchText text={content.purpose} /></div>
    <div className="mt-10 grid gap-px overflow-hidden border border-stone-200 bg-stone-200 md:grid-cols-3 dark:border-stone-800 dark:bg-stone-800">{links.map(([from, to]) => <div key={from} className="bg-white p-5 dark:bg-[#18201d]"><p className="text-xs font-semibold uppercase text-stone-500">{from}</p><p className="mt-3 font-semibold text-ink dark:text-white">{to}</p></div>)}</div>
    <div className="mt-6 flex flex-wrap gap-2"><EvidenceLabel label="Validated relationship" /><EvidenceLabel label="Supported historical pattern" /><EvidenceLabel label="Contextual historical pattern" /><EvidenceLabel label="Contextual indicator" /><EvidenceLabel label="Experimental proxy" /><EvidenceLabel label="Scenario concept" /></div>
    <section className="mt-12"><h2 className="text-xl font-semibold">Explore the transmission layers</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">Select a layer to see its role. Each arrow remains a separate empirical question rather than a claim that the whole sequence is automatic.</p><div className="mt-6"><TimelineDiagram /></div></section>
    <section className="mt-14 border-t border-stone-200 pt-12 dark:border-stone-800">
      <div className="flex flex-wrap items-center gap-2"><h2 className="text-2xl font-semibold">The affordability squeeze: why scarcity can produce lower prices</h2><EvidenceLabel label="Scenario concept" /></div>
      <div className="mt-5 max-w-5xl"><ResearchText text={content.affordabilitySqueeze} /></div>
      <div className="mt-8"><ViablePriceWindowChart /></div>
      <div className="mt-8"><AlignedResearchPanels file="price-availability-activity.json" /></div>
      <div className="mt-8"><PublicationFigure src="/charts/demand_destruction_cycle.png" alt="Demand-destruction sequence from physical constraint and higher essential costs through weaker activity, lower benchmark prices, and reduced future investment" title="Demand-destruction cycle" description="Lower benchmark prices can reflect contracting demand and economic weakness rather than abundant, affordable energy. This figure is a synthesis diagram, not a causal estimate." source="Project synthesis; primary U.S. EIA, FRED, BEA, and BLS series are available in the interactive panels above. Gail Tverberg's affordability-centred interpretation is cited in the generated framework." /></div>
      <div className="mt-8 grid gap-px border border-stone-200 bg-stone-200 md:grid-cols-2 dark:border-stone-800 dark:bg-stone-800">
        <Link to="/energy-burden" className="bg-white p-5 text-sm hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"><strong>Continue to Energy Burden</strong><span className="mt-2 block leading-6 text-stone-600 dark:text-stone-300">Inspect energy costs relative to income, economic capacity, industry, and GDP.</span></Link>
        <Link to="/affordability" className="bg-white p-5 text-sm hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"><strong>Continue to Affordability</strong><span className="mt-2 block leading-6 text-stone-600 dark:text-stone-300">Follow the household-facing evidence through wages, disposable income, food, housing, rent, shelter, and mortgage costs.</span></Link>
      </div>
    </section>
    <section className="mt-14 border-t border-stone-200 pt-12 dark:border-stone-800"><div className="flex flex-wrap items-center gap-2"><h2 className="text-2xl font-semibold">Energy growth beyond population</h2><EvidenceLabel label="Contextual historical pattern" /></div><p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">This contextual view compares global primary-energy growth with population growth and subtracts the latter from the former. It is not a direct measure of living standards: efficiency, energy quality, technology, distribution, and economic structure all matter.</p><div className="mt-8"><ResearchTimeSeriesChart file="global-energy-growth-beyond-population.json" initialTransformation="raw" /></div></section>
    <div className="mt-12 space-y-6"><PublicationFigure src="/charts/system_response_chain.png" alt="System response chain from liquidity through energy and the economy" title="System-response chain" description="Each arrow is a separate hypothesis. Co-movement is not automatically predictive or causal." source="Project framework; evidence status is assigned at the indicator or relationship level." /><PublicationFigure src="/charts/indicator_lag_map.png" alt="Indicative lag map for energy and macro indicators" title="Indicator lag map" description="Observed lead relationships vary by episode and are shown as diagnostics, not fixed laws." source="EIA, FRED, BEA, BLS and project-derived lead scans." /></div>
  </PageBody></>
}
