import { Link } from "react-router-dom";
import { CanadaGeographyControls } from "../components/CanadaGeographyControls";
import { useGeneratedJson } from "../components/charts/useChartData";
import { CanadianDiagnosticSummary } from "../components/diagnostics/CanadianDiagnosticSummary";
import { GeneratedRouteEvidenceSummary } from "../components/diagnostics/GeneratedRouteEvidenceSummary";
import type {
  CanadianClassification,
  CanadianCondition,
  CanadianRegimePayload,
} from "../components/diagnostics/canadaTypes";
import { RegimeScoreChart } from "../components/diagnostics/RegimeScoreChart";
import { PageBody, PageHeader } from "../components/PageHeader";

function Evidence({
  title,
  rows,
}: {
  title: string;
  rows: CanadianCondition[];
}) {
  return (
    <div>
      <h3 className="font-semibold">{title}</h3>
      {rows.length ? (
        <ul className="mt-3 divide-y divide-stone-200 border-y border-stone-200 text-sm dark:divide-stone-800 dark:border-stone-800">
          {rows.slice(0, 8).map((row) => (
            <li
              key={`${title}-${row.indicator}`}
              className="flex items-start justify-between gap-4 py-3"
            >
              <div>
                {row.indicatorId ? (
                  <Link
                    className="font-medium underline decoration-stone-300 underline-offset-2"
                    to={`/canada/current-state?indicator=${row.indicatorId}`}
                  >
                    {row.label}
                  </Link>
                ) : (
                  row.label
                )}
                <p className="mt-1 text-xs text-stone-500">
                  {row.evidenceScope} ·{" "}
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
        <p className="mt-3 text-sm text-stone-500">
          No evidence in this category.
        </p>
      )}
    </div>
  );
}

export function CanadaRegimes() {
  const { data: current, error } = useGeneratedJson<CanadianClassification>(
    "canada/current-classification.json",
  );
  const { data: regimes } = useGeneratedJson<CanadianRegimePayload>(
    "canada/regime-scores.json",
  );
  return (
    <>
      <PageHeader
        eyebrow="Provisional Canadian classifier"
        title="Canadian regime evidence"
        description="Eight transparent candidate states are scored from Canadian historical distributions. Close candidates remain mixed, regional opposition remains visible, and incomplete household evidence lowers confidence."
      />
      <PageBody>
        <CanadaGeographyControls />
        <div className="mt-8">
          <GeneratedRouteEvidenceSummary title="Current regime evidence map" />
        </div>
        {error && <p className="mt-8 text-amber-700">{error}</p>}
        {!current ? (
          <p className="py-20 text-sm text-stone-500">
            Loading Canadian classification…
          </p>
        ) : (
          <>
            <div className="mt-8">
              <CanadianDiagnosticSummary classification={current} />
            </div>
            <section className="mt-12">
              <p className="text-xs font-semibold uppercase text-petroleum">
                Candidate comparison
              </p>
              <h2 className="mt-2 text-2xl font-semibold">
                All Canadian regime scores
              </h2>
              <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-500">
                A single state requires at least 70% availability, a 60% top
                score, and a ten-point margin. Freshness-adjusted coverage is
                displayed separately and informs confidence.
              </p>
              {regimes && (
                <div className="mt-6">
                  <RegimeScoreChart scores={regimes.scores} />
                </div>
              )}
            </section>
            <section className="mt-12 grid gap-8 lg:grid-cols-2">
              <Evidence
                title="Strongest supporting evidence"
                rows={current.supportingEvidence}
              />
              <Evidence
                title="Strongest conflicting evidence"
                rows={current.conflictingEvidence}
              />
            </section>
            <section className="mt-12">
              <h2 className="text-xl font-semibold">Historical analogues</h2>
              <p className="mt-2 text-sm text-stone-500">
                Similarity compares available Canadian-series percentiles. It is
                historical context, not proof of causation.
              </p>
              <div className="mt-5 grid gap-4 md:grid-cols-3">
                {current.historicalAnalogues.map((item) => (
                  <div
                    key={item.episode}
                    className="border-t-2 border-stone-400 pt-3"
                  >
                    <p className="font-semibold">{item.episode}</p>
                    <p className="mt-2 text-sm text-stone-500">
                      {(item.similarity * 100).toFixed(0)}% similarity across{" "}
                      {item.commonIndicators} fields
                    </p>
                  </div>
                ))}
              </div>
            </section>
            <section className="mt-12 border-y border-stone-300 py-6 dark:border-stone-700">
              <h2 className="text-xl font-semibold">Confidence limitations</h2>
              <ul className="mt-4 space-y-2 text-sm leading-6 text-stone-600 dark:text-stone-300">
                {current.limitations.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            </section>
          </>
        )}
      </PageBody>
    </>
  );
}
