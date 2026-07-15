import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useChartDataset } from "./useChartData";
import { AccessibleChartTable } from "./AccessibleChartTable";
import { ChartDownloadMenu } from "./ChartDownloadMenu";
import { ChartDetails } from "./ChartDetails";

const periods = [
  { id: "gfc", label: "2007–09", start: "2007-01-01", end: "2009-12-01" },
  { id: "shale", label: "2014–16", start: "2014-01-01", end: "2016-12-01" },
  { id: "covid", label: "2020–21", start: "2020-01-01", end: "2021-12-01" },
  { id: "war", label: "2022–23", start: "2022-01-01", end: "2023-12-01" },
];

export function ComparablePeriodsChart({
  file,
  seriesKey,
}: {
  file: string;
  seriesKey: string;
}) {
  const { dataset } = useChartDataset(file);
  const [first, setFirst] = useState("gfc");
  const [second, setSecond] = useState("covid");
  const data = useMemo(() => {
    if (!dataset) return [];
    const paths = [first, second].map((id) => {
      const period = periods.find((item) => item.id === id)!;
      const rows = dataset.observations.filter(
        (row) =>
          row.date >= period.start &&
          row.date <= period.end &&
          typeof row[seriesKey] === "number",
      );
      const base = Number(rows[0]?.[seriesKey]);
      return rows.map((row, index) => ({
        elapsed: index,
        value: base ? (100 * Number(row[seriesKey])) / base : null,
        label: period.label,
      }));
    });
    const length = Math.max(...paths.map((path) => path.length), 0);
    return Array.from({ length }, (_, elapsed) => ({
      elapsed,
      [paths[0]?.[0]?.label ?? "first"]: paths[0]?.[elapsed]?.value ?? null,
      [paths[1]?.[0]?.label ?? "second"]: paths[1]?.[elapsed]?.value ?? null,
    }));
  }, [dataset, first, second, seriesKey]);
  if (!dataset) return null;
  const labels = [
    periods.find((item) => item.id === first)!.label,
    periods.find((item) => item.id === second)!.label,
  ];
  const tableRows = data.map((row) => ({
    date: `Month ${row.elapsed}`,
    ...row,
  }));
  const tableSeries = labels.map((label) => ({
    key: label,
    label,
    unit: "index (start = 100)",
    source:
      dataset.series.find((item) => item.key === seriesKey)?.source ??
      "Project dataset",
    status: "derived" as const,
    defaultVisible: true,
    finalObservationDate: null,
  }));
  return (
    <section className="border-y border-stone-200 py-6 dark:border-stone-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">
            Comparable historical periods
          </h2>
          <p className="mt-2 text-sm text-stone-600 dark:text-stone-300">
            Selected paths are normalized to 100 at each period’s first
            available observation and compared by elapsed month.
          </p>
        </div>
        <ChartDownloadMenu
          dataset={dataset}
          displayedRows={tableRows}
          visibleSeries={tableSeries}
        />
      </div>
      <ChartDetails dataset={dataset} />
      <div className="mt-4 flex gap-3">
        {[first, second].map((selected, index) => (
          <select
            key={index}
            value={selected}
            onChange={(event) =>
              index
                ? setSecond(event.target.value)
                : setFirst(event.target.value)
            }
            className="h-10 border border-stone-300 bg-white px-3 text-sm dark:border-stone-700 dark:bg-[#18201d]"
          >
            {periods.map((period) => (
              <option key={period.id} value={period.id}>
                {period.label}
              </option>
            ))}
          </select>
        ))}
      </div>
      <div className="mt-5 h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid opacity={0.25} />
            <XAxis
              dataKey="elapsed"
              label={{ value: "Elapsed months", position: "bottom" }}
            />
            <YAxis />
            <Tooltip />
            {labels.map((label, index) => (
              <Line
                key={label}
                dataKey={label}
                stroke={index ? "#2563eb" : "#0f766e"}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <AccessibleChartTable rows={tableRows} series={tableSeries} />
    </section>
  );
}
