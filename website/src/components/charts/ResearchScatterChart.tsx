import { useMemo } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
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
}: {
  file: string;
  xKey: string;
  yKey: string;
  title: string;
  description: string;
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
            <CartesianGrid opacity={0.25} />
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
              fill="#0f766e"
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
