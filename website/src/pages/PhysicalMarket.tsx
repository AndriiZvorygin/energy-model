import { Activity, Droplets, Gauge } from 'lucide-react'
import { PublicationFigure } from '../components/charts/PublicationFigure'
import { ResearchScatterChart } from '../components/charts/ResearchScatterChart'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { ExplanationCard } from '../components/ExplanationCard'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'
import { percent } from '../lib/format'

export function PhysicalMarket() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Physical oil-market state" title="Inventory explains the path around the forecast" description="Comparative inventory measures whether current U.S. crude stocks sit above or below their prior five-year seasonal norm." /><PageBody>
    <p className="max-w-4xl text-sm leading-6 text-stone-600 dark:text-stone-300">This chart measures the difference between actual oil momentum and the locked rolling GM2 lag-5 path, then places that deviation beside comparative inventory and tradable-exposure tracking.</p>
    <div className="mt-8"><ResearchTimeSeriesChart file="oil-residual-ci.json" initialSeries={['WTI_residual', 'CI_zscore']} initialTransformation="raw" inspectCrossLayer /></div>
    <div className="mt-12 grid gap-4 sm:grid-cols-3">
      <MetricCard icon={Droplets} label="WTI residual explained" value={percent(metrics.wtiResidualExplained)} detail="CI and regime diagnostics" tone="inventory" />
      <MetricCard icon={Droplets} label="Brent residual explained" value={percent(metrics.brentResidualExplained)} detail="CI and regime diagnostics" tone="petroleum" />
      <MetricCard icon={Activity} label="USO tracking residual" value={percent(metrics.usoTrackingResidualExplained)} detail="Explained by CI and regimes" tone="equity" />
    </div>
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={Gauge} eyebrow="Forecast role" title="Not the primary predictor">CI did not improve rolling RMSE or MAE enough to enter the locked Oil YoY model.</ExplanationCard>
      <ExplanationCard icon={Droplets} eyebrow="Diagnostic role" title="Useful for state interpretation">A deficit, surplus, or near-normal reading helps an analyst interpret deviations from the GM2-implied oil path.</ExplanationCard>
    </div>
    <div className="mt-10 max-w-4xl"><ResearchText text={researchData.content.inventoryRole} /></div>
    <section className="mt-12"><h2 className="text-xl font-semibold">Physical-tightness evidence</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">Toggle inventory, production, consumption, and refinery utilization. The standardized view is useful when units differ; no single line determines market tightness.</p><div className="mt-5"><ResearchTimeSeriesChart file="physical-tightness.json" initialTransformation="zscore" syncUrl={false} /></div></section>
    <div className="mt-12"><ResearchScatterChart file="oil-residual-ci.json" xKey="CI_zscore" yKey="WTI_residual" title="Comparative inventory and the WTI residual" description="The scatter supports inspection of physical state around the liquidity-implied path without treating inventory as an independent forecast upgrade." /></div>
    <div className="mt-12 space-y-6"><PublicationFigure src="/charts/final_oil_residual_ci_time_series.png" alt="WTI model residual comparative inventory z-score and USO tracking residual across major regimes" title="Residual and physical-state diagnostic" description="Three aligned panels show when oil and tradable exposure diverge from their benchmark paths, with major shock regimes shaded." source="WTI residual = actual WTI YoY minus rolling GM2-only lag-5 fitted WTI YoY. CI z-score uses the prior five-year same-month inventory distribution." /><PublicationFigure src="/charts/physical_tightness_dashboard.png" alt="Comparative inventory production consumption and refinery utilization through time" title="Physical-tightness indicators" description="Inventory, throughput, supply, and demand remain separate so confirming and conflicting evidence stays visible." source="EIA crude inventories, petroleum production and consumption, and refinery utilization." /><PublicationFigure src="/charts/final_residual_ci_diagnostic.png" alt="Scatter relationship between WTI GM2 residual and comparative inventory" title="Inventory and the liquidity residual" description="CI provides context for the deviation rather than a standalone forecast." source="EIA crude stocks excluding SPR and project rolling GM2 model." /></div>
  </PageBody></>
}
