import { Link } from 'react-router-dom'
import { AffordabilityIndicatorGrid } from '../components/affordability/AffordabilityIndicatorGrid'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { GeneratedRouteEvidenceSummary } from '../components/diagnostics/GeneratedRouteEvidenceSummary'
import { EvidenceGeographySelector } from '../components/diagnostics/EvidenceGeographySelector'
import { PageBody, PageHeader } from '../components/PageHeader'

export const housingPageGeographies = {
  global: {
    title: 'Global residential property prices',
    description: 'BIS international residential-property histories provide global and country-comparison context. They are not household shelter-cost measures.',
    primaryIndicatorFiles: ['global/indicators/bis-real-house-prices.json', 'global/indicators/bis-advanced-real-house-prices.json', 'global/indicators/bis-emerging-real-house-prices.json', 'global/indicators/bis-canada-real-house-prices.json', 'global/indicators/bis-us-real-house-prices.json'],
  },
  canada: {
    title: 'Canadian housing affordability',
    description: 'Canadian property purchase prices, rent, mortgage interest, shelter, income, and housing-cost ratios. Global and U.S. comparisons are separate pages.',
    primaryIndicatorFiles: ['canada/indicators/new-housing-price-index.json', 'canada/indicators/new-housing-house-component.json', 'canada/indicators/new-housing-land-component.json', 'canada/indicators/rent-cpi.json', 'canada/indicators/mortgage-interest-cost.json', 'canada/indicators/shelter-cpi.json', 'canada/indicators/nhpi-to-income.json', 'canada/indicators/rent-to-income.json', 'canada/indicators/shelter-to-income.json', 'canada/indicators/mortgage-interest-to-income.json'],
  },
  'owen-sound': {
    title: 'Owen Sound housing affordability',
    description: 'Owen Sound city-CSD shelter burden, tenure evidence, core housing need, and local rental references. National and international housing series are not substituted for local observations.',
    primaryIndicatorFiles: [],
  },
  comparison: {
    title: 'Canada–U.S. housing comparison',
    description: 'Canadian and U.S. property-price and shelter-cost histories are shown separately with native definitions and explicit country labels.',
    primaryIndicatorFiles: ['canada/indicators/new-housing-price-index.json', 'canada/indicators/rent-cpi.json', 'us/indicators/us-fhfa-house-price-index.json', 'us/indicators/us-rent-cpi.json', 'us/indicators/us-shelter-cpi.json'],
  },
} as const

function PageLinks({ mode }: { mode: keyof typeof housingPageGeographies }) {
  if (mode === 'global') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">For Canadian shelter-cost evidence, continue to <Link className="font-semibold text-petroleum underline" to="/canada/housing">Canadian housing affordability</Link>.</p>
  if (mode === 'owen-sound') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">For broader context, see <Link className="font-semibold text-petroleum underline" to="/canada/housing">Canadian housing affordability</Link>. It is not local evidence.</p>
  if (mode === 'canada') return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">International property-price context is separate under <Link className="font-semibold text-petroleum underline" to="/global/housing">Global housing prices</Link>.</p>
  return <p className="mt-5 text-sm leading-6 text-stone-600 dark:text-stone-300">International context is separate under <Link className="font-semibold text-petroleum underline" to="/global/housing">Global housing prices</Link>.</p>
}

function GlobalHousing() {
  return <>
    <PageHeader eyebrow="Global property-price evidence" title={housingPageGeographies.global.title} description={housingPageGeographies.global.description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary title="Global residential-property evidence" />
      <section className="mt-12"><p className="text-xs font-semibold uppercase text-petroleum">International comparison</p><h2 className="mt-2 text-2xl font-semibold">Real residential property prices</h2><p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">BIS aggregates and selected country series differ in coverage, weighting, and native source methods. They measure asset purchase prices, not rent or current shelter services.</p><div className="mt-6"><ResearchTimeSeriesChart file="affordability-real-house-prices.json" initialTransformation="indexed" /></div><AffordabilityIndicatorGrid files={[...housingPageGeographies.global.primaryIndicatorFiles]} /></section>
      <PageLinks mode="global" />
    </PageBody>
  </>
}

function OwenSoundHousing() {
  return <>
    <PageHeader eyebrow="Owen Sound city-CSD evidence" title={housingPageGeographies['owen-sound'].title} description={housingPageGeographies['owen-sound'].description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary title="Owen Sound local housing evidence" />
      <section className="mt-12 border-y border-stone-300 py-6 dark:border-stone-700"><p className="text-xs font-semibold uppercase text-petroleum">Local data boundary</p><h2 className="mt-2 text-2xl font-semibold">Shelter and tenure evidence remain local</h2><p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">The local evidence includes Owen Sound city-CSD shelter burden, renter and owner burden, core housing need, matched household cases, and local rental references where available. It does not provide a continuous city property-price, rent-CPI, or mortgage-interest history.</p><p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">No Canadian, Toronto, U.S., or BIS series is displayed as an Owen Sound observation.</p></section>
      <PageLinks mode="owen-sound" />
    </PageBody>
  </>
}

function CanadaHousing() {
  return <>
    <PageHeader eyebrow="Canadian household evidence" title={housingPageGeographies.canada.title} description={housingPageGeographies.canada.description} />
    <PageBody>
      <EvidenceGeographySelector />
      <GeneratedRouteEvidenceSummary />
      <section className="mt-12"><p className="text-xs font-semibold uppercase text-petroleum">Property purchase prices</p><h2 className="mt-2 text-2xl font-semibold">Canadian new housing prices</h2><p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">The Statistics Canada NHPI covers new residential properties and separates house structure from land. It is not a broad resale-market index.</p><div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-housing.json" initialTransformation="indexed" /></div><AffordabilityIndicatorGrid files={['canada/indicators/new-housing-price-index.json', 'canada/indicators/new-housing-house-component.json', 'canada/indicators/new-housing-land-component.json', 'canada/indicators/canada-nhpi-yoy.json']} /></section>
      <section className="mt-16"><p className="text-xs font-semibold uppercase text-petroleum">Current housing-service costs</p><h2 className="mt-2 text-2xl font-semibold">Rent, mortgage interest, replacement cost, and shelter</h2><div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-housing-costs.json" initialTransformation="raw" /></div><AffordabilityIndicatorGrid files={['canada/indicators/rent-cpi.json', 'canada/indicators/mortgage-interest-cost.json', 'canada/indicators/homeowners-replacement-cost.json', 'canada/indicators/shelter-cpi.json']} /><div className="mt-10"><ResearchTimeSeriesChart file="affordability-canada-mortgage-renewal.json" initialTransformation="raw" /></div></section>
      <section className="mt-16"><p className="text-xs font-semibold uppercase text-petroleum">Housing relative to income</p><h2 className="mt-2 text-2xl font-semibold">Canadian purchasing power and housing-cost divergence</h2><p className="mt-2 max-w-5xl text-sm leading-6 text-stone-500">Asset affordability compares purchase prices with income. Current housing-cost pressure compares rent, shelter, and mortgage interest with income. Monthly indexes are averaged only across completed quarters.</p><div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-housing-income.json" initialTransformation="raw" /></div><div className="mt-10"><ResearchTimeSeriesChart file="affordability-canada-housing-ratios.json" initialTransformation="raw" /></div><AffordabilityIndicatorGrid files={['canada/indicators/nhpi-to-income.json', 'canada/indicators/residential-property-price-to-income.json', 'canada/indicators/rent-to-income.json', 'canada/indicators/shelter-to-income.json', 'canada/indicators/mortgage-interest-to-income.json', 'canada/indicators/real-nhpi.json']} /><div className="mt-10"><ResearchTimeSeriesChart file="affordability-canada-housing-gaps.json" initialTransformation="raw" /></div></section>
      <section className="mt-16 border-y border-stone-300 py-6 dark:border-stone-700"><p className="text-xs font-semibold uppercase text-petroleum">Methods and limitations</p><p className="mt-3 max-w-5xl text-sm leading-7 text-stone-600 dark:text-stone-300">NHPI, broad property prices, rent, mortgage-interest cost, replacement cost, and shelter CPI are separate measures. A price can remain historically high while becoming more affordable if income rises faster, or decline while affordability worsens when income falls or financing costs rise.</p></section>
      <PageLinks mode="canada" />
    </PageBody>
  </>
}

function HousingComparison() {
  return <>
    <PageHeader eyebrow="Explicit Canada–U.S. comparison" title={housingPageGeographies.comparison.title} description={housingPageGeographies.comparison.description} />
    <PageBody><section><p className="text-xs font-semibold uppercase text-petroleum">Canada</p><h2 className="mt-2 text-2xl font-semibold">Canadian purchase prices and shelter costs</h2><div className="mt-6"><ResearchTimeSeriesChart file="affordability-canada-housing-income.json" initialTransformation="raw" /></div><AffordabilityIndicatorGrid files={['canada/indicators/new-housing-price-index.json', 'canada/indicators/rent-cpi.json', 'canada/indicators/shelter-cpi.json']} /></section><section className="mt-16"><p className="text-xs font-semibold uppercase text-petroleum">United States</p><h2 className="mt-2 text-2xl font-semibold">U.S. purchase prices and shelter costs</h2><div className="mt-6"><ResearchTimeSeriesChart file="affordability-us-housing.json" initialTransformation="indexed" /></div><AffordabilityIndicatorGrid files={['us/indicators/us-fhfa-house-price-index.json', 'us/indicators/us-rent-cpi.json', 'us/indicators/us-shelter-cpi.json', 'us/indicators/us-owners-equivalent-rent-cpi.json']} /></section><PageLinks mode="comparison" /></PageBody>
  </>
}

export function HousingAffordability() { return <CanadaHousing /> }
export function CanadaHousingAffordability() { return <CanadaHousing /> }
export function GlobalHousingPrices() { return <GlobalHousing /> }
export function OwenSoundHousingAffordability() { return <OwenSoundHousing /> }
export function HousingComparisonPage() { return <HousingComparison /> }
