import { useLocation } from 'react-router-dom'
import { GeneratedRouteEvidenceSummary } from '../components/diagnostics/GeneratedRouteEvidenceSummary'
import { GeneratedTopicIndicatorGrid } from '../components/diagnostics/GeneratedTopicIndicatorGrid'
import { PageBody, PageHeader } from '../components/PageHeader'
import { useGeneratedJson } from '../components/charts/useChartData'

type Context = {
  upstreamPressure: string
  humanImpactDirection: string
  humanImpactLevel: string
  demographicExposure: string
  componentDirections: Record<string, string>
  latestUpstreamYear: string | null
  latestFoodAccessYear: number
  latestNutritionYear: number
  latestMortalityYear: number
  latestDemographyYear: number
  staleDataWarnings: string[]
}

const pageCopy: Record<string, { title: string; description: string; note: string }> = {
  'food-security': {
    title: 'Global food security',
    description: 'Official global prevalence and affected-person counts for undernourishment, food insecurity, and healthy-diet affordability.',
    note: 'International commodity pressure can affect access, but retail systems, income, conflict, policy, exchange rates, and local supply also shape food security.',
  },
  nutrition: {
    title: 'Global nutrition outcomes',
    description: 'Biological outcomes including child stunting and wasting, anaemia among women, and low birth weight.',
    note: 'These annual modelled outcomes move more slowly than commodity prices and are revised as country data and inter-agency methods change.',
  },
  'human-impact': {
    title: 'Global human impact',
    description: 'Food access, biological nutrition outcomes, and direct cause-coded mortality are kept on their own publication clocks.',
    note: 'Direct nutritional-deficiency deaths do not measure the full mortality burden statistically attributable to undernutrition.',
  },
  demography: {
    title: 'Global demography',
    description: 'Population, growth, births, children under five, and working-age population describe exposure and denominators.',
    note: 'Population growth changes affected-person counts and exposure. It is never classified as hardship by itself.',
  },
}

export function GlobalHumanImpact() {
  const topic = useLocation().pathname.split('/').filter(Boolean).at(-1) ?? 'human-impact'
  const copy = pageCopy[topic] ?? pageCopy['human-impact']
  const { data: context } = useGeneratedJson<Context>('global/human-impact-context.json')
  return <>
    <PageHeader eyebrow="Global human evidence" title={copy.title} description={copy.description} />
    <PageBody>
      <GeneratedRouteEvidenceSummary title="Current published evidence" />

      {context && <section className="mt-8 border-y border-stone-300 py-6 dark:border-stone-700" aria-label="Publication clocks">
        <h2 className="text-lg font-semibold">Evidence clocks</h2>
        <div className="mt-4 grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-5 dark:border-stone-800 dark:bg-stone-800">
          {[
            ['Upstream', context.latestUpstreamYear], ['Food access', context.latestFoodAccessYear],
            ['Nutrition', context.latestNutritionYear], ['Mortality', context.latestMortalityYear],
            ['Demography', context.latestDemographyYear],
          ].map(([label, value]) => <div key={label} className="bg-white p-4 dark:bg-[#18201d]"><p className="text-xs font-semibold uppercase text-stone-500">{label}</p><p className="mt-1 font-semibold">{String(value)}</p></div>)}
        </div>
        <p className="mt-4 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{copy.note}</p>
        <ul className="mt-3 space-y-1 text-xs leading-5 text-amber-800 dark:text-amber-300">{context.staleDataWarnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
      </section>}

      <section className="mt-10">
        <p className="text-xs font-semibold uppercase text-petroleum">Historical context</p>
        <h2 className="mt-2 text-2xl font-semibold">Official annual histories</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">Rates and affected-person counts remain paired in the generated observations. Open any indicator to inspect its full history, source, definition, and limitations.</p>
        <GeneratedTopicIndicatorGrid />
      </section>
    </PageBody>
  </>
}
