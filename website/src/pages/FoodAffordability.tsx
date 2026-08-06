import { Link } from 'react-router-dom'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { AffordabilityIndicatorGrid } from '../components/affordability/AffordabilityIndicatorGrid'
import { GeneratedRouteEvidenceSummary } from '../components/diagnostics/GeneratedRouteEvidenceSummary'
import { EvidenceGeographySelector } from '../components/diagnostics/EvidenceGeographySelector'
import { PageBody, PageHeader } from '../components/PageHeader'

export const foodPageGeographies = {
  global: {
    title: 'Global food commodity prices',
    description: 'FAO international commodity indexes are shown as upstream global evidence, not as a global grocery-price index.',
    primaryIndicatorFiles: [
      'global/indicators/fao-food-price-index.json',
      'global/indicators/fao-food-price-index-real.json',
      'global/indicators/fao-cereals-price-index.json',
      'global/indicators/fao-vegetable-oils-price-index.json',
      'global/indicators/fao-dairy-price-index.json',
      'global/indicators/fao-meat-price-index.json',
      'global/indicators/fao-sugar-price-index.json',
    ],
  },
  canada: {
    title: 'Canadian food affordability',
    description: 'Canadian food, grocery, wage, disposable-income, and purchasing-power evidence. International commodity context is kept on the separate Global page.',
    primaryIndicatorFiles: [
      'canada/indicators/canada-food-cpi-yoy.json',
      'canada/indicators/canada-grocery-cpi-yoy.json',
      'canada/indicators/canada-food-inflation-gap.json',
      'canada/indicators/canada-grocery-inflation-gap.json',
      'canada/indicators/food-to-income.json',
      'canada/indicators/grocery-to-income.json',
      'canada/indicators/food-to-wage.json',
      'canada/indicators/grocery-to-wage.json',
      'canada/indicators/real-disposable-income-per-person.json',
      'canada/indicators/real-wage-growth.json',
    ],
  },
  'owen-sound': {
    title: 'Owen Sound food affordability',
    description: 'Owen Sound city-CSD and Grey Bruce food-security evidence. National and international food series are not substituted for local observations.',
    primaryIndicatorFiles: [],
  },
  comparison: {
    title: 'Canada–U.S. food comparison',
    description: 'Comparable Canadian and U.S. consumer food and purchasing-power series are shown side by side with each country’s native definitions.',
    primaryIndicatorFiles: [
      'canada/indicators/canada-food-cpi-yoy.json',
      'canada/indicators/canada-grocery-cpi-yoy.json',
      'us/indicators/us-food-cpi-yoy.json',
      'us/indicators/us-food-at-home-cpi-yoy.json',
    ],
  },
} as const

type FoodMode = keyof typeof foodPageGeographies

function PageLinks({ mode }: { mode: FoodMode }) {
  if (mode === 'global') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">For observed human outcomes, continue to <Link className="font-semibold text-petroleum underline" to="/global/food-security">Global food security</Link>.</p>
  if (mode === 'owen-sound') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">For broader context, see <Link className="font-semibold text-petroleum underline" to="/canada/food">Canadian food affordability</Link>. It is not local evidence.</p>
  if (mode === 'canada') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">Global commodity context is available separately under <Link className="font-semibold text-petroleum underline" to="/global/food-prices">Global food commodity prices</Link>.</p>
  return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">The global commodity layer is separate: <Link className="font-semibold text-petroleum underline" to="/global/food-prices">Global food commodity prices</Link>.</p>
}

function GlobalFoodPricesPage() {
  return <>
    <PageHeader eyebrow="Global commodity evidence" title={foodPageGeographies.global.title} description={foodPageGeographies.global.description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary title="Global food commodity evidence" />
      <section className="mt-12">
        <p className="text-xs font-semibold uppercase text-petroleum">International commodity pressure</p>
        <h2 className="mt-2 text-2xl font-semibold">FAO food-price indexes</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">The FAO Food Price Index measures international commodity quotations with a 2014–2016 base. It is not a global grocery-price index. Recent meat observations can combine projected and observed quotations and may be revised.</p>
        <div className="mt-6"><ResearchTimeSeriesChart file="affordability-fao-food.json" initialTransformation="raw" /></div>
        <AffordabilityIndicatorGrid files={[...foodPageGeographies.global.primaryIndicatorFiles]} />
      </section>
      <PageLinks mode="global" />
    </PageBody>
  </>
}

function OwenSoundFood() {
  return <>
    <PageHeader eyebrow="Owen Sound city-CSD evidence" title={foodPageGeographies['owen-sound'].title} description={foodPageGeographies['owen-sound'].description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary title="Owen Sound local food evidence" />
      <section className="mt-12 border-y border-stone-300 py-6 dark:border-stone-700">
        <p className="text-xs font-semibold uppercase text-petroleum">Local data boundary</p>
        <h2 className="mt-2 text-2xl font-semibold">Local food evidence is limited but explicit</h2>
        <p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">The refinery currently provides Grey Bruce food-insecurity prevalence, Grey Bruce nutritious-food-basket observations, and matched Owen Sound household cases. It does not provide a continuous Owen Sound grocery CPI or annual city food-basket history.</p>
        <p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">No FAO index, Canadian CPI, U.S. CPI, or Toronto series is displayed as an Owen Sound observation.</p>
      </section>
      <PageLinks mode="owen-sound" />
    </PageBody>
  </>
}

function CanadaFood() {
  return <>
    <PageHeader eyebrow="Canadian household evidence" title={foodPageGeographies.canada.title} description={foodPageGeographies.canada.description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary />
      <section className="mt-12">
        <p className="text-xs font-semibold uppercase text-petroleum">Canadian grocery prices</p>
        <h2 className="mt-2 text-2xl font-semibold">Food, stores, restaurants, and the broader CPI basket</h2>
        <div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-food.json" initialTransformation="yoy" /></div>
        <AffordabilityIndicatorGrid files={['canada/indicators/canada-food-cpi-yoy.json', 'canada/indicators/canada-grocery-cpi-yoy.json', 'canada/indicators/canada-food-inflation-gap.json', 'canada/indicators/canada-grocery-inflation-gap.json']} />
      </section>
      <section className="mt-16">
        <p className="text-xs font-semibold uppercase text-petroleum">Canadian price context</p>
        <h2 className="mt-2 text-2xl font-semibold">Food relative to Canadian energy prices and the CAD</h2>
        <div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-food-context.json" initialTransformation="raw" /></div>
      </section>
      <section className="mt-16">
        <p className="text-xs font-semibold uppercase text-petroleum">Canadian purchasing power</p>
        <h2 className="mt-2 text-2xl font-semibold">Food prices relative to income and wages</h2>
        <p className="mt-2 max-w-5xl text-sm leading-7 text-stone-600 dark:text-stone-300">Monthly food indexes are compared with monthly wages; quarterly food indexes are compared with quarterly household disposable income. Quarterly income is not forward-filled into monthly observations.</p>
        <div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-food-income.json" initialTransformation="raw" /></div>
        <AffordabilityIndicatorGrid files={['canada/indicators/household-disposable-income-per-person.json', 'canada/indicators/real-disposable-income-per-person.json', 'canada/indicators/food-to-income.json', 'canada/indicators/grocery-to-income.json', 'canada/indicators/food-income-gap.json', 'canada/indicators/grocery-income-gap.json']} />
        <div className="mt-10"><ResearchTimeSeriesChart file="affordability-canada-food-wages.json" initialTransformation="raw" /></div>
        <AffordabilityIndicatorGrid files={['canada/indicators/average-hourly-wages.json', 'canada/indicators/real-wage-growth.json', 'canada/indicators/food-to-wage.json', 'canada/indicators/grocery-to-wage.json']} />
      </section>
      <section className="mt-16 border-y border-stone-300 py-6 dark:border-stone-700"><p className="text-xs font-semibold uppercase text-petroleum">Methods and limitations</p><p className="mt-3 max-w-5xl text-sm leading-7 text-stone-600 dark:text-stone-300">Retail food prices also reflect exchange rates, energy and transport, fertilizer and farm inputs, processing, labour, wholesale and retail margins, domestic supply, taxes, and regulation. Canadian percentiles and affordability ratios use Canadian histories and native source definitions.</p></section>
      <PageLinks mode="canada" />
    </PageBody>
  </>
}

function FoodComparison() {
  return <>
    <PageHeader eyebrow="Explicit Canada–U.S. comparison" title={foodPageGeographies.comparison.title} description={foodPageGeographies.comparison.description} />
    <PageBody>
      <section><p className="text-xs font-semibold uppercase text-petroleum">Canada</p><h2 className="mt-2 text-2xl font-semibold">Canadian food and grocery prices</h2><div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-food.json" initialTransformation="yoy" /></div><AffordabilityIndicatorGrid files={['canada/indicators/canada-food-cpi-yoy.json', 'canada/indicators/canada-grocery-cpi-yoy.json', 'canada/indicators/real-wage-growth.json']} /></section>
      <section className="mt-16"><p className="text-xs font-semibold uppercase text-petroleum">United States</p><h2 className="mt-2 text-2xl font-semibold">U.S. food and food-at-home prices</h2><div className="mt-6"><ResearchTimeSeriesChart file="affordability-us-food-income.json" initialTransformation="raw" /></div><AffordabilityIndicatorGrid files={['us/indicators/us-food-cpi-yoy.json', 'us/indicators/us-food-at-home-cpi-yoy.json', 'us/indicators/us-food-away-from-home-cpi.json']} /></section>
      <PageLinks mode="comparison" />
    </PageBody>
  </>
}

export function FoodAffordability() { return <CanadaFood /> }
export function CanadaFoodAffordability() { return <CanadaFood /> }
export function GlobalFoodPrices() { return <GlobalFoodPricesPage /> }
export function OwenSoundFoodAffordability() { return <OwenSoundFood /> }
export function FoodComparisonPage() { return <FoodComparison /> }
