import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const websiteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const projectRoot = resolve(websiteRoot, '..')
const analysisRoot = resolve(projectRoot, 'analysis')
const chartRoot = resolve(projectRoot, 'charts')

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        field += '"'
        i += 1
      } else {
        quoted = !quoted
      }
    } else if (char === ',' && !quoted) {
      row.push(field)
      field = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i += 1
      row.push(field)
      if (row.some((value) => value.length > 0)) rows.push(row)
      row = []
      field = ''
    } else {
      field += char
    }
  }
  if (field.length || row.length) {
    row.push(field)
    rows.push(row)
  }

  const [headers, ...records] = rows
  return records.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])))
}

const readText = (path) => readFile(resolve(projectRoot, path), 'utf8')
const number = (value) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}
const section = (markdown, heading) => {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = markdown.match(new RegExp(`## ${escaped}\\n\\n([\\s\\S]*?)(?=\\n## |$)`))
  return match?.[1]?.trim() ?? ''
}
const bestCorrelation = (rows, metric, oilMetric, sample = 'full') =>
  rows
    .filter((row) => row.sample === sample && row.metric === metric && row.oil_metric === oilMetric)
    .sort((a, b) => Math.abs(number(b.correlation) ?? 0) - Math.abs(number(a.correlation) ?? 0))[0]

const [
  findingsCsv,
  hierarchyCsv,
  lagCsv,
  equityReturnsCsv,
  executiveSummary,
  integratedAtlas,
  modelCard,
  physicalFindings,
  equityFindings,
  equityRobustness,
  energyFindings,
  usoFindings,
] = await Promise.all([
  readText('analysis/final_findings_table.csv'),
  readText('analysis/system_signal_hierarchy.csv'),
  readText('analysis/lag_correlations.csv'),
  readText('analysis/oil_equity_return_lag_summary.csv'),
  readText('analysis/executive_summary.md'),
  readText('analysis/integrated_lead_lag_atlas.md'),
  readText('analysis/model_card.md'),
  readText('analysis/physical_realised_price_findings.md'),
  readText('analysis/oil_equity_findings.md'),
  readText('analysis/oil_equity_robustness.md'),
  readText('analysis/energy_gdp_findings.md'),
  readText('analysis/uso_findings.md'),
])

const findings = parseCsv(findingsCsv)
const hierarchy = parseCsv(hierarchyCsv)
const lagRows = parseCsv(lagCsv)
const equityReturns = parseCsv(equityReturnsCsv)
const wti = findings.find((row) => row.target === 'WTI_YoY')
const brent = findings.find((row) => row.target === 'Brent_YoY')
const snapshot = findings.find((row) => row.target === 'current_signal_snapshot')
const energy = hierarchy.find((row) => row.signal === 'Energy consumption')
const petroleum = hierarchy.find((row) => row.signal === 'Petroleum consumption')
const monthlyWti = bestCorrelation(equityReturns, 'monthly_log_return', 'WTI_log_return_1m')
const monthlyBrent = bestCorrelation(equityReturns, 'monthly_log_return', 'Brent_log_return_1m')
const usoR2 = Number(usoFindings.match(/full-sample R2 ([0-9]+(?:\.[0-9]+)?)/)?.[1] ?? 0)

const data = {
  generatedAt: new Date().toISOString(),
  metrics: {
    lockedLagMonths: number(wti?.locked_lag_months),
    wtiPeakLagMonths: number(wti?.peak_correlation_lag_months),
    wtiLagCorrelation: number(wti?.peak_correlation),
    brentPeakLagMonths: number(brent?.peak_correlation_lag_months),
    brentLagCorrelation: number(brent?.peak_correlation),
    wtiRollingRmse: number(wti?.rolling_rmse_60m),
    brentRollingRmse: number(brent?.rolling_rmse_60m),
    wtiResidualExplained: number(wti?.residual_explained_variance_ci_regime),
    brentResidualExplained: number(brent?.residual_explained_variance_ci_regime),
    usoTrackingResidualExplained: usoR2,
    sp500WtiReturnCorrelation: number(monthlyWti?.correlation),
    sp500BrentReturnCorrelation: number(monthlyBrent?.correlation),
    energyGdpCorrelation: number(energy?.value),
    petroleumGdpCorrelation: number(petroleum?.value),
  },
  snapshot: {
    month: snapshot?.latest_complete_month,
    gm2Usd: number(snapshot?.latest_gm2_usd),
    gm2Yoy: number(snapshot?.latest_gm2_yoy),
    wtiYoy: number(snapshot?.latest_wti_yoy),
    brentYoy: number(snapshot?.latest_brent_yoy),
    ciZscore: number(snapshot?.latest_ci_zscore),
    impliedWtiYoy: number(snapshot?.model_implied_wti_yoy),
    wtiResidual: number(snapshot?.wti_residual),
    regime: snapshot?.regime,
    ciInterpretation: snapshot?.ci_interpretation,
  },
  gm2LagSeries: lagRows
    .filter((row) => ['WTI_YoY', 'Brent_YoY'].includes(row.target) && number(row.lag_months) !== null)
    .map((row) => ({ target: row.target.replace('_YoY', ''), lag: number(row.lag_months), correlation: number(row.correlation) })),
  equityReturnLagSeries: equityReturns
    .filter((row) => row.sample === 'full' && row.metric === 'monthly_log_return')
    .map((row) => ({
      target: row.oil_metric.startsWith('WTI') ? 'WTI' : 'Brent',
      lag: number(row.lag_periods),
      correlation: number(row.correlation),
    })),
  content: {
    headline: section(executiveSummary, 'Headline'),
    integratedView: section(integratedAtlas, 'Core Interpretation'),
    inventoryRole: section(integratedAtlas, 'Where Does Comparative Inventory Fit?'),
    equityRole: section(equityRobustness, 'Interpretation'),
    physicalPrices: section(physicalFindings, 'Interpretation'),
    energyRole: section(energyFindings, 'Interpretation'),
    usoRole: section(usoFindings, 'Scope'),
    dataSources: section(modelCard, 'Data Sources'),
    formulas: section(modelCard, 'Core Formulas'),
    targets: section(modelCard, 'Target Definitions'),
    lagConvention: section(modelCard, 'Lag Convention'),
    validation: section(modelCard, 'Validation Method'),
    caveats: section(modelCard, 'Known Caveats'),
    shockPeriods: section(modelCard, 'Shock Periods'),
    suitableUses: section(modelCard, 'Suitable Uses'),
    unsuitableUses: section(modelCard, 'Unsuitable Uses'),
    equityEvidence: section(equityFindings, 'Correlation Evidence'),
  },
}

const chartFiles = [
  'final_gm2_oil_lead_chart.png',
  'final_gm2_leads_oil_time_series.png',
  'final_oil_residual_ci_time_series.png',
  'final_residual_ci_diagnostic.png',
  'final_oil_price_layers_time_series.png',
  'physical_realised_prices_vs_benchmarks.png',
  'uso_vs_wti_yoy.png',
  'oil_equity_return_lag_correlation.png',
  'oil_equity_rolling_correlation.png',
  'sp500_vs_wti_yoy.png',
  'final_energy_gdp_time_series.png',
  'gdp_per_energy_trend.png',
  'final_lead_lag_network.png',
]

await mkdir(resolve(websiteRoot, 'src/data'), { recursive: true })
await mkdir(resolve(websiteRoot, 'public/charts'), { recursive: true })
await Promise.all(chartFiles.map((file) => copyFile(resolve(chartRoot, file), resolve(websiteRoot, 'public/charts', file))))
await writeFile(
  resolve(websiteRoot, 'src/data/generated.ts'),
  `// Generated from ../analysis and ../charts by npm run generate:data. Do not edit manually.\nexport const researchData = ${JSON.stringify(data, null, 2)} as const\n`,
)

console.log(`Generated website research data and copied ${chartFiles.length} charts.`)
