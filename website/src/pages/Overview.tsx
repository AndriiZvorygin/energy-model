import { Activity, Droplets, Factory, TrendingUp } from 'lucide-react'
import { ChartViewer } from '../components/ChartViewer'
import { ExplanationCard } from '../components/ExplanationCard'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'

export function Overview() {
  return <><PageHeader eyebrow="System overview" title="A layered model, not a single forecast" description="The project separates the financial impulse, oil-market state, market-pricing context, and physical economic outcome." /><PageBody>
    <div className="max-w-4xl"><ResearchText text={researchData.content.integratedView} /></div>
    <div className="mt-8 grid gap-4 md:grid-cols-2">
      <ExplanationCard icon={TrendingUp} eyebrow="Layer 1" title="Liquidity impulse">Global M2 supplies the strongest leading financial signal for oil-price momentum.</ExplanationCard>
      <ExplanationCard icon={Droplets} eyebrow="Layer 2" title="Physical oil state">Comparative inventory diagnoses whether physical conditions amplify, dampen, or contradict that impulse.</ExplanationCard>
      <ExplanationCard icon={Activity} eyebrow="Layer 3" title="Market pricing">Oil, USO, and equities express overlapping growth and risk expectations through different instruments.</ExplanationCard>
      <ExplanationCard icon={Factory} eyebrow="Layer 4" title="Physical economy">Energy throughput anchors activity, while GDP records the measured economic outcome.</ExplanationCard>
    </div>
    <div className="mt-12"><ChartViewer src="/charts/final_lead_lag_network.png" alt="Network diagram connecting liquidity, oil prices, inventory, equities, energy consumption, industrial production and GDP" title="Integrated lead-lag network" description="The final hierarchy places each signal according to what the evidence supports, without promoting context variables into the locked forecast." source="Project synthesis from generated lead-lag, rolling validation, inventory, equity, and energy-GDP analyses." /></div>
  </PageBody></>
}
