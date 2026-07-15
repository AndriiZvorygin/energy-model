import { useState } from 'react'
import { ArrowDown, Banknote, BarChart3, Droplets, Factory, Fuel, Landmark } from 'lucide-react'

const stages = [
  { title: 'Global liquidity', short: 'GM2', icon: Banknote, tone: 'bg-signal', text: 'Broad money supplies the leading financial impulse in the locked oil-momentum model.' },
  { title: 'Oil momentum', short: 'WTI + Brent', icon: Fuel, tone: 'bg-petroleum', text: 'Benchmark oil prices translate the liquidity impulse into observable year-over-year momentum.' },
  { title: 'Physical state', short: 'Inventory', icon: Droplets, tone: 'bg-inventory', text: 'Comparative inventory helps explain whether oil is rich or cheap versus the liquidity-implied path.' },
  { title: 'Tradable exposure', short: 'USO', icon: BarChart3, tone: 'bg-equity', text: 'USO shows the investor return pathway, including roll yield, fees, and fund structure.' },
  { title: 'Energy use', short: 'Throughput', icon: Factory, tone: 'bg-stone-600', text: 'Energy and petroleum consumption anchor industrial activity in the physical economy.' },
  { title: 'Measured output', short: 'GDP', icon: Landmark, tone: 'bg-stone-900 dark:bg-stone-200', text: 'GDP records the economic outcome; GDP per energy captures efficiency and structural change.' },
]

export function TimelineDiagram() {
  const [active, setActive] = useState(0)
  const ActiveIcon = stages[active].icon

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_0.7fr] lg:items-center">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {stages.map((stage, index) => {
          const Icon = stage.icon
          return (
            <div key={stage.title} className="relative">
              <button
                type="button"
                onClick={() => setActive(index)}
                className={`flex h-28 w-full flex-col items-start justify-between border p-3 text-left transition ${active === index ? 'border-petroleum bg-white shadow-quiet dark:bg-[#18201d]' : 'border-stone-200 bg-white/60 hover:border-stone-400 dark:border-stone-800 dark:bg-stone-900/50'}`}
                aria-pressed={active === index}
              >
                <span className={`flex h-7 w-7 items-center justify-center rounded-md text-white ${stage.tone}`}><Icon size={15} /></span>
                <span><span className="block text-xs font-semibold text-ink dark:text-white">{stage.title}</span><span className="mt-1 block text-[11px] text-stone-500">{stage.short}</span></span>
              </button>
              {index < stages.length - 1 && <ArrowDown className="absolute -bottom-4 left-1/2 z-10 -translate-x-1/2 text-stone-400 lg:-right-3 lg:bottom-auto lg:left-auto lg:top-1/2 lg:-translate-y-1/2 lg:-rotate-90" size={14} />}
            </div>
          )
        })}
      </div>
      <div className="border-l-2 border-petroleum pl-5" aria-live="polite">
        <ActiveIcon className="mb-3 text-petroleum" size={24} aria-hidden="true" />
        <p className="text-xs font-semibold uppercase tracking-widest text-petroleum">Layer {active + 1} of {stages.length}</p>
        <h3 className="mt-1 text-xl font-semibold dark:text-white">{stages[active].title}</h3>
        <p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">{stages[active].text}</p>
      </div>
    </div>
  )
}
