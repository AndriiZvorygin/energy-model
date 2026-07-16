import { useMemo } from "react";
import { Link } from "react-router-dom";
import { EvidenceLabel } from "../components/EvidenceLabel";
import { CanadaGeographyControls } from "../components/CanadaGeographyControls";
import { LayerHistoryChart } from "../components/charts/LayerHistoryChart";
import type { IndicatorDataset } from "../components/charts/chartTypes";
import {
  useGeneratedJson,
  useIndicatorDatasets,
} from "../components/charts/useChartData";
import type {
  CanadianCondition,
  CanadianSymptomPayload,
} from "../components/diagnostics/canadaTypes";
import { GeneratedEvidenceSummary } from "../components/diagnostics/GeneratedEvidenceSummary";
import { GeneratedRouteEvidenceSummary } from "../components/diagnostics/GeneratedRouteEvidenceSummary";
import { PageBody, PageHeader } from "../components/PageHeader";

type CanadaManifest = { indicators: Array<{ id: string; file: string }> };
const tones: Record<string, string> = {
  active:
    "border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200",
  emerging:
    "border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  fading:
    "border-sky-500 bg-sky-50 text-sky-800 dark:bg-sky-950/40 dark:text-sky-200",
  inactive:
    "border-stone-400 bg-stone-50 text-stone-700 dark:bg-stone-900 dark:text-stone-200",
  insufficient_data:
    "border-stone-400 bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-300",
};
const month = (value: string) =>
  new Intl.DateTimeFormat("en-CA", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value.slice(0, 10)}T00:00:00Z`));

function Conditions({
  title,
  rows,
}: {
  title: string;
  rows: CanadianCondition[];
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold">{title}</h4>
      {rows.length ? (
        <ul className="mt-2 divide-y divide-stone-200 border-y border-stone-200 text-sm dark:divide-stone-800 dark:border-stone-800">
          {rows.map((row) => (
            <li
              key={`${title}-${row.indicator}-${row.transformation}`}
              className="grid gap-2 py-3 sm:grid-cols-[28px_1fr_auto]"
            >
              <span
                className={`font-bold ${!row.available ? "text-stone-500" : row.met ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"}`}
              >
                {!row.available ? "~" : row.met ? "✓" : "×"}
              </span>
              <div>
                {row.indicatorId ? (
                  <Link
                    className="font-medium underline decoration-stone-300 underline-offset-2 hover:text-petroleum"
                    to={`/canada/current-state?indicator=${row.indicatorId}`}
                  >
                    {row.label}
                  </Link>
                ) : (
                  <span className="font-medium">{row.label}</span>
                )}
                <p className="mt-1 text-xs text-stone-500">
                  {row.evidenceScope ?? row.geography ?? "Canadian evidence"} ·
                  expected {row.expectedDirection} · observation{" "}
                  {row.sourceDate?.slice(0, 7) ?? "missing"}
                </p>
              </div>
              <span className="text-xs text-stone-500">
                {row.historicalPercentile === null
                  ? "n/a"
                  : `P${row.historicalPercentile.toFixed(0)}`}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-stone-500">None recorded.</p>
      )}
    </div>
  );
}

export function CanadaSymptoms() {
  const { data, error } = useGeneratedJson<CanadianSymptomPayload>(
    "canada/symptom-evaluations.json",
  );
  const { data: manifest } = useGeneratedJson<CanadaManifest>(
    "canada/manifest.json",
  );
  const files = useMemo(
    () => manifest?.indicators.map((item) => `canada/${item.file}`) ?? [],
    [manifest],
  );
  const { indicators } = useIndicatorDatasets(files);
  const byId = useMemo(
    () => new Map(indicators.map((item) => [item.id, item])),
    [indicators],
  );
  return (
    <>
      <PageHeader
        eyebrow="Provisional Canadian diagnostic"
        title="Canadian symptom evidence"
        description="Six transparent rules show which patterns can be evaluated now. Household stress remains explicitly unevaluable until the missing household evidence is implemented."
      />
      <PageBody>
        <CanadaGeographyControls />
        <div className="mt-8">
          <GeneratedRouteEvidenceSummary />
        </div>
        {error && <p className="mt-8 text-amber-700">{error}</p>}
        {!data ? (
          <p className="py-20 text-sm text-stone-500">
            Loading Canadian symptoms…
          </p>
        ) : (
          <>
            <section className="mt-8 border-y border-stone-300 py-5 text-sm dark:border-stone-700">
              <p>
                <strong>Scope:</strong> {data.scope}
              </p>
              <p className="mt-2 text-stone-500">
                Evaluation {month(data.date)} · availability{" "}
                {(data.clock.requiredIndicatorAvailability * 100).toFixed(0)}% ·
                freshness-adjusted{" "}
                {(data.clock.freshnessAdjustedCoverage * 100).toFixed(0)}% ·
                retrospective revised data
              </p>
            </section>
            <div className="mt-10 space-y-10">
              {data.evaluations.map((item) => {
                const evidenceRows = [
                  ...item.requiredConditionResults,
                  ...item.confirmingEvidence,
                  ...item.conflictingEvidence,
                ] as CanadianCondition[];
                const chartIndicators = [
                  ...new Set(
                    evidenceRows.map((row) => row.indicatorId).filter(Boolean),
                  ),
                ]
                  .map((id) => byId.get(String(id)))
                  .filter((row): row is IndicatorDataset => Boolean(row));
                return (
                  <article
                    key={item.id}
                    className="border-t border-stone-300 pt-6 dark:border-stone-700"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <span
                          className={`inline-flex border-l-4 px-3 py-1 text-xs font-semibold uppercase ${tones[item.status]}`}
                        >
                          {item.statusLabel}
                        </span>
                        <h2 className="mt-3 text-2xl font-semibold">
                          {item.name}
                        </h2>
                      </div>
                      <EvidenceLabel label={item.evidenceLabel} />
                    </div>
                    <p className="mt-3 max-w-4xl leading-7 text-stone-700 dark:text-stone-300">
                      {item.plainLanguageMeaning}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-5 text-xs text-stone-500">
                      <span>Confidence {item.confidence}</span>
                      <span>Coverage {(item.coverage * 100).toFixed(0)}%</span>
                      <span>
                        Persistence {item.persistence.consecutiveUpdates}/
                        {item.persistence.requiredForActive}
                      </span>
                      <span>Score {(item.score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="mt-6">
                      <GeneratedEvidenceSummary
                        topic={`symptom_canada_${item.id}`}
                        title="Why is this symptom active or inactive?"
                      />
                    </div>
                    <details className="mt-6 border-y border-stone-200 py-4 dark:border-stone-800">
                      <summary className="cursor-pointer font-semibold">
                        Evidence, charts, and rule details
                      </summary>
                      <div className="mt-6 space-y-7">
                        <Conditions
                          title="Required evidence"
                          rows={
                            item.requiredConditionResults as CanadianCondition[]
                          }
                        />
                        <div className="grid gap-7 lg:grid-cols-2">
                          <Conditions
                            title="Confirming evidence met"
                            rows={
                              item.confirmingEvidence as CanadianCondition[]
                            }
                          />
                          <Conditions
                            title="Conflicting evidence met"
                            rows={
                              item.conflictingEvidence as CanadianCondition[]
                            }
                          />
                        </div>
                        {chartIndicators.length > 0 && (
                          <LayerHistoryChart indicators={chartIndicators} />
                        )}
                        <div className="grid gap-7 text-sm lg:grid-cols-3">
                          <div>
                            <h4 className="font-semibold">
                              Historical analogues
                            </h4>
                            <p className="mt-2 text-stone-500">
                              {item.historicalAnalogues.join(", ")}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-semibold">
                              Alternative explanations
                            </h4>
                            <p className="mt-2 text-stone-500">
                              {item.alternativeExplanations.join("; ")}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-semibold">Limitations</h4>
                            <p className="mt-2 text-stone-500">
                              {item.limitations.join(" ")}
                            </p>
                          </div>
                        </div>
                      </div>
                    </details>
                  </article>
                );
              })}
            </div>
          </>
        )}
      </PageBody>
    </>
  );
}
