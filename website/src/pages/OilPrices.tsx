import { BarChart3, Factory, Fuel, Ship } from 'lucide-react'
import { ChartViewer } from '../components/ChartViewer'
import { ExplanationCard } from '../components/ExplanationCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'

export function OilPrices() {
  return <><PageHeader eyebrow="Oil price layers" title="There is no single barrel price" description="Benchmarks, realised physical costs, and investor-accessible oil exposure answer different questions and can diverge materially." /><PageBody>
    <div className="grid gap-4 sm:grid-cols-2">
      <ExplanationCard icon={Fuel} eyebrow="WTI" title="U.S. benchmark">A futures-linked benchmark price and the locked model’s primary Oil YoY target.</ExplanationCard>
      <ExplanationCard icon={Ship} eyebrow="Brent" title="International benchmark">The global seaborne benchmark used as a parallel target for the liquidity relationship.</ExplanationCard>
      <ExplanationCard icon={Factory} eyebrow="RAC" title="Realised refiner cost">The average crude acquisition cost actually paid by U.S. refiners.</ExplanationCard>
      <ExplanationCard icon={BarChart3} eyebrow="USO" title="Investor-accessible exposure">A tradable ETF pathway affected by futures roll yield, fees, tracking differences, and fund structure.</ExplanationCard>
    </div>
    <div className="mt-10 max-w-4xl"><ResearchText text={researchData.content.physicalPrices} /></div>
    <div className="mt-12 space-y-10">
      <ChartViewer src="/charts/final_oil_price_layers_time_series.png" alt="Standardized WTI Brent RAC composite and USO year-over-year series over time" title="Benchmark, realised, and tradable oil layers" description="Standardizing the series makes their common cycles and meaningful divergences visible on one scale." source="WTI and Brent from FRED; RAC composite from EIA; USO adjusted close from Yahoo Finance. Each series is monthly YoY, then standardized within its available sample." />
      <ChartViewer src="/charts/physical_realised_prices_vs_benchmarks.png" alt="Physical realised crude prices compared with WTI and Brent benchmarks" title="What refiners paid versus quoted benchmarks" description="Realised crude costs track benchmarks closely but retain basis differences caused by crude quality, location, transport, and timing." source="EIA Petroleum Marketing Monthly refiner acquisition, first purchase, and imported landed cost series; FRED WTI and Brent." />
      <ChartViewer src="/charts/uso_vs_wti_yoy.png" alt="USO year-over-year performance compared with WTI year-over-year price change" title="USO is exposure, not spot oil" description="The ETF follows oil directionally while its cumulative return path can separate from benchmark changes." source="Yahoo Finance USO adjusted close and FRED WTI monthly averages. USO tracking residual = USO YoY minus WTI YoY." />
    </div>
  </PageBody></>
}
