import { ArrowRight, House, ShoppingBasket } from "lucide-react";
import { Link } from "react-router-dom";
import { AffordabilityIndicatorGrid } from "../components/affordability/AffordabilityIndicatorGrid";
import { ResearchTimeSeriesChart } from "../components/charts/ResearchTimeSeriesChart";
import { GeneratedEvidenceSummary } from "../components/diagnostics/GeneratedEvidenceSummary";
import { PageBody, PageHeader } from "../components/PageHeader";

export function Affordability() {
  return (
    <>
      <PageHeader
        eyebrow="Global and domestic price evidence"
        title="Food and housing affordability"
        description="International commodities, domestic prices, household income, wages, property purchase prices, and current shelter costs are related but distinct evidence layers."
      />
      <PageBody>
        <GeneratedEvidenceSummary
          topic="affordability"
          title="Household affordability evidence"
        />
        <section className="mt-12 border-y border-stone-300 py-6 dark:border-stone-700">
          <h2 className="text-2xl font-semibold">Global current evidence</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">
            FAO indices measure international commodity quotations, not grocery
            bills. BIS aggregates cover participating national property-price
            series rather than every dwelling worldwide.
          </p>
          <AffordabilityIndicatorGrid
            files={[
              "global/indicators/fao-food-price-index.json",
              "global/indicators/fao-food-price-index-real.json",
              "global/indicators/bis-real-house-prices.json",
              "global/indicators/bis-advanced-real-house-prices.json",
            ]}
          />
        </section>
        <section className="mt-14">
          <p className="text-xs font-semibold uppercase text-petroleum">
            Canadian purchasing power
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            Prices in relation to income and wages
          </h2>
          <p className="mt-3 max-w-5xl text-sm leading-7 text-stone-600 dark:text-stone-300">
            Price inflation measures how quickly a price index changes.
            Affordability compares that change with household income or wages.
            Asset affordability compares purchase prices with income, while
            current housing-cost pressure compares rent, shelter, and mortgage
            interest with income. A price can be historically high while
            becoming more affordable when income rises faster. A price can also
            fall while affordability worsens when income declines or financing
            costs rise.
          </p>
          <div className="mt-6">
            <ResearchTimeSeriesChart
              file="affordability-canada-purchasing-power.json"
              initialTransformation="indexed"
            />
          </div>
          <div className="mt-10">
            <ResearchTimeSeriesChart
              file="affordability-canada-wages.json"
              initialTransformation="indexed"
            />
          </div>
          <AffordabilityIndicatorGrid
            files={[
              "canada/indicators/real-disposable-income-per-person.json",
              "canada/indicators/real-wage-growth.json",
              "canada/indicators/household-saving-rate.json",
              "canada/indicators/food-to-income.json",
              "canada/indicators/rent-to-income.json",
              "canada/indicators/shelter-to-income.json",
              "canada/indicators/mortgage-interest-to-income.json",
              "canada/indicators/nhpi-to-income.json",
            ]}
          />
        </section>
        <div className="mt-12 grid gap-px border border-stone-200 bg-stone-200 md:grid-cols-2 dark:border-stone-800 dark:bg-stone-800">
          <Link
            to="/affordability/food"
            className="bg-white p-6 hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"
          >
            <ShoppingBasket className="text-petroleum" />
            <h2 className="mt-4 text-xl font-semibold">Food-price evidence</h2>
            <p className="mt-2 text-sm leading-6 text-stone-500">
              Commodity pressure, Canadian and U.S. retail prices, transmission
              lags, wages, and household income.
            </p>
            <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">
              Explore food evidence <ArrowRight size={15} />
            </span>
          </Link>
          <Link
            to="/affordability/housing"
            className="bg-white p-6 hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"
          >
            <House className="text-petroleum" />
            <h2 className="mt-4 text-xl font-semibold">
              Housing-price evidence
            </h2>
            <p className="mt-2 text-sm leading-6 text-stone-500">
              Purchase prices, rent, mortgage interest, shelter services,
              income, and international comparisons.
            </p>
            <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">
              Explore housing evidence <ArrowRight size={15} />
            </span>
          </Link>
        </div>
      </PageBody>
    </>
  );
}
