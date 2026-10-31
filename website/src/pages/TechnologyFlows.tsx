import { useGeneratedJson } from '../components/charts/useChartData'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { PageBody, PageHeader } from '../components/PageHeader'

type CapabilityRow = {
  model: string
  score: number | null
  displayScore: string
  scoreUnit: string
  evaluationDate: string
  configuration: string
  source: string
  sourceUrl: string
  confidence: string
  notes: string
}

type CapabilityFamily = {
  id: string
  category: string
  benchmark: string
  metricLabel: string
  scaleMaximum: number
  scope: string
  conditions: string
  rows: CapabilityRow[]
}

type CapabilityPayload = {
  title: string
  snapshotDate: string
  methodology: string
  families: CapabilityFamily[]
}

type ComputeScenario = {
  scenario: string
  accelerators: number
  acceleratorsHigh?: number
  usableStorageTb: number
  facilityPowerLowKw: number
  facilityPowerHighKw: number
  monthlyEnergyLowMwh: number
  monthlyEnergyHighMwh: number
  monthlyElectricityCostLowCad: number
  monthlyElectricityCostHighCad: number
  annualElectricityCostLowCad: number
  annualElectricityCostHighCad: number
  waterPerDayLowM3: number
  waterPerDayHighM3: number
  capitalLowCad: number
  capitalHighCad: number
  workload: string
  basis: string
  capitalExtrapolated: boolean
}

type ComputePayload = {
  electricityPriceNote: string
  electricityRateSource: string
  electricityRateSourceUrl: string
  waterNote: string
  campusNote: string
  calculation: string
  scenarioSource: string
  scenarioSourceUrl: string
  trainingSource: string
  trainingSourceUrl: string
  trainingRunAnchor: {
    model: string
    reportedAcceleratorHours: number
    reportedAccelerator: string
    equivalentAccelerators: number
    equivalentClusterDays: number
    facilityPowerLowKw: number
    facilityPowerHighKw: number
    energyLowMwh: number
    energyHighMwh: number
    electricityCostLowCad: number
    electricityCostHighCad: number
    waterLowM3: number
    waterHighM3: number
    source: string
    note: string
  } | null
  scenarios: ComputeScenario[]
}

type SiteRow = {
  province: string
  city: string
  hydroFact: string
  hydroScaleComparison: string
  hydroSource: string
  hydroSourceUrl: string
  gridAndPolicyFact: string
  gridAndPolicySource: string
  gridAndPolicyUrl: string
  municipalWaterDailyLitres: number
  municipalWaterFact: string
  waterSource: string
  waterSourceUrl: string
  assessment: string
  openQuestion: string
}

type SitePayload = {
  screeningLoadMw: number
  screeningWaterM3PerDay: number
  methodology: string
  rows: SiteRow[]
}

type WorkloadModel = {
  model: string
  completedCalls: number
  promptTokens: number
  outputTokens: number
  promptEvalHours: number
  outputEvalHours: number
  totalRuntimeHours: number
}

type WorkloadSnapshotPayload = {
  title: string
  snapshotDate: string
  scope: string
  source: string
  sourceUrl: string
  summary: {
    completedCalls: number
    promptTokens: number
    outputTokens: number
    totalRuntimeHours: number
  }
  models: WorkloadModel[]
  limitations: string[]
}

const countFormat = new Intl.NumberFormat('en-CA')
const compactFormat = new Intl.NumberFormat('en-CA', { notation: 'compact', maximumFractionDigits: 1 })

function cad(value: number) {
  return `C$${compactFormat.format(value)}`
}

function powerLabel(lowKw: number, highKw: number) {
  return highKw >= 1000
    ? `${(lowKw / 1000).toFixed(lowKw % 1000 === 0 ? 0 : 1)}–${(highKw / 1000).toFixed(highKw % 1000 === 0 ? 0 : 1)} MW`
    : `${Math.round(lowKw)}–${Math.round(highKw)} kW`
}

function waterLabel(lowM3: number, highM3: number) {
  if (highM3 < 1) return `${Math.round(lowM3 * 1000)}–${Math.round(highM3 * 1000)} L/day`
  return `${lowM3.toFixed(1)}–${highM3.toFixed(1)} m³/day`
}

function CapabilityScorecard() {
  const { data, error } = useGeneratedJson<CapabilityPayload>('technology-capability-scorecard.json')
  if (error) return <section className="mt-12"><h2 className="text-2xl font-semibold">AI capability by task family</h2><p className="mt-4 text-sm text-red-700 dark:text-red-300">Could not load capability evidence: {error}</p></section>
  if (!data) return <section className="mt-12"><h2 className="text-2xl font-semibold">AI capability by task family</h2><p className="mt-4 text-sm text-stone-500">Loading archived capability results…</p></section>
  return <section className="mt-12">
    <div className="max-w-4xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-petroleum dark:text-emerald-300">Capability snapshot · {data.snapshotDate}</p>
      <h2 className="mt-2 text-2xl font-semibold">What current systems can do, task by task</h2>
      <p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">The comparisons span graduate science, hard expert questions, novel abstraction, professional work, coding agents and long technical tasks. Each panel keeps its own metric; the page does not collapse these into one “AI score.”</p>
    </div>
    <div className="mt-5 grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-4 dark:border-stone-800 dark:bg-stone-800">
      {[
        ['Task-specific human comparisons', 'Top archived scores exceed the published human reference on GPQA Diamond and ARC-AGI-2. The test sets and human protocols differ, so this stays a narrow benchmark result.'],
        ['Expert questions remain unsaturated', 'The top no-tool Humanity’s Last Exam result is 54.8%; no single human accuracy baseline is available for direct comparison.'],
        ['Professional work is partial', 'GDPval reports a 47.6% win-or-tie rate for Claude Opus 4.1 across paired expert work products. That is not a productivity increase or an occupation replacement rate.'],
        ['Agent scores include tools', 'DeepSWE, MLE-Bench and METR evaluate systems with scaffolding. Their results do not describe a model answering once without tools.'],
      ].map(([title, description]) => <div key={title} className="bg-paper p-4 dark:bg-[#111715]"><h3 className="text-sm font-semibold">{title}</h3><p className="mt-2 text-xs leading-5 text-stone-600 dark:text-stone-300">{description}</p></div>)}
    </div>
    <div className="mt-6 grid gap-5 xl:grid-cols-2">
      {data.families.map((family) => <article key={family.id} className="border border-stone-200 bg-paper p-5 dark:border-stone-800 dark:bg-[#111715]">
        <p className="text-xs font-semibold uppercase tracking-widest text-stone-500 dark:text-stone-400">{family.category}</p>
        <h3 className="mt-2 text-lg font-semibold">{family.benchmark}</h3>
        <p className="mt-1 text-xs text-stone-500 dark:text-stone-400">{family.metricLabel}</p>
        <div className="mt-5 space-y-4" role="list" aria-label={`${family.benchmark} results`}>
          {family.rows.map((row) => {
            const percentage = row.score === null ? 0 : Math.max(0, Math.min(row.score / family.scaleMaximum * 100, 100))
            return <div key={`${row.model}-${row.evaluationDate}`} role="listitem">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-sm">
                <span className="font-medium">{row.model}{row.model.toLowerCase().includes('human') && <span className="ml-2 text-[10px] font-normal uppercase tracking-wide text-stone-500">reference</span>}</span>
                <strong className="tabular-nums">{row.displayScore}</strong>
              </div>
              <div className="mt-2 h-2 bg-stone-100 dark:bg-stone-800" role="meter" aria-label={`${row.model} ${family.benchmark} result`} aria-valuemin={0} aria-valuemax={family.scaleMaximum} aria-valuenow={row.score ?? 0}>
                <div className={`h-full ${row.model.toLowerCase().includes('human') ? 'bg-stone-500' : 'bg-petroleum'}`} aria-hidden="true" style={{ width: `${percentage}%` }} />
              </div>
              <div className="mt-1 flex flex-wrap justify-between gap-x-3 text-[11px] leading-4 text-stone-500 dark:text-stone-400">
                <span>{row.configuration || 'Evaluation setup not fully reported'}</span>
                <span>{row.evaluationDate}</span>
              </div>
              <a className="mt-0.5 inline-block text-[11px] font-medium text-petroleum underline dark:text-emerald-300" href={row.sourceUrl} target="_blank" rel="noreferrer">{row.source}</a>
            </div>
          })}
        </div>
        <div className="mt-5 border-t border-stone-200 pt-4 text-xs leading-5 text-stone-600 dark:border-stone-800 dark:text-stone-300">
          <p>{family.scope}</p>
          <p className="mt-2 text-stone-500 dark:text-stone-400">{family.conditions}</p>
        </div>
      </article>)}
    </div>
    <p className="mt-4 max-w-5xl text-xs leading-5 text-stone-500 dark:text-stone-400">{data.methodology} Results are a dated archive snapshot, not a live leaderboard. Model-card claims, independent benchmark submissions and agent-system results are labelled separately through their linked sources.</p>
  </section>
}

function ComputeSizing() {
  const { data, error } = useGeneratedJson<ComputePayload>('technology-compute-scenarios.json')
  if (error) return <section className="mt-12"><h2 className="text-2xl font-semibold">Compute tiers and cost</h2><p className="mt-4 text-sm text-red-700 dark:text-red-300">Could not load the compute scenarios: {error}</p></section>
  if (!data) return <section className="mt-12"><h2 className="text-2xl font-semibold">Compute tiers and cost</h2><p className="mt-4 text-sm text-stone-500">Loading compute scenarios…</p></section>
  const campus = data.scenarios.find((row) => row.capitalExtrapolated)
  return <section className="mt-12">
    <div className="max-w-4xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-petroleum dark:text-emerald-300">Compute planning</p>
      <h2 className="mt-2 text-2xl font-semibold">From a lab to a frontier-scale campus</h2>
      <p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">Accelerator counts are H100-class planning proxies. The small tiers cover local fine-tuning and regional distillation/evaluation; a 2,048-GPU campaign is a training cluster; a 100 MW campus is a separate, much larger facility envelope.</p>
    </div>
    <div className="mt-5 overflow-x-auto border border-stone-200 dark:border-stone-800">
      <table className="w-full min-w-[980px] text-left text-sm">
        <thead className="bg-stone-100 text-xs uppercase tracking-wide dark:bg-stone-900"><tr><th className="p-3">Tier</th><th className="p-3">Accelerators</th><th className="p-3">Facility load</th><th className="p-3">30-day power bill</th><th className="p-3">Capital envelope</th><th className="p-3">Cooling water/day</th></tr></thead>
        <tbody>{data.scenarios.map((row) => <tr key={row.scenario} className="border-t border-stone-200 align-top dark:border-stone-800">
          <th scope="row" className="max-w-64 p-3 font-semibold">{row.scenario}<p className="mt-1 text-xs font-normal leading-5 text-stone-500 dark:text-stone-400">{row.workload}</p></th>
          <td className="p-3 tabular-nums">{countFormat.format(row.accelerators)}{row.acceleratorsHigh ? `–${countFormat.format(row.acceleratorsHigh)}` : ''}</td>
          <td className="p-3 tabular-nums">{powerLabel(row.facilityPowerLowKw, row.facilityPowerHighKw)}</td>
          <td className="p-3 tabular-nums">{cad(row.monthlyElectricityCostLowCad)}–{cad(row.monthlyElectricityCostHighCad)}</td>
          <td className="p-3 tabular-nums">{cad(row.capitalLowCad)}–{cad(row.capitalHighCad)}{row.capitalExtrapolated && <span className="mt-1 block text-[11px] text-amber-700 dark:text-amber-300">Linear extrapolation</span>}</td>
          <td className="p-3 tabular-nums">{waterLabel(row.waterPerDayLowM3, row.waterPerDayHighM3)}</td>
        </tr>)}</tbody>
      </table>
    </div>
    {data.trainingRunAnchor && <div className="mt-5 border border-stone-200 p-5 dark:border-stone-800">
      <p className="text-xs font-semibold uppercase tracking-widest text-petroleum dark:text-emerald-300">Reported training-run anchor</p>
      <h3 className="mt-2 text-lg font-semibold">{data.trainingRunAnchor.model}: {(data.trainingRunAnchor.reportedAcceleratorHours / 1_000_000).toFixed(3)} million {data.trainingRunAnchor.reportedAccelerator}</h3>
      <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">That is about {data.trainingRunAnchor.equivalentClusterDays.toFixed(1)} days on {countFormat.format(data.trainingRunAnchor.equivalentAccelerators)} accelerators at continuous utilization. Transferring the archived facility-power proxy to that duration gives {data.trainingRunAnchor.energyLowMwh.toLocaleString('en-CA', { maximumFractionDigits: 0 })}–{data.trainingRunAnchor.energyHighMwh.toLocaleString('en-CA', { maximumFractionDigits: 0 })} MWh and an energy-only sensitivity of {cad(data.trainingRunAnchor.electricityCostLowCad)}–{cad(data.trainingRunAnchor.electricityCostHighCad)}.</p>
      <a className="mt-2 inline-block text-xs font-medium text-petroleum underline dark:text-emerald-300" href={data.trainingRunAnchor.source} target="_blank" rel="noreferrer">DeepSeek-V3 technical report</a>
      <p className="mt-2 text-xs leading-5 text-stone-500 dark:text-stone-400">{data.trainingRunAnchor.note} Water sensitivity at 0.3 L/kWh: {data.trainingRunAnchor.waterLowM3.toFixed(0)}–{data.trainingRunAnchor.waterHighM3.toFixed(0)} m³ over the run.</p>
    </div>}
    {campus && <div className="mt-5 grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-3 dark:border-stone-800 dark:bg-stone-800">
      <div className="bg-paper p-4 dark:bg-[#111715]"><p className="text-xs text-stone-500 dark:text-stone-400">100 MW campus · annual electricity</p><p className="mt-1 text-lg font-semibold tabular-nums">{cad(campus.annualElectricityCostLowCad)}–{cad(campus.annualElectricityCostHighCad)} / year</p></div>
      <div className="bg-paper p-4 dark:bg-[#111715]"><p className="text-xs text-stone-500 dark:text-stone-400">100 MW campus · water at planning WUE</p><p className="mt-1 text-lg font-semibold tabular-nums">{campus.waterPerDayLowM3.toFixed(0)} m³/day</p></div>
      <div className="bg-paper p-4 dark:bg-[#111715]"><p className="text-xs text-stone-500 dark:text-stone-400">100 MW campus · accelerator equivalent</p><p className="mt-1 text-lg font-semibold tabular-nums">{countFormat.format(campus.accelerators)}–{countFormat.format(campus.acceleratorsHigh ?? campus.accelerators)}</p></div>
    </div>}
    <div className="mt-4 space-y-1 text-xs leading-5 text-stone-500 dark:text-stone-400">
      <p>{data.calculation}</p>
      <p>{data.electricityPriceNote} <a className="underline" href={data.electricityRateSourceUrl} target="_blank" rel="noreferrer">{data.electricityRateSource}</a>.</p>
      <p>{data.waterNote}</p>
      <p>{data.campusNote} Sources: <a className="underline" href={data.scenarioSourceUrl} target="_blank" rel="noreferrer">{data.scenarioSource}</a>; <a className="underline" href={data.trainingSourceUrl} target="_blank" rel="noreferrer">{data.trainingSource}</a>.</p>
    </div>
  </section>
}

function CanadianSiteScreen() {
  const { data, error } = useGeneratedJson<SitePayload>('technology-canadian-site-screen.json')
  if (error) return <section className="mt-12"><h2 className="text-2xl font-semibold">Canadian hydro and water screening</h2><p className="mt-4 text-sm text-red-700 dark:text-red-300">Could not load the Canadian site screen: {error}</p></section>
  if (!data) return <section className="mt-12"><h2 className="text-2xl font-semibold">Canadian hydro and water screening</h2><p className="mt-4 text-sm text-stone-500">Loading Canadian site screen…</p></section>
  return <section className="mt-12">
    <div className="max-w-4xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-petroleum dark:text-emerald-300">Canada · preliminary site screen</p>
      <h2 className="mt-2 text-2xl font-semibold">Hydro-rich regions with city-scale water systems</h2>
      <p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">At 100 MW running continuously, the planning case needs 876 GWh/year and about {data.screeningWaterM3PerDay.toFixed(0)} m³/day of cooling water at 0.3 L/kWh. The cities below have relevant provincial hydro resources and documented municipal water systems. That does not mean the electricity or water is currently uncommitted.</p>
    </div>
    <div className="mt-5 grid gap-5 xl:grid-cols-3">
      {data.rows.map((row) => {
        const waterShare = row.municipalWaterDailyLitres > 0 ? data.screeningWaterM3PerDay * 1000 / row.municipalWaterDailyLitres * 100 : 0
        return <article key={row.city} className="border border-stone-200 bg-paper p-5 dark:border-stone-800 dark:bg-[#111715]">
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-500 dark:text-stone-400">{row.province}</p>
          <h3 className="mt-2 text-lg font-semibold">{row.city}</h3>
          <p className="mt-4 text-sm leading-6">{row.hydroFact}</p>
          <a className="mt-1 inline-block text-xs font-medium text-petroleum underline dark:text-emerald-300" href={row.hydroSourceUrl} target="_blank" rel="noreferrer">{row.hydroSource}</a>
          <p className="mt-2 text-xs leading-5 text-stone-500 dark:text-stone-400">100 MW scale: {row.hydroScaleComparison}</p>
          <p className="mt-4 text-sm leading-6">{row.gridAndPolicyFact}</p>
          <a className="mt-1 inline-block text-xs font-medium text-petroleum underline dark:text-emerald-300" href={row.gridAndPolicyUrl} target="_blank" rel="noreferrer">{row.gridAndPolicySource}</a>
          <div className="mt-4 border-t border-stone-200 pt-4 dark:border-stone-800">
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500 dark:text-stone-400">Municipal water context</p>
            <p className="mt-2 text-sm leading-6">{row.municipalWaterFact}</p>
            <p className="mt-2 text-xs tabular-nums text-stone-500 dark:text-stone-400">100 MW design case = {waterShare.toFixed(3)}% of that city's reported daily water metric</p>
            <a className="mt-1 inline-block text-xs font-medium text-petroleum underline dark:text-emerald-300" href={row.waterSourceUrl} target="_blank" rel="noreferrer">{row.waterSource}</a>
          </div>
          <p className="mt-4 text-sm font-medium leading-6">{row.assessment}</p>
          <p className="mt-2 text-xs leading-5 text-stone-500 dark:text-stone-400">{row.openQuestion}</p>
        </article>
      })}
    </div>
    <p className="mt-4 max-w-5xl text-xs leading-5 text-stone-500 dark:text-stone-400">{data.methodology} Water comparisons use city-wide output/design figures, not available spare volume. Actual site screening needs a utility connection study, drought-adjusted firm supply, cooling design, water permits, transmission, land, fibre, and community and Indigenous engagement.</p>
  </section>
}

function WorkloadSnapshot() {
  const { data, error } = useGeneratedJson<WorkloadSnapshotPayload>('technology-ollama-workload-snapshot.json')
  if (error) return <p className="mt-4 text-sm text-red-700 dark:text-red-300">Could not load the archived workload: {error}</p>
  if (!data) return <p className="mt-4 text-sm text-stone-500">Loading archived workload…</p>
  const maximumCalls = Math.max(...data.models.map((row) => row.completedCalls), 1)
  const metrics = [
    ['Completed responses', countFormat.format(data.summary.completedCalls)],
    ['Prompt tokens', countFormat.format(data.summary.promptTokens)],
    ['Output tokens', countFormat.format(data.summary.outputTokens)],
    ['Summed response runtime', `${data.summary.totalRuntimeHours.toFixed(2)} h`],
  ]
  return <div className="mt-5">
    <div className="grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-4 dark:border-stone-800 dark:bg-stone-800">
      {metrics.map(([label, value]) => <div key={label} className="bg-paper p-4 dark:bg-[#111715]"><p className="text-xs text-stone-500 dark:text-stone-400">{label}</p><p className="mt-1 text-xl font-semibold tabular-nums">{value}</p></div>)}
    </div>
    <div className="mt-7 border border-stone-200 p-4 dark:border-stone-800 sm:p-5">
      <h3 className="text-sm font-semibold">Completed responses by model</h3>
      <div className="mt-5 space-y-5" role="list" aria-label="Archived Ollama responses by model">
        {data.models.map((row) => <div key={row.model} role="listitem">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-sm">
            <span className="font-medium">{row.model}</span>
            <span className="tabular-nums"><strong>{countFormat.format(row.completedCalls)}</strong> responses · {countFormat.format(row.outputTokens)} output tokens</span>
          </div>
          <div className="mt-2 h-3 bg-stone-100 dark:bg-stone-800" role="meter" aria-label={`${row.model} response count`} aria-valuemin={0} aria-valuemax={maximumCalls} aria-valuenow={row.completedCalls}>
            <div className="h-full bg-petroleum" aria-hidden="true" style={{ width: `${Math.max(row.completedCalls / maximumCalls * 100, row.completedCalls > 0 ? 0.35 : 0)}%` }} />
          </div>
        </div>)}
      </div>
      <p className="mt-5 text-xs leading-5 text-stone-500 dark:text-stone-400">Archived snapshot: {data.snapshotDate}. The bars compare response counts; token and runtime totals are shown as separate measures.</p>
    </div>
    <p className="mt-3 max-w-4xl text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href={data.sourceUrl} target="_blank" rel="noreferrer">{data.source}</a>. Records were deduplicated by model, creation time, and response counters across discovered pyash folders. This is an aggregate snapshot, not a monthly time series; response records do not establish useful work.</p>
  </div>
}

export function TechnologyFlows() {
  return <>
    <PageHeader eyebrow="AI capability and infrastructure · v1 to 2030" title="What AI can do, what it takes, and where it fits" description="A Canada-first research page comparing model capabilities, compute scale, power and water needs, and candidate regions for large AI research infrastructure." />
    <PageBody>
      <div className="grid gap-px border border-stone-200 bg-stone-200 sm:grid-cols-2 xl:grid-cols-4 dark:border-stone-800 dark:bg-stone-800">
        {[
          ['1 · Capability', 'Separate evidence for science, abstraction, professional work, coding and long tasks.'],
          ['2 · Compute tiers', 'Local lab, regional model lab, national cluster and 100 MW campus.'],
          ['3 · Canadian sites', 'Hydro generation and municipal water context, with grid constraints exposed.'],
          ['4 · Useful work', 'Real productivity still needs accepted-task outcomes and human review time.'],
        ].map(([title, description]) => <div key={title} className="bg-paper p-4 dark:bg-[#111715]"><h2 className="text-sm font-semibold">{title}</h2><p className="mt-2 text-xs leading-5 text-stone-600 dark:text-stone-300">{description}</p></div>)}
      </div>

      <CapabilityScorecard />
      <ComputeSizing />
      <CanadianSiteScreen />

      <section className="mt-12 border-l-2 border-petroleum pl-5">
        <h2 className="text-xl font-semibold">Electricity system context</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">The compute cases above are facility scenarios. These charts show the wider demand context: Ontario's data-centre forecast, Canadian electricity generation and U.S. data-centre scale. They do not identify spare capacity at a candidate site.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-semibold">Canada and Ontario electricity context</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">National electricity generation gives a Canada-wide scale reference. The IESO forecast then isolates the Ontario data-centre sub-sector. It includes cloud and other computing demand as well as AI and is not a local Grey-Bruce forecast.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-canada-electricity-generation.json" initialTransformation="indexed" syncUrl={false} /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510001501" target="_blank" rel="noreferrer">Statistics Canada monthly electricity generation by type</a>. Complete calendar years are summed to TWh.</p>
        <div className="mt-10"><ResearchTimeSeriesChart file="technology-ontario-data-centre-electricity.json" initialTransformation="raw" syncUrl={false} showDots /></div>
        <p className="mt-3 max-w-4xl text-xs leading-5 text-stone-500 dark:text-stone-400">Source: <a className="underline" href="https://www.ieso.ca/en/Sector-Participants/Planning-and-Forecasting/Annual-Planning-Outlook" target="_blank" rel="noreferrer">IESO 2026 Annual Planning Outlook</a>. Scenario values stop at 2030 in v1.</p>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">U.S. data-centre scale comparator</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">The U.S. series is separate from Ontario. LBNL estimates 2024 use and publishes 2030 cases; the chart shows only those endpoints and does not fill in intervening years.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-us-data-centre-electricity.json" initialTransformation="raw" syncUrl={false} showDots /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Historical estimates: <a className="underline" href="https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report" target="_blank" rel="noreferrer">LBNL 2024 report</a>. 2024 estimate and 2030 cases: <a className="underline" href="https://eta-publications.lbl.gov/publications/united-states-data-center-energy-2025" target="_blank" rel="noreferrer">LBNL 2025 Update</a>. Data-centre electricity is not AI-only electricity.</p>
        <div className="mt-10"><ResearchTimeSeriesChart file="technology-us-grid-growth-comparison.json" initialTransformation="raw" syncUrl={false} showDots /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Growth is indexed to 2020 = 100. Electricity sales and summer generating capacity come from the <a className="underline" href="https://www.eia.gov/electricity/annual/" target="_blank" rel="noreferrer">U.S. EIA Electric Power Annual</a>; the data-centre series uses LBNL estimates.</p>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Capital entering digital infrastructure</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">U.S. software and computer-equipment investment are broad BEA categories, not AI-specific spending. They show an upstream flow proxy, not where the equipment was installed or what work it performed.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-capital-investment-proxies.json" initialTransformation="indexed" syncUrl={false} /></div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">A local inference example</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">This personal deployment is retained as one measured small-scale example. It is not the organizing case for the capability or infrastructure comparison. Both snapshots publish aggregate model, call, and token counts; neither identifies useful-task completion or machine location.</p>
        <WorkloadSnapshot />
        <h3 className="mt-10 text-lg font-semibold">Recent local deployment aggregate</h3>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">One monthly observation is available so far for this deployment. The chart now marks that observation explicitly; later monthly exports will extend the series. Published fields exclude prompts, responses, call IDs, endpoints, and host information.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-local-inference-calls.json" initialTransformation="raw" syncUrl={false} showDots /></div>
        <div className="mt-10"><ResearchTimeSeriesChart file="technology-local-inference-tokens.json" initialTransformation="raw" syncUrl={false} showDots /></div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold">Electricity sensitivity for a 9B-class local model</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">A published H100 benchmark is transferred to output tokens from the local 9B-class model as an illustrative GPU-only estimate. The 27B workload remains unestimated because the selected reference is not size-matched. No prompt-processing, CPU, memory, remaining server load, or cooling electricity is included.</p>
        <div className="mt-5"><ResearchTimeSeriesChart file="technology-local-gpu-energy-estimate.json" initialTransformation="raw" syncUrl={false} showDots /></div>
        <p className="mt-3 text-xs leading-5 text-stone-500 dark:text-stone-400">Reference: <a className="underline" href="https://ojs.aaai.org/index.php/AAAI/article/view/40535" target="_blank" rel="noreferrer">TokenPowerBench, AAAI 2026</a>. The published setup varies model, context, engine, and batch size, so this is a sensitivity, not local telemetry.</p>
      </section>

      <section className="mt-12 border-l-2 border-petroleum pl-5">
        <h2 className="text-xl font-semibold">What would count as useful work?</h2>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">A later measure could compare accepted task outcomes with electricity and human review time. This v1 has no accepted-task denominator or time-saved observations, so it leaves human-time values as future scenario inputs and does not turn calls, tokens, or benchmark scores into a productivity claim.</p>
      </section>
    </PageBody>
  </>
}
