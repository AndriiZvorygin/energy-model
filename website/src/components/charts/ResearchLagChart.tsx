import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EvidenceLabel } from "../EvidenceLabel";
import { ChartDetails, type ChartDetailsData } from "./ChartDetails";

type LagRow = {
  target?: string;
  oilMetric?: string;
  sample?: string;
  metric?: string;
  lag: number;
  correlation: number | null;
  n: number;
};

export function ResearchLagChart({
  mode,
  title,
  description,
}: {
  mode: "gm2" | "equity";
  title: string;
  description: string;
}) {
  const [payload, setPayload] = useState<{
    gm2Oil: LagRow[];
    oilEquityReturns: LagRow[];
    details: { gm2: ChartDetailsData; equity: ChartDetailsData };
  } | null>(null);
  useEffect(() => {
    void fetch(`${import.meta.env.BASE_URL}generated/lag-results.json`)
      .then((response) => response.json())
      .then(setPayload);
  }, []);
  const data = useMemo(() => {
    const rows =
      mode === "gm2"
        ? (payload?.gm2Oil ?? [])
        : (payload?.oilEquityReturns ?? []).filter(
            (row) =>
              row.sample === "full" && row.metric === "monthly_log_return",
          );
    const grouped = new Map<number, Record<string, number | null>>();
    rows.forEach((row) => {
      const key =
        mode === "gm2"
          ? row.target?.replace("_YoY", "")
          : row.oilMetric?.startsWith("WTI")
            ? "WTI"
            : "Brent";
      grouped.set(Number(row.lag), {
        ...(grouped.get(Number(row.lag)) ?? { lag: Number(row.lag) }),
        [key ?? "series"]: row.correlation,
      });
    });
    return [...grouped.values()].sort((a, b) => Number(a.lag) - Number(b.lag));
  }, [mode, payload]);
  const csv = [
    "lag_months,WTI_correlation,Brent_correlation",
    ...data.map((row) => `${row.lag},${row.WTI ?? ""},${row.Brent ?? ""}`),
  ].join("\n");
  const download = () => {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    link.download = `${mode}-lag-correlation.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };
  return (
    <section className="border-y border-stone-200 py-6 dark:border-stone-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold">{title}</h2>
            <EvidenceLabel
              label={
                mode === "gm2"
                  ? "Validated relationship"
                  : "Contextual indicator"
              }
            />
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">
            {description}
          </p>
        </div>
        <details className="relative">
          <summary className="cursor-pointer border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700">
            Download and cite
          </summary>
          <div className="absolute right-0 z-20 mt-1 w-56 border bg-white p-1 shadow-lg dark:border-stone-700 dark:bg-[#18201d]">
            <button
              type="button"
              onClick={download}
              className="block w-full px-3 py-2 text-left text-xs"
            >
              Download lag CSV
            </button>
            <a
              href={`${import.meta.env.BASE_URL}charts/${mode === "gm2" ? "final_gm2_oil_lead_chart.png" : "oil_equity_return_lag_correlation.png"}`}
              target="_blank"
              rel="noreferrer"
              className="block px-3 py-2 text-xs"
            >
              Open publication PNG
            </a>
            <button
              type="button"
              onClick={() =>
                void navigator.clipboard.writeText(window.location.href)
              }
              className="block w-full px-3 py-2 text-left text-xs"
            >
              Copy shareable URL
            </button>
          </div>
        </details>
      </div>
      {payload?.details && <ChartDetails dataset={payload.details[mode]} />}
      <div className="mt-5 h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid opacity={0.25} />
            <XAxis
              dataKey="lag"
              label={{ value: "Lag (months)", position: "bottom" }}
            />
            <YAxis domain={[-1, 1]} width={52} />
            <ReferenceLine y={0} stroke="#78716c" />
            <ReferenceLine
              x={mode === "gm2" ? 5 : 0}
              stroke="#d97706"
              strokeDasharray="4 3"
            />
            <Tooltip formatter={(value) => Number(value).toFixed(3)} />
            {["WTI", "Brent"].map((key, index) => (
              <Line
                key={key}
                dataKey={key}
                stroke={index ? "#2563eb" : "#0f766e"}
                strokeWidth={2}
                dot={false}
                connectNulls={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-stone-500">
        {mode === "gm2"
          ? "Positive lag means GM2 leads oil. The line at 5 marks the locked benchmark, while the simple correlation peak occurs near 4."
          : "Positive lag means stocks lead oil; negative lag means oil leads stocks. Return correlations are more relevant to timing than overlapping YoY correlations."}
      </p>
      <details className="mt-4 border-t border-stone-200 pt-4 dark:border-stone-800">
        <summary className="cursor-pointer text-sm font-semibold">
          Accessible lag table
        </summary>
        <div className="mt-3 max-h-80 overflow-auto">
          <table className="min-w-full text-left text-xs">
            <thead>
              <tr>
                <th className="p-2">Lag months</th>
                <th className="p-2">WTI correlation</th>
                <th className="p-2">Brent correlation</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.lag} className="border-t dark:border-stone-800">
                  <th className="p-2">{row.lag}</th>
                  <td className="p-2">
                    {typeof row.WTI === "number"
                      ? row.WTI.toFixed(3)
                      : "Not available"}
                  </td>
                  <td className="p-2">
                    {typeof row.Brent === "number"
                      ? row.Brent.toFixed(3)
                      : "Not available"}
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
