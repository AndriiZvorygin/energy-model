import { ArrowRight, Banknote, Factory, MapPin, Pickaxe } from "lucide-react";
import { Link } from "react-router-dom";
import { CanadaGeographyControls } from "../components/CanadaGeographyControls";
import { GeneratedEvidenceSummary } from "../components/diagnostics/GeneratedEvidenceSummary";
import { PageBody, PageHeader } from "../components/PageHeader";

export function Canada() {
  return (
    <>
      <PageHeader
        eyebrow="Primary domestic geography"
        title="Canadian energy-economic conditions"
        description="Canada is the observatory's domestic evidence layer, interpreted alongside global liquidity and oil markets without replacing the locked benchmark model or the U.S. comparison dataset."
      />
      <PageBody>
        <CanadaGeographyControls />
        <div className="mt-8">
          <GeneratedEvidenceSummary topic="canada" />
        </div>
        <section className="mt-10">
          <p className="max-w-4xl text-lg leading-8 text-stone-600 dark:text-stone-300">
            This release adds a provisional transparent Canadian classifier over
            the existing evidence. Household stress remains unevaluable, and
            Ontario and Alberta contributions stay separate.
          </p>
          <div className="mt-8 grid gap-px border border-stone-200 bg-stone-200 md:grid-cols-2 dark:border-stone-800 dark:bg-stone-800">
            {[
              [
                Pickaxe,
                "Energy",
                "Production, exports, imports, refinery inputs and inventories remain distinct.",
                "/canada/energy",
              ],
              [
                Factory,
                "Economy",
                "Monthly GDP by industry anchors high-frequency Canadian output.",
                "/canada/economy",
              ],
              [
                Banknote,
                "Labour and households",
                "Employment rates and population alignment qualify unemployment.",
                "/canada/labour",
              ],
              [
                MapPin,
                "Ontario context",
                "Provincial CPI and labour evidence inherits only explicit global inputs.",
                "/canada/ontario",
              ],
              [
                Factory,
                "Canadian regimes",
                "Compare eight provisional states, coverage, freshness and regional evidence.",
                "/canada/regimes",
              ],
              [
                Banknote,
                "Canadian symptoms",
                "Inspect active, emerging, fading, inactive and unavailable patterns.",
                "/canada/symptoms",
              ],
            ].map(([Icon, title, text, to]) => {
              const Component = Icon as typeof Pickaxe;
              return (
                <Link
                  key={String(title)}
                  to={String(to)}
                  className="bg-white p-6 hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"
                >
                  <Component size={21} className="text-petroleum" />
                  <h2 className="mt-4 text-xl font-semibold">
                    {String(title)}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-stone-500">
                    {String(text)}
                  </p>
                  <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">
                    Open evidence <ArrowRight size={15} />
                  </span>
                </Link>
              );
            })}
          </div>
        </section>
      </PageBody>
    </>
  );
}
