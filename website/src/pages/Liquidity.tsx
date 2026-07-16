import { Clock3, Gauge, LockKeyhole } from 'lucide-react'
import { PublicationFigure } from '../components/charts/PublicationFigure'
import { ResearchLagChart } from '../components/charts/ResearchLagChart'
import { ResearchTimeSeriesChart } from '../components/charts/ResearchTimeSeriesChart'
import { RollingModelPerformanceChart } from '../components/charts/RollingModelPerformanceChart'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'
import { decimal } from '../lib/format'

export function Liquidity() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Liquidity impulse" title="Global M2 leads oil-price momentum" description="The model aggregates G4 broad money in U.S. dollars, measures its year-over-year growth, and relates that signal to later oil-price momentum." /><PageBody>
    <div className="grid gap-4 sm:grid-cols-3">
      <MetricCard icon={Gauge} label="WTI lag correlation" value={decimal(metrics.wtiLagCorrelation)} detail={`Peak at ${metrics.wtiPeakLagMonths} months`} tone="petroleum" />
      <MetricCard icon={Gauge} label="Brent lag correlation" value={decimal(metrics.brentLagCorrelation)} detail={`Peak at ${metrics.brentPeakLagMonths} months`} tone="signal" />
      <MetricCard icon={LockKeyhole} label="Locked model" value={`${metrics.lockedLagMonths} months`} detail="Selected from rolling validation" tone="inventory" />
    </div>

    <div className="mt-12"><ResearchTimeSeriesChart file="gm2-oil-lead.json" initialSeries={['GM2_shifted', 'WTI_YoY', 'Brent_YoY', 'RAC_composite_YoY']} initialTransformation="zscore" lagControl inspectCrossLayer /></div>
    <div className="mt-12"><ResearchLagChart mode="gm2" title="Correlation across GM2 lead times" description="Explore the tested lag range while keeping descriptive correlation separate from the locked rolling-validation choice." /></div>
    <div className="mt-12"><RollingModelPerformanceChart /></div>
    <div className="mt-10 flex items-start gap-3 border-l-2 border-signal pl-5"><Clock3 className="mt-1 shrink-0 text-signal" size={20} /><p className="max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-300">Lead time is an empirical relationship, not a countdown clock. Policy shifts, geopolitics, and physical disruptions can move oil away from the liquidity-implied path.</p></div>
    <div className="mt-12 space-y-6"><PublicationFigure src="/charts/final_gm2_oil_lead_chart.png" alt="GM2 lead relationship with WTI and Brent year-over-year momentum" title="GM2 and the oil lead relationship" description="Simple correlation peaks around four months, close to the locked rolling-validation choice of five months." source="G4 GM2 from FRED, ECB, BOJ, and China monetary sources; WTI and Brent from FRED. Formula: corr(GM2 YoY at t-L, Oil YoY at t)." /><PublicationFigure src="/charts/final_gm2_leads_oil_time_series.png" alt="Time series of GM2 shifted forward five months with WTI Brent and RAC year-over-year momentum" title="Liquidity impulse through time" description="GM2 YoY is visually shifted forward by the locked five-month lead to compare it with subsequent benchmark and realised oil momentum." source="Generated project chart. Series are standardized for comparison; GM2 is aligned using only information available five months earlier." /></div>
  </PageBody></>
}
