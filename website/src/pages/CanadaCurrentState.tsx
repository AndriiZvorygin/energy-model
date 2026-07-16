import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CanadaGeographyControls } from "../components/CanadaGeographyControls";
import { CurrentStateIndicatorCard } from "../components/CurrentStateIndicatorCard";
import { ChartModal } from "../components/charts/ChartModal";
import { IndicatorHistoryChart } from "../components/charts/IndicatorHistoryChart";
import { LayerHistoryChart } from "../components/charts/LayerHistoryChart";
import type { IndicatorDataset } from "../components/charts/chartTypes";
import {
  useGeneratedJson,
  useIndicatorDatasets,
} from "../components/charts/useChartData";
import { PageBody, PageHeader } from "../components/PageHeader";
import { CanadianDiagnosticSummary } from "../components/diagnostics/CanadianDiagnosticSummary";
import { GeneratedRouteEvidenceSummary } from "../components/diagnostics/GeneratedRouteEvidenceSummary";
import type { CanadianClassification } from "../components/diagnostics/canadaTypes";

type CanadaManifest = {
  scope: string;
  generatedAt: string;
  defaultGeography: string;
  classificationImplemented: boolean;
  indicators: Array<{
    id: string;
    file: string;
    label: string;
    geography: string;
    layer: string;
    core: boolean;
    latestDate: string;
  }>;
};
type CanadaState = {
  status: string;
  latestObservationDate: string;
  notes: string[];
};

const layerOrder = [
  "Global oil and liquidity inputs",
  "Physical energy conditions",
  "Energy affordability and finance",
  "Food affordability",
  "Housing purchase prices and shelter costs",
  "Canadian purchasing power",
  "Production and output",
  "Labour and households",
];
const layerText: Record<string, string> = {
  "Global oil and liquidity inputs":
    "External global liquidity and benchmark oil conditions inherited from the existing locked research layer.",
  "Physical energy conditions":
    "Canadian production, trade, refinery inputs and inventories are shown separately; production is not treated as household affordability.",
  "Energy affordability and finance":
    "Domestic-currency oil, consumer energy prices, shelter, rates, exchange rates and debt service describe financial exposure.",
  "Food affordability":
    "Consumer food, grocery, and inflation-gap measures remain distinct from international commodity quotations and require income context.",
  "Housing purchase prices and shelter costs":
    "New-property purchase prices, rent, mortgage interest, replacement cost, and shelter services are separate housing evidence.",
  "Canadian purchasing power":
    "Quarterly household income and monthly worker wages provide separate denominators for food and housing affordability.",
  "Production and output":
    "Monthly real GDP by industry provides the main high-frequency Canadian output evidence.",
  "Labour and households":
    "Employment rates, participation, prime-age employment and job composition supplement unemployment.",
};

function CanadaStatePage({
  geography = "Canada",
  layer,
}: {
  geography?: "Canada" | "Ontario";
  layer?: string;
}) {
  const { data: manifest, error: manifestError } =
    useGeneratedJson<CanadaManifest>("canada/manifest.json");
  const { data: state } = useGeneratedJson<CanadaState>(
    "canada/current-state.json",
  );
  const { data: classification } = useGeneratedJson<CanadianClassification>(
    "canada/current-classification.json",
  );
  const [searchParams] = useSearchParams();
  const requested = searchParams.get("indicator");
  const entries = useMemo(
    () =>
      manifest?.indicators
        .filter(
          (item) =>
            ((item.geography === geography || item.geography === "Global") &&
              (!layer || item.layer === layer)) ||
            item.id === requested,
        )
        .map((item) => `canada/${item.file}`) ?? [],
    [manifest, geography, layer, requested],
  );
  const { indicators, error } = useIndicatorDatasets(entries);
  const [selected, setSelected] = useState<IndicatorDataset | null>(null);
  useEffect(() => {
    if (requested && indicators.length)
      setSelected(indicators.find((item) => item.id === requested) ?? null);
  }, [requested, indicators]);
  const visibleLayers = layer ? [layer] : layerOrder;
  const title =
    geography === "Ontario"
      ? "Ontario evidence with global inputs"
      : layer
        ? `Canadian ${layer.toLowerCase()}`
        : "Canadian current state";
  if (manifestError || error)
    return (
      <>
        <PageHeader
          eyebrow="Canadian evidence"
          title={title}
          description="The Canadian generated dataset could not be loaded."
        />
        <PageBody>
          <p className="text-sm text-amber-700">{manifestError ?? error}</p>
        </PageBody>
      </>
    );
  return (
    <>
      <PageHeader
        eyebrow="Canadian-centred research"
        title={title}
        description="Canadian evidence is shown with its own history, definitions and source dates. The provisional classifier preserves national, Ontario, Alberta, and global contributions separately."
      />
      <PageBody>
        <CanadaGeographyControls />
        {!manifest || !state || !indicators.length ? (
          <div className="flex h-64 items-center justify-center text-sm text-stone-500">
            Loading Canadian indicator histories…
          </div>
        ) : (
          <>
            {classification && geography === "Canada" && !layer ? (
              <>
                <section className="mt-8">
                  <CanadianDiagnosticSummary
                    classification={classification}
                    compact
                  />
                </section>
                <div className="mt-8">
                  <GeneratedRouteEvidenceSummary />
                </div>
              </>
            ) : (
              <section className="mt-8 border-y border-stone-300 py-6 dark:border-stone-700">
                <p className="text-xs font-semibold uppercase text-petroleum">
                  Evidence status
                </p>
                <h2 className="mt-2 text-2xl font-semibold">{state.status}</h2>
                <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-stone-500">Formal scope</p>
                    <p className="mt-1 font-medium">{manifest.scope}</p>
                  </div>
                  <div>
                    <p className="text-stone-500">Newest observation</p>
                    <p className="mt-1 font-medium">
                      {state.latestObservationDate.slice(0, 7)}
                    </p>
                  </div>
                  <div>
                    <p className="text-stone-500">Displayed geography</p>
                    <p className="mt-1 font-medium">
                      {geography} with global inputs
                    </p>
                  </div>
                  <div>
                    <p className="text-stone-500">Classifier</p>
                    <p className="mt-1 font-medium">
                      Provisional Canadian rules
                    </p>
                  </div>
                </div>
                <p className="mt-4 text-xs leading-5 text-stone-500">
                  {state.notes.join(" ")}
                </p>
              </section>
            )}
            <div className="mt-12 space-y-16">
              {visibleLayers.map((layerName) => {
                const rows = indicators.filter(
                  (item) => item.layer === layerName,
                );
                if (!rows.length) return null;
                return (
                  <section key={layerName}>
                    <div className="border-b border-stone-300 pb-4 dark:border-stone-700">
                      <p className="text-xs font-semibold uppercase text-petroleum">
                        {geography === "Ontario" &&
                        layerName !== "Global oil and liquidity inputs"
                          ? "Ontario regional context"
                          : "Evidence layer"}
                      </p>
                      <h2 className="mt-2 text-2xl font-semibold">
                        {layerName}
                      </h2>
                      <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
                        {layerText[layerName]}
                      </p>
                    </div>
                    <div className="mt-6">
                      <LayerHistoryChart indicators={rows} />
                    </div>
                    <div className="mt-6 grid gap-4 xl:grid-cols-2">
                      {rows.map((indicator) => (
                        <CurrentStateIndicatorCard
                          key={indicator.id}
                          indicator={indicator}
                          onExpand={() => setSelected(indicator)}
                          showEvidenceContext
                        />
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          </>
        )}
        <ChartModal
          open={Boolean(selected)}
          title={selected?.label ?? "Canadian indicator history"}
          onClose={() => setSelected(null)}
        >
          {selected && <IndicatorHistoryChart indicator={selected} />}
        </ChartModal>
      </PageBody>
    </>
  );
}

export function CanadaCurrentState() {
  return <CanadaStatePage />;
}
export function CanadaEnergy() {
  return <CanadaStatePage layer="Physical energy conditions" />;
}
export function CanadaEconomy() {
  return <CanadaStatePage layer="Production and output" />;
}
export function CanadaLabour() {
  return <CanadaStatePage layer="Labour and households" />;
}
export function CanadaHouseholds() {
  return <CanadaStatePage layer="Energy affordability and finance" />;
}
export function CanadaOntario() {
  return <CanadaStatePage geography="Ontario" />;
}
