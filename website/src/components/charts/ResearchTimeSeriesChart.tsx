import { useEffect, useMemo, useState } from "react";
import {
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EvidenceLabel } from "../EvidenceLabel";
import { AccessibleChartTable } from "./AccessibleChartTable";
import { ChartDownloadMenu } from "./ChartDownloadMenu";
import { ChartDetails } from "./ChartDetails";
import { EventAnnotations } from "./EventAnnotations";
import { LatestValuesPanel } from "./LatestValuesPanel";
import { NormalizationControls } from "./NormalizationControls";
import { RecessionOverlay } from "./RecessionOverlay";
import { RegimeOverlay } from "./RegimeOverlay";
import { SeriesControls } from "./SeriesControls";
import { TimeRangeControls } from "./TimeRangeControls";
import type {
  ChartDataset,
  ChartObservation,
  ChartSeries,
  ChartState,
  Transformation,
} from "./chartTypes";
import {
  chartStateSearch,
  correlation,
  parseChartState,
  rangeRows,
  referenceStatistics,
  shiftSeries,
  transformObservations,
} from "./chartUtils";
import {
  useChartContext,
  useChartDataset,
  useCrossLayerData,
} from "./useChartData";

type ResearchTimeSeriesChartProps = {
  file: string;
  initialSeries?: string[];
  initialTransformation?: Transformation;
  syncUrl?: boolean;
  lagControl?: boolean;
  inspectCrossLayer?: boolean;
  showRegimes?: boolean;
  showRecessions?: boolean;
};

const transformedUnit = (transformation: Transformation, raw: string) =>
  transformation === "zscore"
    ? "standard deviations"
    : transformation === "indexed"
      ? "index (start = 100)"
      : ["yoy", "pct_change"].includes(transformation)
        ? "percent"
        : raw;
const dateLabel = (date: string, frequency: string) =>
  new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: frequency === "annual" ? undefined : "short",
  }).format(new Date(`${date}T00:00:00Z`));
const formatValue = (value: unknown) =>
  typeof value === "number"
    ? new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value)
    : "Missing";
const fallbackFigures: Record<string, string> = {
  "oil-price-layers.json": "final_oil_price_layers_time_series.png",
  "gm2-oil-lead.json": "final_gm2_leads_oil_time_series.png",
  "oil-residual-ci.json": "final_oil_residual_ci_time_series.png",
  "energy-gdp.json": "final_energy_gdp_time_series.png",
  "oil-equities.json": "sp500_vs_wti_yoy.png",
  "uso-tracking.json": "uso_vs_wti_yoy.png",
};

function ResearchTooltip({
  active,
  label,
  payload,
  frequency,
  compact,
  dataset,
  transformation,
  statistics,
  lag,
}: {
  active?: boolean;
  label?: string;
  payload?: {
    value?: number;
    dataKey?: string;
    color?: string;
    name?: string;
    payload?: ChartObservation;
  }[];
  frequency: string;
  compact: boolean;
  dataset: ChartDataset;
  transformation: Transformation;
  statistics: ReturnType<typeof referenceStatistics>;
  lag?: number;
}) {
  if (!active || !label || !payload?.length) return null;
  return (
    <div className="max-w-80 border border-stone-200 bg-white p-3 text-xs shadow-lg dark:border-stone-700 dark:bg-[#18201d]">
      <p className="font-semibold">
        Displayed comparison month: {dateLabel(label, frequency)}
      </p>
      {payload.slice(0, compact ? 3 : undefined).map((item) => {
        const key = String(item.dataKey);
        const raw = item.payload?.[`__raw_${key}`];
        const sourceDate = item.payload?.[`__sourceDate_${key}`];
        const stat = statistics[key];
        return (
          <div
            key={key}
            className="mt-2 border-t border-stone-100 pt-2 first:border-0 first:pt-0 dark:border-stone-700"
          >
            <p className="flex justify-between gap-4">
              <span style={{ color: item.color }}>{item.name}</span>
              <strong>{formatValue(item.value)}</strong>
            </p>
            {transformation === "zscore" && (
              <>
                <p>Raw observation: {formatValue(raw)}</p>
                <p>
                  Historical mean / std. dev.: {formatValue(stat?.mean)} /{" "}
                  {formatValue(stat?.standardDeviation)}
                </p>
                <p>
                  Reference:{" "}
                  {dataset.transformation.referenceStart?.slice(0, 7)} to{" "}
                  {dataset.transformation.referenceEnd?.slice(0, 7)}
                </p>
              </>
            )}
            {typeof sourceDate === "string" && (
              <>
                <p>Original observation month: {sourceDate.slice(0, 7)}</p>
                <p>
                  Selected lag: {lag} months (
                  {lag === 5 ? "locked" : "exploratory"})
                </p>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ResearchTimeSeriesChart({
  file,
  initialSeries,
  initialTransformation = "raw",
  syncUrl = true,
  lagControl = false,
  inspectCrossLayer = false,
  showRegimes = true,
  showRecessions = true,
}: ResearchTimeSeriesChartProps) {
  const { dataset, error } = useChartDataset(file);
  const { events, regimes, recessions } = useChartContext();
  const crossLayer = useCrossLayerData(inspectCrossLayer);
  const defaults = useMemo<ChartState>(
    () => ({
      series: initialSeries ?? [],
      transformation: initialTransformation,
      range: "all",
      lag: lagControl ? 5 : undefined,
    }),
    [initialSeries, initialTransformation, lagControl],
  );
  const [state, setState] = useState<ChartState>(() =>
    syncUrl ? parseChartState(window.location.search, defaults) : defaults,
  );
  const [focused, setFocused] = useState<string | null>(null);
  const [lockedDate, setLockedDate] = useState<string | null>(null);
  const [eventId, setEventId] = useState<string | null>(null);
  const [regimesEnabled, setRegimesEnabled] = useState(showRegimes);
  const [recessionsEnabled, setRecessionsEnabled] = useState(showRecessions);
  const [eventsEnabled, setEventsEnabled] = useState(true);

  useEffect(() => {
    if (!dataset || state.series.length) return;
    setState((current) => ({
      ...current,
      series: dataset.series
        .filter((item) => item.defaultVisible)
        .map((item) => item.key),
    }));
  }, [dataset, state.series.length]);
  useEffect(() => {
    if (!syncUrl || !dataset) return;
    const query = chartStateSearch(state);
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`,
    );
  }, [dataset, state, syncUrl]);

  const prepared = useMemo(() => {
    if (!dataset)
      return {
        rows: [],
        series: [] as ChartSeries[],
        baselineStats: {},
        stats: null,
        overlap: null,
      };
    const lag = state.lag ?? 5;
    const virtual = lagControl
      ? {
          ...dataset.series.find((item) => item.key === "GM2_YoY")!,
          key: "GM2_shifted",
          label: `GM2 shifted +${lag}m`,
          defaultVisible: true,
          color: "#d97706",
        }
      : null;
    const series = virtual ? [...dataset.series, virtual] : dataset.series;
    const shifted = virtual
      ? shiftSeries(dataset.observations, "GM2_YoY", lag, "GM2_shifted")
      : dataset.observations;
    const ranged = rangeRows(shifted, state.range, state.from, state.to);
    const baselineStats = referenceStatistics(
      shifted,
      series,
      dataset.transformation.referenceStart,
      dataset.transformation.referenceEnd,
    );
    const transformed = transformObservations(
      ranged,
      series,
      dataset.availableTransformations.includes(state.transformation)
        ? state.transformation
        : initialTransformation,
      shifted,
      baselineStats,
    );
    const overlapRows = virtual
      ? shifted.filter(
          (row) =>
            typeof row.GM2_shifted === "number" &&
            typeof row.WTI_YoY === "number",
        )
      : [];
    return {
      rows: transformed,
      series,
      baselineStats,
      stats: virtual ? correlation(shifted, "GM2_shifted", "WTI_YoY") : null,
      overlap: overlapRows.length
        ? {
            start: overlapRows[0].date,
            end: overlapRows[overlapRows.length - 1].date,
          }
        : null,
    };
  }, [
    dataset,
    initialTransformation,
    lagControl,
    state.from,
    state.lag,
    state.range,
    state.to,
    state.transformation,
  ]);

  if (error)
    return (
      <div className="border border-amber-300 bg-amber-50 p-5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
        <p>Interactive data could not be loaded: {error}</p>
        {fallbackFigures[file] && (
          <img
            src={`${import.meta.env.BASE_URL}charts/${fallbackFigures[file]}`}
            alt="Static publication fallback"
            className="mt-4 w-full"
          />
        )}
      </div>
    );
  if (!dataset)
    return (
      <div className="flex h-80 items-center justify-center border border-stone-200 text-sm text-stone-500 dark:border-stone-800">
        Loading full-resolution research data…
      </div>
    );

  const visibleKeys = new Set(state.series);
  const visibleSeries = prepared.series.filter((item) =>
    visibleKeys.has(item.key),
  );
  const displaySeries = visibleSeries.map((item) => ({
    ...item,
    unit: transformedUnit(state.transformation, item.unit),
  }));
  const validTransformations = dataset.availableTransformations.filter(
    (transformation) =>
      visibleSeries.every((item) =>
        (item.transformations ?? dataset.availableTransformations).includes(
          transformation,
        ),
      ),
  );
  const unitGroups = visibleSeries.reduce<Record<string, ChartSeries[]>>(
    (result, item) => {
      (result[item.unit] ??= []).push(item);
      return result;
    },
    {},
  );
  const groups: [string, ChartSeries[]][] =
    state.transformation === "raw"
      ? Object.entries(unitGroups)
      : [[transformedUnit(state.transformation, ""), visibleSeries]];
  const activeEvents = events.filter(
    (event) =>
      dataset.annotations.includes(event.id) &&
      event.start <= (dataset.dateRange.end ?? "") &&
      event.end >= (dataset.dateRange.start ?? ""),
  );
  const selectedEvent = activeEvents.find((event) => event.id === eventId);
  const lockedRow = lockedDate
    ? prepared.rows.find((row) => row.date === lockedDate)
    : null;
  const crossRow = lockedDate
    ? crossLayer.find((row) => row.date === lockedDate)
    : null;
  const lockedPerformance = dataset.methodology.lockedPerformance as
    | {
        windowMonths?: number;
        rmse?: number;
        mae?: number;
        r2?: number;
        n?: number;
      }
    | undefined;
  const updateSeries = (key: string) =>
    setState((current) => {
      const nextSeries = current.series.includes(key)
        ? current.series.filter((item) => item !== key)
        : [...current.series, key];
      const metadata = prepared.series.filter((item) =>
        nextSeries.includes(item.key),
      );
      const allowed = dataset.availableTransformations.filter(
        (transformation) =>
          metadata.every((item) =>
            (item.transformations ?? dataset.availableTransformations).includes(
              transformation,
            ),
          ),
      );
      return {
        ...current,
        series: nextSeries,
        transformation: allowed.includes(current.transformation)
          ? current.transformation
          : (allowed[0] ?? "raw"),
      };
    });

  return (
    <section
      className="border-y border-stone-200 py-6 dark:border-stone-800"
      aria-label={dataset.title}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold">{dataset.title}</h2>
            <EvidenceLabel label={dataset.evidenceLabel} />
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">
            {dataset.description}
          </p>
        </div>
        <ChartDownloadMenu
          dataset={dataset}
          displayedRows={prepared.rows}
          visibleSeries={displaySeries}
        />
      </div>
      <ChartDetails dataset={dataset} />
      <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_auto]">
        <div className="space-y-5">
          <SeriesControls
            series={prepared.series}
            visible={visibleKeys}
            focused={focused}
            onToggle={updateSeries}
            onFocus={setFocused}
          />
          <NormalizationControls
            available={
              validTransformations.length ? validTransformations : ["raw"]
            }
            selected={state.transformation}
            onChange={(transformation) =>
              setState((current) => ({ ...current, transformation }))
            }
          />
        </div>
        <TimeRangeControls
          range={state.range}
          from={state.from}
          to={state.to}
          onChange={(range, from, to) =>
            setState((current) => ({ ...current, range, from, to }))
          }
          onReset={() =>
            setState({
              ...defaults,
              series:
                initialSeries ??
                dataset.series
                  .filter((item) => item.defaultVisible)
                  .map((item) => item.key),
            })
          }
        />
      </div>
      <fieldset className="mt-5">
        <legend className="mb-2 text-xs font-semibold uppercase text-stone-500">
          Context overlays
        </legend>
        <div className="flex flex-wrap gap-4 text-xs">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={recessionsEnabled}
              onChange={(event) => setRecessionsEnabled(event.target.checked)}
            />
            Recessions
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={regimesEnabled}
              onChange={(event) => setRegimesEnabled(event.target.checked)}
            />
            Project regimes
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={eventsEnabled}
              onChange={(event) => setEventsEnabled(event.target.checked)}
            />
            Event markers
          </label>
        </div>
      </fieldset>
      {lagControl && (
        <div className="mt-5 border-l-2 border-signal pl-4">
          <div className="flex flex-wrap items-center gap-4">
            <label className="text-sm font-semibold">
              GM2 lead{" "}
              <input
                aria-label="GM2 lead months"
                type="range"
                min="0"
                max="18"
                value={state.lag ?? 5}
                onChange={(event) =>
                  setState((current) => ({
                    ...current,
                    lag: Number(event.target.value),
                  }))
                }
                className="mx-3 align-middle"
              />
              <span>{state.lag ?? 5} months</span>
            </label>
            <span className="text-sm text-stone-500">
              Correlation {prepared.stats?.correlation?.toFixed(3) ?? "n/a"} ·
              n={prepared.stats?.n ?? 0} · overlap{" "}
              {prepared.overlap
                ? `${prepared.overlap.start.slice(0, 7)} to ${prepared.overlap.end.slice(0, 7)}`
                : "n/a"}{" "}
              ·{" "}
              {(state.lag ?? 5) === 5 ? "locked benchmark" : "exploratory lag"}
            </span>
          </div>
          <p className="mt-2 text-xs leading-5 text-stone-500">
            A model lag uses an earlier GM2 observation to estimate a later oil
            outcome. The visual shift places that earlier value at the later
            comparison month. Correlation measures co-movement, predictive
            usefulness requires out-of-sample improvement, and neither alone
            establishes causation. Simple-correlation peak: 4 months. Locked
            rolling model: 5 months
            {lockedPerformance?.rmse !== undefined
              ? `; ${lockedPerformance.windowMonths}-month rolling RMSE ${Number(lockedPerformance.rmse).toFixed(2)}, MAE ${Number(lockedPerformance.mae).toFixed(2)}, R² ${Number(lockedPerformance.r2).toFixed(2)}, n=${lockedPerformance.n}`
              : ""}
            .
          </p>
        </div>
      )}
      <div className="mt-6 space-y-3">
        {groups.map(([unit, panelSeries], panelIndex) => (
          <div
            key={unit}
            className="h-[280px] w-full"
            tabIndex={0}
            aria-label={`${dataset.title}, ${unit} panel. Use the data table below for exact keyboard-accessible values.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={prepared.rows}
                margin={{ top: 8, right: 12, left: 4, bottom: 8 }}
                onClick={(next: unknown) => {
                  const point = next as { activeLabel?: string };
                  if (point.activeLabel) setLockedDate(point.activeLabel);
                }}
              >
                <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
                <XAxis
                  dataKey="date"
                  minTickGap={36}
                  tickFormatter={(date) => String(date).slice(0, 7)}
                  fontSize={11}
                />
                <YAxis
                  width={62}
                  fontSize={11}
                  label={{
                    value: transformedUnit(state.transformation, unit),
                    angle: -90,
                    position: "insideLeft",
                    fontSize: 10,
                  }}
                />
                <Tooltip
                  content={
                    <ResearchTooltip
                      frequency={dataset.frequency}
                      compact={window.innerWidth < 640}
                      dataset={dataset}
                      transformation={state.transformation}
                      statistics={prepared.baselineStats}
                      lag={state.lag}
                    />
                  }
                />
                <RecessionOverlay
                  recessions={recessionsEnabled ? recessions : []}
                />
                <RegimeOverlay regimes={regimesEnabled ? regimes : []} />
                <EventAnnotations
                  events={activeEvents}
                  enabled={eventsEnabled}
                />
                {panelSeries.map((item) => (
                  <Line
                    key={item.key}
                    type="monotone"
                    dataKey={item.key}
                    name={item.label}
                    stroke={item.color ?? "#0f766e"}
                    strokeWidth={focused === item.key ? 3 : 1.7}
                    strokeOpacity={focused && focused !== item.key ? 0.2 : 0.9}
                    dot={false}
                    connectNulls={false}
                    isAnimationActive={false}
                  />
                ))}
                {panelIndex === groups.length - 1 &&
                  prepared.rows.length > 30 && (
                    <Brush
                      dataKey="date"
                      height={22}
                      travellerWidth={8}
                      stroke="#0f766e"
                    />
                  )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>
      {lockedRow && (
        <div className="mt-4 border border-petroleum/30 bg-petroleum/5 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold">
              Locked inspection: {dateLabel(lockedRow.date, dataset.frequency)}
            </p>
            <button
              type="button"
              onClick={() => setLockedDate(null)}
              className="text-xs font-semibold"
            >
              Clear
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
            {visibleSeries.map((item) => (
              <span key={item.key}>
                <strong>{item.label}:</strong>{" "}
                {formatValue(lockedRow[item.key])}
              </span>
            ))}
          </div>
          {crossRow && (
            <div className="mt-4 border-t border-stone-200 pt-3 dark:border-stone-700">
              <p className="text-xs font-semibold uppercase text-stone-500">
                Cross-layer inspection
              </p>
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
                {Object.entries(crossRow)
                  .filter(([key]) => key !== "date")
                  .map(([key, value]) => (
                    <span key={key}>
                      <strong>{key.replaceAll("_", " ")}:</strong>{" "}
                      {formatValue(value)}
                    </span>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
      <div className="mt-5">
        <LatestValuesPanel rows={prepared.rows} series={displaySeries} />
      </div>
      {activeEvents.length > 0 && (
        <div className="mt-5">
          <p className="text-xs font-semibold uppercase text-stone-500">
            Historical annotations
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {activeEvents.map((event) => (
              <button
                key={event.id}
                type="button"
                onClick={() =>
                  setEventId(eventId === event.id ? null : event.id)
                }
                className={`border px-3 py-2 text-xs ${eventId === event.id ? "border-amber-500 bg-amber-50 dark:bg-amber-950/30" : "border-stone-300 dark:border-stone-700"}`}
              >
                {event.name}
              </button>
            ))}
          </div>
          {selectedEvent && (
            <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">
              <strong>
                {selectedEvent.start.slice(0, 7)} to{" "}
                {selectedEvent.end.slice(0, 7)}:
              </strong>{" "}
              {selectedEvent.explanation} Affected layers:{" "}
              {selectedEvent.layers.join(", ")}. This annotation organizes
              historical context and is not proof of causation.
            </p>
          )}
        </div>
      )}
      <div className="mt-6">
        <AccessibleChartTable rows={prepared.rows} series={displaySeries} />
      </div>
    </section>
  );
}
