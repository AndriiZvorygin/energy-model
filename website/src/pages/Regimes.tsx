import { ChartViewer } from '../components/ChartViewer'
import { PageBody, PageHeader } from '../components/PageHeader'
import { ResearchText } from '../components/ResearchText'
import { researchData } from '../data/generated'

export function Regimes() {
  return <><PageHeader eyebrow="System states" title="Regimes describe sequences, not labels in isolation" description="Expansion can give way to physical tightening, affordability stress, transmission, demand destruction, price collapse, after-effects, and recovery." /><PageBody><div className="max-w-4xl"><ResearchText text={researchData.systemResponse.content.regimes} /></div><div className="mt-12 space-y-10"><ChartViewer src="/charts/regime_timeline.png" alt="Timeline of historical energy and economic regimes" title="Historical regime timeline" description="Episode boundaries provide comparison windows; they are not an automatic current-state classifier." source="Project-defined historical episodes using EIA, FRED, BEA and BLS observations." /><ChartViewer src="/charts/demand_destruction_cycle.png" alt="Demand destruction sequence around oil price peaks" title="Demand destruction cycle" description="A falling oil price can be part of worsening conditions when activity and demand are contracting." source="WTI, petroleum consumption, industrial production and NBER recession periods." /></div></PageBody></>
}
