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
  latestObservedHumanYear: number
  latestIndicatorYear: number
  latestFoodAccessYear: number
  latestNutritionYear: number
  latestMortalityYear: number
  latestDemographyYear: number
  staleDataWarnings: string[]
  observedHumanAssessment: {
    throughYear: number
    level: string
    direction: string
    recentMomentumOneYear: string
    primaryDirectionThreeYears: string
    structuralContextFiveYears: string
    humanEffectsAfterLatestYear: string
  }
  historicalMortalityAssessment: { label: string; throughYear: number; direction: string }
  humanImpactNowcast: { label: string; status: string; reason: string }
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
      {context && topic !== 'demography' && <section className="grid gap-3 lg:grid-cols-3" aria-label="Temporally separated global evidence">
        <article className="border-t-4 border-emerald-600 bg-white p-5 shadow-sm dark:bg-[#18201d]">
          <p className="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-300">1. Latest observed human conditions</p>
          <h2 className="mt-2 text-lg font-semibold">Through {context.latestObservedHumanYear}</h2>
          <p className="mt-2 text-sm leading-6">Observed human-impact level through {context.latestObservedHumanYear}: <strong className="capitalize">{context.observedHumanAssessment.level}</strong>.</p>
          <p className="mt-1 text-sm leading-6">Observed human-impact direction through {context.latestObservedHumanYear}: <strong className="capitalize">{context.observedHumanAssessment.direction}</strong>.</p>
          <p className="mt-3 text-xs leading-5 text-stone-600 dark:text-stone-300">One-year momentum: {context.observedHumanAssessment.recentMomentumOneYear}. Three-year primary direction: {context.observedHumanAssessment.primaryDirectionThreeYears}. Five-year context: {context.observedHumanAssessment.structuralContextFiveYears}.</p>
        </article>
        <article className="border-t-4 border-amber-500 bg-white p-5 shadow-sm dark:bg-[#18201d]">
          <p className="text-xs font-semibold uppercase text-amber-700 dark:text-amber-300">2. Current upstream market pressure</p>
          <h2 className="mt-2 text-lg font-semibold capitalize">{context.upstreamPressure}</h2>
          <p className="mt-2 text-sm leading-6">Current upstream pressure through {context.latestUpstreamYear}: <strong className="capitalize">{context.upstreamPressure}</strong>. This is a market reading, not a contemporaneous human outcome.</p>
          <p className="mt-3 text-xs font-semibold leading-5 text-stone-600 dark:text-stone-300">Human effects after {context.latestObservedHumanYear}: not yet observed.</p>
        </article>
        <article className="border-t-4 border-stone-500 bg-white p-5 shadow-sm dark:bg-[#18201d]">
          <p className="text-xs font-semibold uppercase text-stone-600 dark:text-stone-300">3. Human-impact nowcast</p>
          <h2 className="mt-2 text-lg font-semibold">Unavailable until validated</h2>
          <p className="mt-2 text-sm leading-6">No 2025–2026 human outcome is inferred from later commodity prices.</p>
          <p className="mt-3 text-xs leading-5 text-stone-600 dark:text-stone-300">{context.humanImpactNowcast.reason}</p>
        </article>
      </section>}

      <div className="mt-8"><GeneratedRouteEvidenceSummary title={topic === 'demography' ? 'Current published evidence' : 'Current observed evidence'} /></div>

      {context && <section className="mt-8 border-y border-stone-300 py-6 dark:border-stone-700" aria-label="Publication clocks">
        <h2 className="text-lg font-semibold">Evidence clocks</h2>
        <div className="mt-4 grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-5 dark:border-stone-800 dark:bg-stone-800">
          {[
            ['Upstream prices', context.latestUpstreamYear], ['Observed human state', context.latestObservedHumanYear], ['Food access', context.latestFoodAccessYear],
            ['Nutrition', context.latestNutritionYear], ['Mortality', context.latestMortalityYear],
            ['Demography', context.latestDemographyYear],
          ].map(([label, value]) => <div key={label} className="bg-white p-4 dark:bg-[#18201d]"><p className="text-xs font-semibold uppercase text-stone-500">{label}</p><p className="mt-1 font-semibold">{String(value)}</p></div>)}
        </div>
        <p className="mt-4 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">{copy.note}</p>
        <ul className="mt-3 space-y-1 text-xs leading-5 text-amber-800 dark:text-amber-300">{context.staleDataWarnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
      </section>}

      <section className="mt-10">
        <p className="text-xs font-semibold uppercase text-petroleum">Maintained observations</p>
        <h2 className="mt-2 text-2xl font-semibold">Latest observed human evidence</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">Rates and affected-person counts remain paired in the generated observations. Open any indicator to inspect its full history, source, definition, and limitations.</p>
        <GeneratedTopicIndicatorGrid groups={['Latest maintained human evidence']} />
      </section>

      {(topic === 'nutrition' || topic === 'human-impact') && <section className="mt-12 border-t border-stone-300 pt-8 dark:border-stone-700">
        <p className="text-xs font-semibold uppercase text-stone-500">Historical supporting evidence</p>
        <h2 className="mt-2 text-2xl font-semibold">{context?.historicalMortalityAssessment.label ?? 'Older outcome histories'}</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">Mortality, DALYs, low birth weight, and other stale histories remain available for long-run context. They have zero weight in the observed 2024 headline.</p>
        <GeneratedTopicIndicatorGrid groups={['Historical supporting evidence']} />
      </section>}
    </PageBody>
  </>
}
