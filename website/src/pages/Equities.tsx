import { Activity, CandlestickChart, TriangleAlert } from 'lucide-react'
import { PublicationFigure } from '../components/charts/PublicationFigure'
import { ResearchLagChart } from '../components/charts/ResearchLagChart'
import { ResearchScatterChart } from '../components/charts/ResearchScatterChart'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { ExplanationCard } from '../components/ExplanationCard'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'
import { decimal } from '../lib/format'

export function Equities() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Financial market response" title="Stocks provide context, not an oil forecast upgrade" description="The S&P 500 and oil share risk, growth, and inflation information, but adding stocks does not improve the locked oil model by the project’s five-percent rule." /><PageBody>
    <p className="max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">Monthly log returns show market co-movement without the overlap built into YoY growth. Toggle to the YoY series for macro-cycle context, but do not interpret its negative lag pattern as a general timing rule.</p>
    <div className="mt-8"><ResearchTimeSeriesChart file="oil-equities.json" initialSeries={['SP500_return', 'WTI_return', 'Brent_return']} initialTransformation="raw" inspectCrossLayer /></div>
    <div className="mt-12 grid gap-4 sm:grid-cols-2">
      <MetricCard icon={CandlestickChart} label="SP500–WTI monthly returns" value={decimal(metrics.sp500WtiReturnCorrelation)} detail="Strongest at lag 0: contemporaneous" tone="equity" />
      <MetricCard icon={CandlestickChart} label="SP500–Brent monthly returns" value={decimal(metrics.sp500BrentReturnCorrelation)} detail="Strongest at lag 0: contemporaneous" tone="signal" />
    </div>
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={Activity} eyebrow="Macro cycle" title="YoY lead-lag is broad context">Overlapping YoY series are smoothed and autocorrelated, so the negative oil-leading-stock result is a stress pattern rather than a precise timing rule.</ExplanationCard>
      <ExplanationCard icon={TriangleAlert} eyebrow="Market timing" title="Returns are noisier and more relevant">Monthly return evidence is contemporaneous in the full sample and does not show a stable oil-leading-stock rule outside shocks.</ExplanationCard>
    </div>
    <div className="mt-12"><ResearchLagChart mode="equity" title="Monthly return lead-lag" description="Return correlations test whether either market consistently moves first. Full-sample evidence is strongest near contemporaneous timing and remains regime-dependent." /></div>
    <div className="mt-12"><ResearchScatterChart file="oil-equities.json" xKey="SP500_return" yKey="WTI_return" title="Monthly S&P 500 and WTI returns" description="The scatter shows shared risk and growth movement, dispersion, and shock outliers without imposing a lead relationship." /></div>
    <div className="mt-12 space-y-6"><PublicationFigure src="/charts/oil_equity_return_lag_correlation.png" alt="Monthly and quarterly SP500 oil return lag correlation robustness results" title="Return-based robustness" description="The return tests sharply qualify the apparent thirteen-month YoY stress pattern." source="FRED SP500 and WTI/Brent monthly series." /><PublicationFigure src="/charts/sp500_vs_wti_yoy.png" alt="S&P 500 and WTI year-over-year series over time" title="The macro-cycle view" description="YoY series reveal broad stress cycles but should not be read as tradable entry and exit dates." source="FRED SP500 and WTI." /></div>
  </PageBody></>
}
