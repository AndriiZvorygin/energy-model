import { CheckCircle2, Database, FlaskConical, ShieldAlert } from 'lucide-react'
import { ExplanationCard } from '../components/ExplanationCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'
import { ConceptExplainerChart, type ConceptType } from '../components/charts/ConceptExplainerChart'

const sections = [
  { title: 'Data sources', icon: Database, text: researchData.content.dataSources },
  { title: 'Core formulas', icon: FlaskConical, text: researchData.content.formulas },
  { title: 'Target definitions', icon: CheckCircle2, text: researchData.content.targets },
  { title: 'Lag convention', icon: CheckCircle2, text: researchData.content.lagConvention },
  { title: 'Validation method', icon: FlaskConical, text: researchData.content.validation },
  { title: 'Known caveats', icon: ShieldAlert, text: researchData.content.caveats },
  { title: 'Shock periods', icon: ShieldAlert, text: researchData.content.shockPeriods },
  { title: 'System-response scope', icon: FlaskConical, text: researchData.systemResponse.content.firstRelease },
  { title: 'Evidence labels', icon: CheckCircle2, text: researchData.systemResponse.content.evidenceLabels },
  { title: 'Diagnostic limitations', icon: ShieldAlert, text: researchData.systemResponse.content.gaps },
]

const explainers: { concept: ConceptType; title: string; description: string }[] = [
  { concept: 'zscore', title: 'Z-score', description: 'Place a raw observation relative to a fixed historical mean and standard deviation.' },
  { concept: 'yoy', title: 'Year-over-year change', description: 'Compare the current month with the same month one year earlier.' },
  { concept: 'lag', title: 'Lag alignment', description: 'Align an earlier predictor observation with a later outcome without using future information.' },
  { concept: 'correlation', title: 'Correlation', description: 'See positive, weak, and negative co-movement without interpreting it as causation.' },
  { concept: 'residual', title: 'Model residual', description: 'Separate actual movement from the model-implied path.' },
  { concept: 'indexed', title: 'Indexed to 100', description: 'Compare relative paths when raw starting levels and units differ.' },
]

export function Methodology() {
  return <><PageHeader eyebrow="Methodology" title="How the evidence is built" description="The site presents a descriptive, interpretable research model. Rolling validation and strict lag conventions matter more than in-sample fit." /><PageBody>
    <div className="space-y-4">{sections.map(({ title, icon: Icon, text }) => <section key={title} className="border-b border-stone-200 py-6 first:pt-0 dark:border-stone-800"><div className="grid gap-5 md:grid-cols-[180px_1fr]"><div><Icon className="text-petroleum" size={20} /><h2 className="mt-3 font-semibold text-ink dark:text-white">{title}</h2></div><ResearchText text={text} /></div></section>)}</div>
    <section className="mt-14"><p className="text-xs font-semibold uppercase text-petroleum">Interactive methods</p><h2 className="mt-2 text-2xl font-semibold">See the calculation, not only the definition</h2><div className="mt-6 grid gap-5 lg:grid-cols-2">{explainers.map((item) => <article key={item.concept}><h3 className="font-semibold">{item.title}</h3><p className="mt-1 mb-3 text-sm leading-6 text-stone-500">{item.description}</p><ConceptExplainerChart concept={item.concept} /></article>)}</div></section>
    <div className="mt-12 grid gap-4 md:grid-cols-2"><ExplanationCard title="Suitable uses" icon={CheckCircle2}><ResearchText text={researchData.content.suitableUses} /></ExplanationCard><ExplanationCard title="Unsuitable uses" icon={ShieldAlert}><ResearchText text={researchData.content.unsuitableUses} /></ExplanationCard></div>
    <p className="mt-10 text-xs leading-5 text-stone-500">Website content is generated from the project’s analysis CSV and Markdown outputs. The website does not run, alter, or replace the Python research pipeline.</p>
  </PageBody></>
}
