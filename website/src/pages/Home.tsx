import { ArrowRight, Droplets, Factory, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { TimelineDiagram } from '../components/TimelineDiagram'
import { researchData } from '../data/generated'

export function Home() {
  return (
    <div>
      <section className="research-grid border-b border-stone-200 bg-white px-5 py-12 sm:px-8 lg:px-12 lg:py-20 dark:border-stone-800 dark:bg-[#151c1a]">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-petroleum">An educational research atlas</p>
          <h1 className="mt-4 max-w-5xl text-4xl font-semibold leading-[1.08] text-ink sm:text-5xl lg:text-6xl dark:text-white">Oil, Liquidity, Inventory, and the Real Economy</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-stone-600 dark:text-stone-300">Oil prices are shaped by interacting layers: a liquidity impulse, the physical oil-market state, financial-market response, and real economic energy throughput.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/overview" className="inline-flex items-center gap-2 rounded-md bg-petroleum px-4 py-2.5 text-sm font-semibold text-white">Explore the system <ArrowRight size={16} /></Link>
            <Link to="/methodology" className="inline-flex items-center gap-2 rounded-md border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold dark:border-stone-700 dark:bg-stone-900">Read the methodology</Link>
          </div>
        </div>
      </section>

      <section className="border-b border-stone-200 px-5 py-10 sm:px-8 lg:px-12 lg:py-14 dark:border-stone-800">
        <div className="mx-auto max-w-6xl"><TimelineDiagram /></div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-12 sm:px-8 lg:px-12 lg:py-16">
        <div className="grid gap-px overflow-hidden border border-stone-200 bg-stone-200 md:grid-cols-3 dark:border-stone-800 dark:bg-stone-800">
          {[
            { icon: TrendingUp, label: 'Liquidity impulse', title: 'GM2 leads oil momentum', text: `The locked model uses GM2 from ${researchData.metrics.lockedLagMonths} months earlier to frame current WTI and Brent YoY.`, to: '/liquidity' },
            { icon: Droplets, label: 'Physical state', title: 'Inventory explains deviations', text: 'Comparative inventory is most useful for interpreting rich or cheap oil relative to the liquidity path.', to: '/physical-market' },
            { icon: Factory, label: 'Measured economy', title: 'Energy anchors activity', text: 'Energy and petroleum consumption move closely with GDP, even as GDP per unit of energy rises.', to: '/economy' },
          ].map(({ icon: Icon, label, title, text, to }) => <Link key={title} to={to} className="group bg-white p-6 transition hover:bg-stone-50 dark:bg-[#18201d] dark:hover:bg-stone-900"><Icon className="text-petroleum" size={22} /><p className="mt-5 text-xs font-semibold uppercase tracking-widest text-stone-500">{label}</p><h2 className="mt-2 text-xl font-semibold group-hover:text-petroleum">{title}</h2><p className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">{text}</p><span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-petroleum">Open layer <ArrowRight size={15} /></span></Link>)}
        </div>
      </section>
    </div>
  )
}
