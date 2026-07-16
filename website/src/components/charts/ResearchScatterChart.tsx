import { useMemo } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { EvidenceLabel } from "../EvidenceLabel";
import { AccessibleChartTable } from "./AccessibleChartTable";
import { ChartDownloadMenu } from "./ChartDownloadMenu";
import { ChartDetails } from "./ChartDetails";
import { useChartDataset } from "./useChartData";

export function ResearchScatterChart({
  file,
  xKey,
  yKey,
  title,
  description,
  trendLine = false,
}: {
  file: string;
  xKey: string;
  yKey: string;
  title: string;
  description: string;
  trendLine?: boolean;
}) {
  const { dataset, error } = useChartDataset(file);
  const points = useMemo(
    () =>
      dataset?.observations
        .filter(
          (row) =>
            typeof row[xKey] === "number" && typeof row[yKey] === "number",
        )
        .map((row) => ({ date: row.date, x: row[xKey], y: row[yKey] })) ?? [],
    [dataset, xKey, yKey],
  );
  const trend = useMemo<readonly [{ x: number; y: number }, { x: number; y: number }] | null>(() => {
    if (!trendLine || points.length < 2) return null;
    const meanX = points.reduce((sum, point) => sum + Number(point.x), 0) / points.length;
    const meanY = points.reduce((sum, point) => sum + Number(point.y), 0) / points.length;
    const denominator = points.reduce((sum, point) => sum + (Number(point.x) - meanX) ** 2, 0);
    if (!denominator) return null;
    const slope = points.reduce((sum, point) => sum + (Number(point.x) - meanX) * (Number(point.y) - meanY), 0) / denominator;
    const intercept = meanY - slope * meanX;
    const minimum = Math.min(...points.map((point) => Number(point.x)));
    const maximum = Math.max(...points.map((point) => Number(point.x)));
    return [{ x: minimum, y: intercept + slope * minimum }, { x: maximum, y: intercept + slope * maximum }] as const;
  }, [points, trendLine]);
  if (error)
    return <p className="border border-amber-300 p-4 text-sm">{error}</p>;
  if (!dataset)
    return (
      <div className="h-72 animate-pulse bg-stone-100 dark:bg-stone-900" />
    );
  const xSeries = dataset.series.find((item) => item.key === xKey)!;
  const ySeries = dataset.series.find((item) => item.key === yKey)!;
  const tableRows = points.map((point) => ({
    date: point.date,
    [xKey]: point.x,
    [yKey]: point.y,
  }));
  return (
    <section className="border-y border-stone-200 py-6 dark:border-stone-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold">{title}</h2>
            <EvidenceLabel label={dataset.evidenceLabel} />
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">
            {description}
          </p>
        </div>
        <ChartDownloadMenu
          dataset={dataset}
          displayedRows={tableRows}
          visibleSeries={[xSeries, ySeries]}
        />
      </div>
      <ChartDetails dataset={dataset} />
      <div
        className="mt-5 h-[380px]"
        tabIndex={0}
        aria-label={`${title}. Accessible values are available in the table below.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 15, right: 20, bottom: 30, left: 15 }}>
            <CartesianGrid opacity={0.55} />
            <XAxis
              type="number"
              dataKey="x"
              name={xSeries.label}
              unit={` ${xSeries.unit}`}
              label={{ value: xSeries.label, position: "bottom" }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name={ySeries.label}
              unit={` ${ySeries.unit}`}
              label={{
                value: ySeries.label,
                angle: -90,
                position: "insideLeft",
              }}
            />
            <ZAxis range={[35, 35]} />
            {trend && <ReferenceLine segment={trend} stroke="var(--chart-2)" strokeWidth={2.25} strokeDasharray="7 4" ifOverflow="extendDomain" />}
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) =>
                active && payload?.[0]?.payload ? (
                  <div className="border border-stone-200 bg-white p-3 text-xs shadow-lg dark:border-stone-700 dark:bg-[#18201d]">
                    <p className="font-semibold">{payload[0].payload.date}</p>
                    <p className="mt-1">
                      {xSeries.label}: {Number(payload[0].payload.x).toFixed(2)}
                    </p>
                    <p>
                      {ySeries.label}: {Number(payload[0].payload.y).toFixed(2)}
                    </p>
                  </div>
                ) : null
              }
            />
            <Scatter
              data={points}
              fill="var(--chart-1)"
              fillOpacity={0.58}
              isAnimationActive={false}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <AccessibleChartTable rows={tableRows} series={[xSeries, ySeries]} />
    </section>
  );
}
