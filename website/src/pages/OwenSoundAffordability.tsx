import { Link } from 'react-router-dom'
import { GeneratedRouteEvidenceSummary } from '../components/diagnostics/GeneratedRouteEvidenceSummary'
import { EvidenceGeographySelector } from '../components/diagnostics/EvidenceGeographySelector'
import { PageBody, PageHeader } from '../components/PageHeader'

export function OwenSoundAffordability() {
  return (
    <>
      <PageHeader
        eyebrow="Owen Sound city-CSD evidence"
        title="Owen Sound household affordability"
        description="Local household, shelter, food-security, and matched basic-needs evidence for the Owen Sound census subdivision. Canadian evidence is linked as context, not substituted for local observations."
      />
      <PageBody>
        <EvidenceGeographySelector />
        <GeneratedRouteEvidenceSummary title="Owen Sound local affordability evidence" />
        <section className="mt-10 border-y border-stone-300 py-6 dark:border-stone-700">
          <p className="text-xs font-semibold uppercase text-petroleum">Local evidence boundary</p>
          <h2 className="mt-2 text-2xl font-semibold">What is actually measured locally</h2>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">
            The local headline uses Owen Sound city-CSD shelter burden, core housing need, food insecurity, Grey Bruce food-basket observations, and matched city household cases where available. The 2021 Census and newer regional observations do not form a continuous annual city affordability series.
          </p>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-stone-600 dark:text-stone-300">
            City-level income, tenure, rent, and food-cost gaps remain explicit data limitations. No Canadian, Toronto, U.S., FAO, or BIS observation is presented as an Owen Sound observation.
          </p>
          <Link className="mt-5 inline-flex text-sm font-semibold text-petroleum underline" to="/canada/food">See Canadian food evidence as broader context</Link>
        </section>
      </PageBody>
    </>
  )
}
