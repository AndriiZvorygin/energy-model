import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EvidenceLabel } from "../EvidenceLabel";
import { ChartDetails, type ChartDetailsData } from "./ChartDetails";

type CorrelationRow = {
  economic_measure: string;
  label: string;
  contemporaneous_correlation: number | null;
  best_lag_quarters: number | null;
  best_lag_periods: number;
  lag_unit: string;
  best_lag_correlation: number | null;
  rolling_20q_correlation_mean: number | null;
  rolling_correlation_mean: number | null;
  rolling_window: string;
  oos_improvement_vs_ar_pct: number | null;
  start_date: string;
  end_date: string;
  n: number;
  energy_measure: string;
};

type Payload = {
  evidenceLabel: string;
  details: ChartDetailsData;
  rows: CorrelationRow[];
};

const value = (input: number | null) =>
  input === null ? "Not available" : input.toFixed(3);

export function EnergyOutputCorrelationChart() {
  const [payload, setPayload] = useState<Payload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [energyMeasure, setEnergyMeasure] = useState("Total energy consumption growth");
  useEffect(() => {
    void fetch(
      `${import.meta.env.BASE_URL}generated/output-quality-correlations.json`,
    )
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(setPayload)
      .catch((reason: Error) => setError(reason.message));
  }, []);
  if (error)
    return (
      <p className="border border-amber-300 p-4 text-sm">
        Energy-correlation data could not be loaded: {error}
      </p>
    );
  if (!payload)
    return (
      <div className="h-80 animate-pulse bg-stone-100 dark:bg-stone-900" />
    );
  const measures = [...new Set(payload.rows.map((row) => row.energy_measure))];
  const rows = payload.rows.filter((row) => row.energy_measure === energyMeasure);
  return (
    <section
      className="border-y border-stone-200 py-6 dark:border-stone-800"
      aria-label="Energy correlation by economic measure"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-xl font-semibold">
          Energy correlation by economic measure
        </h2>
        <EvidenceLabel label={payload.evidenceLabel} />
      </div>
      <ChartDetails dataset={payload.details} />
      <label className="mt-5 block max-w-sm text-xs font-semibold uppercase text-stone-500">
        Energy measure
        <select value={energyMeasure} onChange={(event) => setEnergyMeasure(event.target.value)} className="mt-2 block h-10 w-full border border-stone-300 bg-white px-3 text-sm normal-case text-ink dark:border-stone-700 dark:bg-[#18201d] dark:text-white">
          {measures.map((measure) => <option key={measure}>{measure}</option>)}
        </select>
      </label>
      <div
        className="mt-6 h-[440px]"
        tabIndex={0}
        aria-label="Horizontal bar chart of energy-growth correlations. Exact values follow in a table."
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ left: 24, right: 20 }}
          >
            <CartesianGrid opacity={0.55} />
            <XAxis type="number" domain={[-1, 1]} />
            <YAxis
              type="category"
              dataKey="label"
              width={180}
              tick={{ fontSize: 11 }}
            />
            <ReferenceLine x={0} stroke="var(--chart-neutral)" strokeWidth={1.5} />
            <Tooltip
              content={({ active, payload: items }) =>
                active && items?.[0]?.payload ? (
                  <div className="max-w-72 border border-stone-200 bg-white p-3 text-xs shadow-lg dark:border-stone-700 dark:bg-[#18201d]">
                    <p className="font-semibold">{items[0].payload.label}</p>
                    <p>
                      Contemporaneous:{" "}
                      {value(items[0].payload.contemporaneous_correlation)}
                    </p>
                    <p>
                      Best lag: {items[0].payload.best_lag_periods} {items[0].payload.lag_unit} (
                      {value(items[0].payload.best_lag_correlation)})
                    </p>
                    <p>
                      Rolling mean:{" "}
                      {value(items[0].payload.rolling_correlation_mean)} ({items[0].payload.rolling_window})
                    </p>
                    <p>
                      OOS improvement vs AR:{" "}
                      {items[0].payload.oos_improvement_vs_ar_pct?.toFixed(1) ??
                        "n/a"}
                      %
                    </p>
                    <p>
                      Coverage: {items[0].payload.start_date} to{" "}
                      {items[0].payload.end_date}
                    </p>
                  </div>
                ) : null
              }
            />
            <Bar dataKey="contemporaneous_correlation" fill="var(--chart-1)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-5">
        <summary className="cursor-pointer text-sm font-semibold">
          Accessible relationship table
        </summary>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-left text-xs">
            <thead>
              <tr>
                <th className="p-2">Measure</th>
                <th className="p-2">Correlation</th>
                <th className="p-2">Best lag</th>
                <th className="p-2">Rolling mean</th>
                <th className="p-2">OOS vs AR</th>
                <th className="p-2">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`${row.energy_measure}-${row.economic_measure}`}
                  className="border-t dark:border-stone-800"
                >
                  <th className="p-2">{row.label}</th>
                  <td className="p-2">
                    {value(row.contemporaneous_correlation)}
                  </td>
                  <td className="p-2">{row.best_lag_periods} {row.lag_unit}</td>
                  <td className="p-2">
                    {value(row.rolling_correlation_mean)} ({row.rolling_window})
                  </td>
                  <td className="p-2">
                    {row.oos_improvement_vs_ar_pct?.toFixed(1) ?? "n/a"}%
                  </td>
                  <td className="p-2">
                    {row.start_date} to {row.end_date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
