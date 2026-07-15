import { Factory, Fuel, TrendingUp } from 'lucide-react'
import { ChartViewer } from '../components/ChartViewer'
import { ExplanationCard } from '../components/ExplanationCard'
import { MetricCard } from '../components/MetricCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { researchData } from '../data/generated'
import { decimal } from '../lib/format'

export function Economy() {
  const { metrics } = researchData
  return <><PageHeader eyebrow="Physical economy" title="Energy throughput anchors measured activity" description="Energy and petroleum consumption move tightly with real GDP at quarterly frequency, while rising GDP per energy captures efficiency and structural change." /><PageBody>
    <div className="grid gap-4 sm:grid-cols-2">
      <MetricCard icon={Factory} label="Energy consumption vs GDP" value={decimal(metrics.energyGdpCorrelation)} detail="Quarterly growth, strongest at lag 0" tone="petroleum" />
      <MetricCard icon={Fuel} label="Petroleum consumption vs GDP" value={decimal(metrics.petroleumGdpCorrelation)} detail="Quarterly growth, strongest at lag 0" tone="signal" />
    </div>
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={Factory} eyebrow="Throughput" title="Energy remains foundational">The high contemporaneous correlations support energy as the physical throughput base beneath measured output.</ExplanationCard>
      <ExplanationCard icon={TrendingUp} eyebrow="Efficiency" title="More GDP per unit of energy">The long-run rise does not imply detachment from energy; it reflects technology, efficiency, and structural change.</ExplanationCard>
    </div>
    <div className="mt-12 space-y-10">
      <ChartViewer src="/charts/final_energy_gdp_time_series.png" alt="Energy consumption petroleum consumption real GDP and industrial production growth with GDP per energy trend" title="Energy and real activity through time" description="The upper panel compares growth rates; the lower panel shows how measured output per unit of energy has risen." source="EIA total energy and petroleum consumption; FRED GDPC1 real GDP and INDPRO industrial production. Quarterly growth rates are aligned without future information." />
      <ChartViewer src="/charts/gdp_per_energy_trend.png" alt="Long-run trend in GDP per unit of energy" title="Efficiency and structural change" description="The economy remains physically grounded in energy throughput while producing more measured GDP per unit consumed." source="Real GDP divided by U.S. total energy consumption. The ratio is an aggregate structural indicator, not a direct engineering efficiency measure." />
    </div>
  </PageBody></>
}
