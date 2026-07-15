import { Activity, CandlestickChart, TriangleAlert } from 'lucide-react'
import { ChartViewer } from '../components/ChartViewer'
import { ExplanationCard } from '../components/ExplanationCard'
import { InteractiveLagChart } from '../components/InteractiveLagChart'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'
import { decimal } from '../lib/format'

export function Equities() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Financial market response" title="Stocks provide context, not an oil forecast upgrade" description="The S&P 500 and oil share risk, growth, and inflation information, but adding stocks does not improve the locked oil model by the project’s five-percent rule." /><PageBody>
    <div className="grid gap-4 sm:grid-cols-2">
      <MetricCard icon={CandlestickChart} label="SP500–WTI monthly returns" value={decimal(metrics.sp500WtiReturnCorrelation)} detail="Strongest at lag 0: contemporaneous" tone="equity" />
      <MetricCard icon={CandlestickChart} label="SP500–Brent monthly returns" value={decimal(metrics.sp500BrentReturnCorrelation)} detail="Strongest at lag 0: contemporaneous" tone="signal" />
    </div>
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={Activity} eyebrow="Macro cycle" title="YoY lead-lag is broad context">Overlapping YoY series are smoothed and autocorrelated, so the negative oil-leading-stock result is a stress pattern rather than a precise timing rule.</ExplanationCard>
      <ExplanationCard icon={TriangleAlert} eyebrow="Market timing" title="Returns are noisier and more relevant">Monthly return evidence is contemporaneous in the full sample and does not show a stable oil-leading-stock rule outside shocks.</ExplanationCard>
    </div>
    <section className="mt-14"><p className="text-xs font-semibold uppercase tracking-widest text-petroleum">Interactive evidence</p><h2 className="mt-2 text-2xl font-semibold">Monthly return lead-lag</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">This non-overlapping return view is more relevant to timing questions than YoY comparisons, though it remains noisy and regime-dependent.</p><div className="mt-5"><InteractiveLagChart data={researchData.equityReturnLagSeries} convention="Project convention: positive lag means the stock market leads oil; negative lag means oil leads stocks; zero is contemporaneous." /></div></section>
    <div className="mt-12 space-y-10">
      <ChartViewer src="/charts/oil_equity_return_lag_correlation.png" alt="Monthly and quarterly SP500 oil return lag correlation robustness results" title="Return-based robustness" description="The return tests sharply qualify the apparent thirteen-month YoY stress pattern." source="FRED SP500 and WTI/Brent monthly series. Monthly log returns use non-overlapping one-month changes; quarterly returns use three-month changes." />
      <ChartViewer src="/charts/sp500_vs_wti_yoy.png" alt="S&P 500 and WTI year-over-year series over time" title="The macro-cycle view" description="YoY series reveal broad stress cycles but should not be read as tradable entry and exit dates." source="FRED SP500 and WTI. YoY = 100 × (level / level 12 months earlier − 1)." />
    </div>
  </PageBody></>
}
