import { AffordabilityIndicatorGrid } from "../components/affordability/AffordabilityIndicatorGrid";
import { ResearchTimeSeriesChart } from "../components/charts/ResearchTimeSeriesChart";
import { GeneratedRouteEvidenceSummary } from "../components/diagnostics/GeneratedRouteEvidenceSummary";
import { EvidenceGeographySelector } from "../components/diagnostics/EvidenceGeographySelector";
import { PageBody, PageHeader } from "../components/PageHeader";

export function HousingAffordability() {
  return (
    <>
      <PageHeader
        eyebrow="Affordability evidence"
        title="Housing purchase prices and shelter costs"
        description="Asset purchase prices, rent, mortgage interest, replacement costs, and shelter services remain separate so their different transmission paths stay visible."
      />
      <PageBody>
        <EvidenceGeographySelector />
        <GeneratedRouteEvidenceSummary />
        <section className="mt-12">
          <p className="text-xs font-semibold uppercase text-petroleum">
            1. Property purchase prices
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            Canadian new housing prices
          </h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
            The Statistics Canada NHPI covers new residential properties and
            separates the house structure from land. It is not a broad
            resale-market index.
          </p>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-housing.json"
              initialTransformation="indexed"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/new-housing-price-index.json",
              "canada/indicators/new-housing-house-component.json",
              "canada/indicators/new-housing-land-component.json",
              "canada/indicators/canada-nhpi-yoy.json",
            ]}
          />
        </section>
        <section className="mt-16">
          <p className="text-xs font-semibold uppercase text-petroleum">
            2–4. Rent, mortgage interest, and shelter CPI
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            Current housing-service costs can diverge from property prices
          </h2>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-housing-costs.json"
              initialTransformation="raw"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/rent-cpi.json",
              "canada/indicators/mortgage-interest-cost.json",
              "canada/indicators/homeowners-replacement-cost.json",
              "canada/indicators/shelter-cpi.json",
            ]}
          />
          <div className="mt-10">
            <ResearchTimeSeriesChart
              file="affordability-canada-mortgage-renewal.json"
              initialTransformation="raw"
            />
          </div>
        </section>
        <section className="mt-16">
          <p className="text-xs font-semibold uppercase text-petroleum">
            5. House prices and housing costs relative to income
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            Canadian purchasing power, quarterly aligned
          </h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
            Asset affordability compares purchase prices with income. Current
            housing-cost pressure compares rent, shelter, and mortgage interest
            with income. Monthly price indexes are averaged only across
            completed quarters, and all ratio components use a fixed 2017 Q1
            reference.
          </p>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-housing-income.json"
              initialTransformation="raw"
            />
          </div>
          <div className="mt-10">
            <ResearchTimeSeriesChart
              file="affordability-canada-housing-ratios.json"
              initialTransformation="raw"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/nhpi-to-income.json",
              "canada/indicators/real-nhpi.json",
              "canada/indicators/rent-to-income.json",
              "canada/indicators/shelter-to-income.json",
              "canada/indicators/mortgage-interest-to-income.json",
            ]}
          />
          <h2 className="mt-12 text-2xl font-semibold">
            Housing-cost divergence
          </h2>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-housing-gaps.json"
              initialTransformation="raw"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/nhpi-income-gap.json",
              "canada/indicators/rent-income-gap.json",
              "canada/indicators/shelter-income-gap.json",
              "canada/indicators/mortgage-income-gap.json",
            ]}
          />
          <h2 className="mt-12 text-2xl font-semibold">
            Broader official property-price audit
          </h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
            The broad official RPPI covers six metropolitan areas and ends in
            2021 Q4. Current metro condominium indexes cover new apartments
            only. They are shown as separate histories and are not spliced to
            NHPI or resale prices.
          </p>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-property-income.json"
              initialTransformation="indexed"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/six-cma-residential-property-price-index.json",
              "canada/indicators/residential-property-price-to-income.json",
              "canada/indicators/toronto-new-condominium-price-index.json",
              "canada/indicators/ottawa-new-condominium-price-index.json",
            ]}
          />
          <h2 className="mt-12 text-2xl font-semibold">
            United States comparison
          </h2>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-house-price-income.json"
              initialTransformation="indexed"
            />
          </div>
        </section>
        <section className="mt-16">
          <p className="text-xs font-semibold uppercase text-petroleum">
            6. International comparison
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            BIS selected real residential property prices
          </h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
            The world, advanced, and emerging aggregates cover participating
            national series and use BIS methodology; they are not a census of
            every home.
          </p>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-real-house-prices.json"
              initialTransformation="indexed"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "global/indicators/bis-real-house-prices.json",
              "global/indicators/bis-canada-real-house-prices.json",
              "global/indicators/bis-us-real-house-prices.json",
              "us/indicators/us-real-fhfa-house-price-index.json",
            ]}
          />
        </section>
        <section className="mt-16">
          <p className="text-xs font-semibold uppercase text-petroleum">
            U.S. housing detail
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            FHFA purchase prices and BLS shelter services
          </h2>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-us-housing.json"
              initialTransformation="indexed"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "us/indicators/us-fhfa-house-price-index.json",
              "us/indicators/us-rent-cpi.json",
              "us/indicators/us-shelter-cpi.json",
              "us/indicators/us-owners-equivalent-rent-cpi.json",
            ]}
          />
        </section>
        <section className="mt-16 border-y border-stone-300 py-6 dark:border-stone-700">
          <p className="text-xs font-semibold uppercase text-petroleum">
            7. Methods and limitations
          </p>
          <p className="mt-3 max-w-5xl text-sm leading-7 text-stone-600 dark:text-stone-300">
            NHPI, RPPI, condominium, FHFA, and BIS property-price indexes have
            different market coverage. Rent CPI measures renter costs,
            mortgage-interest cost responds to rates and renewals, replacement
            cost tracks structures, and shelter CPI combines current
            housing-service costs. A price can remain historically high while
            becoming more affordable if income rises faster, or decline while
            affordability worsens when income falls or financing costs rise. No
            series is silently spliced or averaged into one stress score.
          </p>
        </section>
      </PageBody>
    </>
  );
}
