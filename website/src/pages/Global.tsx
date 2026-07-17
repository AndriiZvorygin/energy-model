import { Link } from "react-router-dom";
import { ArrowRight, Droplets, House, TrendingUp } from "lucide-react";
import { AffordabilityIndicatorGrid } from "../components/affordability/AffordabilityIndicatorGrid";
import { GeneratedRouteEvidenceSummary } from "../components/diagnostics/GeneratedRouteEvidenceSummary";
import { PageBody, PageHeader } from "../components/PageHeader";

export function Global() {
  return (
    <>
      <PageHeader
        eyebrow="Global geography"
        title="Global energy and affordability inputs"
        description="Global liquidity, benchmark oil prices, international food commodities, and international housing aggregates are presented here as global evidence. They may inform domestic analysis, but they are not Canadian observations."
      />
      <PageBody>
        <GeneratedRouteEvidenceSummary title="Global current evidence" />

        <section className="mt-12 border-y border-stone-300 py-7 dark:border-stone-700">
          <p className="text-xs font-semibold uppercase text-petroleum">International affordability context</p>
          <h2 className="mt-2 text-2xl font-semibold">Food commodities and residential property</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">
            FAO indices measure international commodity quotations, not grocery bills. BIS aggregates cover participating national property-price series rather than every dwelling worldwide.
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

        <div className="mt-12 grid gap-px border border-stone-200 bg-stone-200 md:grid-cols-3 dark:border-stone-800 dark:bg-stone-800">
          {[
            [TrendingUp, "Global liquidity", "Inspect G4 GM2 and its tested lead relationship with oil.", "/liquidity"],
            [Droplets, "Global oil market", "Inspect comparative inventory and physical oil-market state.", "/physical-market"],
            [House, "Canadian affordability", "Move from global inputs to Canadian household evidence.", "/affordability"],
          ].map(([Icon, title, description, route]) => {
            const Component = Icon as typeof TrendingUp;
            return (
              <Link key={String(title)} to={String(route)} className="bg-white p-6 hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900">
                <Component size={20} className="text-petroleum" />
                <h2 className="mt-4 text-lg font-semibold">{String(title)}</h2>
                <p className="mt-2 text-sm leading-6 text-stone-500">{String(description)}</p>
                <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">Open evidence <ArrowRight size={15} /></span>
              </Link>
            );
          })}
        </div>
      </PageBody>
    </>
  );
}
