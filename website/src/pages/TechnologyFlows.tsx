import { useGeneratedJson } from '../components/charts/useChartData'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { PageBody, PageHeader } from '../components/PageHeader'

type BenchmarkRow = {
  model: string
  benchmark: string
  score_percent: number
  score_status: string
  source: string
  source_url: string
  limitation: string
}

type BenchmarkPayload = {
  title: string
  benchmark: string
  methodology: string
  rows: BenchmarkRow[]
}

function BenchmarkScores() {
  const { data, error } = useGeneratedJson<BenchmarkPayload>('technology-benchmark-scores.json')
  return <section className="mt-12">
    <h2 className="text-2xl font-semibold">Capability: public task-quality benchmarks</h2>
    <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">GPQA Diamond offers one comparable science-reasoning result. These are model-card scores for base models; they do not establish the quality of the local quantized builds or local government tasks.</p>
    {error && <p className="mt-4 text-sm text-red-700 dark:text-red-300">Could not load benchmark rows: {error}</p>}
    {!data && !error && <p className="mt-4 text-sm text-stone-500">Loading public benchmark results…</p>}
    {data && <>
      <div className="mt-5 overflow-x-auto border border-stone-200 dark:border-stone-800">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead className="bg-stone-100 text-xs uppercase tracking-wide dark:bg-stone-900"><tr><th className="p-3">Base model</th><th className="p-3">GPQA Diamond</th><th className="p-3">Source</th></tr></thead>
          <tbody>{data.rows.map((row) => <tr key={row.model} className="border-t border-stone-200 align-top dark:border-stone-800"><th scope="row" className="p-3 font-semibold">{row.model}</th><td className="p-3 tabular-nums">{row.score_percent.toFixed(1)}%</td><td className="p-3"><a className="font-medium text-petroleum underline dark:text-emerald-300" href={row.source_url} target="_blank" rel="noreferrer">{row.source}</a><p className="mt-1 max-w-xl text-xs leading-5 text-stone-500 dark:text-stone-400">{row.limitation}</p></td></tr>)}</tbody>
        </table>
      </div>
      <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">{data.methodology}</p>
    </>}
  </section>
}

export function TechnologyFlows() {
  return <>
    <PageHeader eyebrow="AI and technology flows · v1 to 2030" title="From capital and electricity to useful work" description="A Canada-first flow model for digital infrastructure. The central question is how much useful work a system delivers for its electricity, equipment, and human time." />
    <PageBody>
      <div className="grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-5 dark:border-stone-800 dark:bg-stone-800">
        {[
          ['1 · Capital and equipment', 'Broad investment proxies show capital entering software and computer equipment.'],
          ['2 · Facilities and grids', 'Ontario and U.S. forecasts describe data-centre electricity demand at different scales.'],
          ['3 · Compute workload', 'Local Ollama aggregates count calls and tokens without retaining prompts or host identifiers.'],
          ['4 · Capability', 'Public model-card scores provide a limited task-quality reference.'],
          ['5 · Useful work', 'Accepted tasks and time saved are not measured by token counts, so no productivity score is inferred.'],
        ].map(([title, description]) => <div key={title} className="bg-paper p-4 dark:bg-[#111715]"><h2 className="text-sm font-semibold">{title}</h2><p className="mt-2 text-xs leading-5 text-stone-600 dark:text-stone-300">{description}</p></div>)}
      </div>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Capital entering digital infrastructure</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">U.S. software and computer-equipment investment are broad BEA categories, not AI-specific spending. They show an upstream flow proxy, not where the equipment was installed or what work it performed.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-capital-investment-proxies.json" initialTransformation="indexed" syncUrl={false} /></div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Canada and Ontario electricity context</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">National electricity generation gives a Canada-wide scale reference. The IESO forecast then isolates the Ontario data-centre sub-sector. It includes cloud and other computing demand as well as AI and is not an Owen Sound or Grey-Bruce forecast.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-canada-electricity-generation.json" initialTransformation="indexed" syncUrl={false} /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510001501" target="_blank" rel="noreferrer">Statistics Canada monthly electricity generation by type</a>. Complete calendar years are summed to TWh.</p>
        <div className="mt-10"><ResearchTimeSeriesChart file="technology-ontario-data-centre-electricity.json" initialTransformation="raw" syncUrl={false} /></div>
        <p className="mt-3 max-w-4xl text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href="https://www.ieso.ca/en/Sector-Participants/Planning-and-Forecasting/Annual-Planning-Outlook" target="_blank" rel="noreferrer">IESO 2026 Annual Planning Outlook</a>. Scenario values are limited to 2027–2030 for v1.</p>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">U.S. data-centre scale comparator</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">The U.S. series is separate from Ontario. LBNL estimates 2024 use and publishes 2030 cases; the chart shows only those endpoints and does not fill in intervening years.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-us-data-centre-electricity.json" initialTransformation="raw" syncUrl={false} /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href="https://eta-publications.lbl.gov/publications/united-states-data-center-energy-2025" target="_blank" rel="noreferrer">Lawrence Berkeley National Laboratory, 2025 Update</a>. Data-centre electricity is not AI-only electricity.</p>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Local compute workload</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">These monthly totals come from local Ollama inference. The published aggregate contains model labels, call counts, and prompt/output token totals only. It excludes prompts, responses, call IDs, endpoints, timestamps below month-level, and host information. The aggregate does not identify the machine&apos;s location. Training demand remains inside the facility-level scenarios and is not split out in this v1 source set.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-local-inference-calls.json" initialTransformation="raw" syncUrl={false} /></div>
        <div className="mt-10"><ResearchTimeSeriesChart file="technology-local-inference-tokens.json" initialTransformation="raw" syncUrl={false} /></div>
      </section>

      <BenchmarkScores />

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Electricity sensitivity for a 9B-class local model</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">A published H100 benchmark is transferred to output tokens from the local 9B-class model as an illustrative GPU-only estimate. The 27B workload remains unestimated because the selected reference is not size-matched. No prompt-processing, CPU, memory, remaining server load, or cooling electricity is included.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-local-gpu-energy-estimate.json" initialTransformation="raw" syncUrl={false} /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Reference: <a className="underline" href="https://ojs.aaai.org/index.php/AAAI/article/view/40535" target="_blank" rel="noreferrer">TokenPowerBench, AAAI 2026</a>. The published setup varies model, context, engine, and batch size, so this is a sensitivity, not local telemetry.</p>
      </section>

      <section className="mt-12 border-l-2 border-petroleum pl-5">
        <h2 className="text-xl font-semibold">What would count as useful work?</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">A later measure could compare accepted task outcomes with electricity and human review time. This v1 has no accepted-task denominator or time-saved observations, so it leaves human-time values as future scenario inputs and does not turn calls, tokens, or benchmark scores into a productivity claim.</p>
      </section>
    </PageBody>
  </>
}
