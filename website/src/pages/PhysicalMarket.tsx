import { Activity, Droplets, Gauge } from 'lucide-react'
import { ChartViewer } from '../components/ChartViewer'
import { ExplanationCard } from '../components/ExplanationCard'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'
import { percent } from '../lib/format'

export function PhysicalMarket() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Physical oil-market state" title="Inventory explains the path around the forecast" description="Comparative inventory measures whether current U.S. crude stocks sit above or below their prior five-year seasonal norm." /><PageBody>
    <div className="grid gap-4 sm:grid-cols-3">
      <MetricCard icon={Droplets} label="WTI residual explained" value={percent(metrics.wtiResidualExplained)} detail="CI and regime diagnostics" tone="inventory" />
      <MetricCard icon={Droplets} label="Brent residual explained" value={percent(metrics.brentResidualExplained)} detail="CI and regime diagnostics" tone="petroleum" />
      <MetricCard icon={Activity} label="USO tracking residual" value={percent(metrics.usoTrackingResidualExplained)} detail="Explained by CI and regimes" tone="equity" />
    </div>
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={Gauge} eyebrow="Forecast role" title="Not the primary predictor">CI did not improve rolling RMSE or MAE enough to enter the locked Oil YoY model.</ExplanationCard>
      <ExplanationCard icon={Droplets} eyebrow="Diagnostic role" title="Useful for state interpretation">A deficit, surplus, or near-normal reading helps an analyst interpret deviations from the GM2-implied oil path.</ExplanationCard>
    </div>
    <div className="mt-10 max-w-4xl"><ResearchText text={researchData.content.inventoryRole} /></div>
    <div className="mt-12 space-y-10">
      <ChartViewer src="/charts/final_oil_residual_ci_time_series.png" alt="WTI model residual comparative inventory z-score and USO tracking residual across major regimes" title="Residual and physical-state diagnostic" description="Three aligned panels show when oil and tradable exposure diverge from their benchmark paths, with major shock regimes shaded." source="WTI residual = actual WTI YoY minus rolling GM2-only lag-5 fitted WTI YoY. CI z-score uses the prior five-year same-month inventory distribution. USO residual = USO YoY minus WTI YoY." />
      <ChartViewer src="/charts/final_residual_ci_diagnostic.png" alt="Scatter relationship between WTI GM2 residual and comparative inventory" title="Inventory and the liquidity residual" description="The relationship is informative but incomplete: CI provides context for the deviation rather than a standalone forecast." source="EIA crude stocks excluding SPR and project rolling GM2 model. Regime variables cover 2008-09, 2014-17, 2020-21, and 2022-23." />
    </div>
  </PageBody></>
}
