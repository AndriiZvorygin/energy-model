import { ChartViewer } from '../components/ChartViewer'
import { EvidenceLabel } from '../components/EvidenceLabel'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
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
    <div className="mt-6 flex flex-wrap gap-2"><EvidenceLabel label="Validated relationship" /><EvidenceLabel label="Supported historical pattern" /><EvidenceLabel label="Contextual indicator" /><EvidenceLabel label="Experimental proxy" /><EvidenceLabel label="Scenario concept" /></div>
    <div className="mt-12 space-y-10"><ChartViewer src="/charts/system_response_chain.png" alt="System response chain from liquidity through energy and the economy" title="System-response chain" description="Each arrow is a separate hypothesis. Co-movement is not automatically predictive or causal." source="Project framework; evidence status is assigned at the indicator or relationship level." /><ChartViewer src="/charts/indicator_lag_map.png" alt="Indicative lag map for energy and macro indicators" title="Indicator lag map" description="Observed lead relationships vary by episode and are shown as diagnostics, not fixed laws." source="EIA, FRED, BEA, BLS and project-derived lead scans." /></div>
  </PageBody></>
}
