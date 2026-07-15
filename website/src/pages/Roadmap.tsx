import { CheckCircle2, FlaskConical, Map } from 'lucide-react'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'

const columns = [
  { title: 'Implemented', icon: CheckCircle2, items: ['Five-layer framework and catalogue', 'Compact energy-economic dataset', 'Energy-burden benchmark tests', 'Physical-tightness diagnostics', 'Labour early-warning scan', 'Historical episode schema'] },
  { title: 'Experimental', icon: FlaskConical, items: ['Household and GDP burden proxies', 'Transparent regime-rule design', 'Distributed-lag transmission links', 'Latest-vintage current-state percentiles'] },
  { title: 'Proposed', icon: Map, items: ['Real-time data vintages', 'Global spare-capacity history', 'Reliable futures-curve structure', 'Distributional household exposure', 'Carefully scoped social and institutional measures'] },
]

export function Roadmap() {
  return <><PageHeader eyebrow="Research status" title="What exists, what is tentative, and what comes next" description="The project preserves useful individual indicators even when they do not improve a forecasting benchmark." /><PageBody><div className="grid gap-px border border-stone-200 bg-stone-200 lg:grid-cols-3 dark:border-stone-800 dark:bg-stone-800">{columns.map(({ title, icon: Icon, items }) => <section key={title} className="bg-white p-6 dark:bg-[#18201d]"><Icon size={20} className="text-petroleum" /><h2 className="mt-3 text-lg font-semibold">{title}</h2><ul className="mt-5 space-y-3 text-sm leading-6 text-stone-600 dark:text-stone-300">{items.map((item) => <li key={item} className="border-b border-stone-100 pb-3 last:border-0 dark:border-stone-800">{item}</li>)}</ul></section>)}</div><div className="mt-12 grid gap-8 md:grid-cols-2"><section><h2 className="text-lg font-semibold">Known gaps</h2><div className="mt-3"><ResearchText text={researchData.systemResponse.content.gaps} /></div></section><section><h2 className="text-lg font-semibold">Recommended next step</h2><div className="mt-3"><ResearchText text={researchData.systemResponse.content.nextStep} /></div></section></div></PageBody></>
}
