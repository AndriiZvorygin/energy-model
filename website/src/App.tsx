import { lazy, Suspense, useEffect, useState } from 'react'
import { BookOpen, CircleHelp, Droplets, Factory, Fuel, Home as HomeIcon, Landmark, Menu, Moon, Network, Sun, TrendingUp, X } from 'lucide-react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
const Home = lazy(() => import('./pages/Home').then((module) => ({ default: module.Home })))
const Overview = lazy(() => import('./pages/Overview').then((module) => ({ default: module.Overview })))
const Liquidity = lazy(() => import('./pages/Liquidity').then((module) => ({ default: module.Liquidity })))
const PhysicalMarket = lazy(() => import('./pages/PhysicalMarket').then((module) => ({ default: module.PhysicalMarket })))
const OilPrices = lazy(() => import('./pages/OilPrices').then((module) => ({ default: module.OilPrices })))
const Equities = lazy(() => import('./pages/Equities').then((module) => ({ default: module.Equities })))
const Economy = lazy(() => import('./pages/Economy').then((module) => ({ default: module.Economy })))
const Methodology = lazy(() => import('./pages/Methodology').then((module) => ({ default: module.Methodology })))

const navItems = [
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/overview', label: 'System overview', icon: Network },
  { to: '/liquidity', label: 'Liquidity', icon: TrendingUp },
  { to: '/physical-market', label: 'Physical market', icon: Droplets },
  { to: '/oil-prices', label: 'Oil prices', icon: Fuel },
  { to: '/equities', label: 'Equities', icon: Landmark },
  { to: '/economy', label: 'Economy', icon: Factory },
  { to: '/methodology', label: 'Methodology', icon: BookOpen },
]

const glossary = {
  GM2: 'A USD-converted aggregate of broad money from the United States, euro area, China, and Japan.',
  'Comparative inventory': 'Current U.S. crude inventory minus the prior five-year average for the same month. Its z-score scales that gap by historical variation.',
  WTI: 'West Texas Intermediate, the main U.S. crude-oil benchmark used in the locked model.',
  Brent: 'The international crude-oil benchmark used as a second benchmark target.',
  RAC: 'Refiner Acquisition Cost, the average realised price U.S. refiners paid for crude oil.',
  USO: 'United States Oil Fund, an investor-accessible ETF exposure whose return path can diverge from benchmark oil.',
  'GDP per energy': 'Real GDP divided by energy consumption, used here as a broad efficiency and structural-change measure.',
}

export default function App() {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && matchMedia('(prefers-color-scheme: dark)').matches))
  const [menuOpen, setMenuOpen] = useState(false)
  const [glossaryOpen, setGlossaryOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])
  useEffect(() => setMenuOpen(false), [location.pathname])
  useEffect(() => window.scrollTo(0, 0), [location.pathname])

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-stone-200 bg-paper/95 px-4 backdrop-blur lg:hidden dark:border-stone-800 dark:bg-[#111715]/95">
        <NavLink to="/" className="font-semibold text-ink dark:text-white">Oil system research</NavLink>
        <button type="button" onClick={() => setMenuOpen(!menuOpen)} className="flex h-9 w-9 items-center justify-center rounded-md border border-stone-300 dark:border-stone-700" aria-label="Toggle navigation">{menuOpen ? <X size={19} /> : <Menu size={19} />}</button>
      </header>

      <aside className={`${menuOpen ? 'block' : 'hidden'} fixed inset-x-0 top-16 z-30 border-b border-stone-200 bg-paper p-4 lg:sticky lg:top-0 lg:block lg:h-screen lg:border-b-0 lg:border-r lg:p-5 dark:border-stone-800 dark:bg-[#111715]`}>
        <NavLink to="/" className="mb-8 hidden lg:block">
          <span className="block text-xs font-semibold uppercase tracking-widest text-petroleum">Research atlas</span>
          <span className="mt-2 block max-w-40 text-xl font-semibold leading-6 text-ink dark:text-white">Oil and the macro system</span>
        </NavLink>
        <nav className="grid grid-cols-2 gap-1 sm:grid-cols-4 lg:block" aria-label="Research sections">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition lg:mb-1 ${isActive ? 'bg-petroleum text-white' : 'text-stone-600 hover:bg-stone-200/70 hover:text-ink dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-white'}`}>
              <Icon size={17} aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-5 grid grid-cols-2 gap-2 border-t border-stone-200 pt-5 lg:absolute lg:bottom-5 lg:left-5 lg:right-5 dark:border-stone-800">
          <button type="button" onClick={() => setGlossaryOpen(true)} className="flex items-center justify-center gap-2 rounded-md border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700"><CircleHelp size={15} />Glossary</button>
          <button type="button" onClick={() => setDark(!dark)} className="flex items-center justify-center gap-2 rounded-md border border-stone-300 px-3 py-2 text-xs font-semibold dark:border-stone-700" aria-label={`Use ${dark ? 'light' : 'dark'} theme`}>{dark ? <Sun size={15} /> : <Moon size={15} />}{dark ? 'Light' : 'Dark'}</button>
        </div>
      </aside>

      <main className="min-w-0">
        <Suspense fallback={<div className="flex min-h-[60vh] items-center justify-center text-sm text-stone-500">Loading research section…</div>}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/liquidity" element={<Liquidity />} />
            <Route path="/physical-market" element={<PhysicalMarket />} />
            <Route path="/oil-prices" element={<OilPrices />} />
            <Route path="/equities" element={<Equities />} />
            <Route path="/economy" element={<Economy />} />
            <Route path="/methodology" element={<Methodology />} />
          </Routes>
        </Suspense>
      </main>

      {glossaryOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-labelledby="glossary-title" onClick={() => setGlossaryOpen(false)}>
          <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto bg-white p-6 shadow-2xl dark:bg-[#18201d]" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-widest text-petroleum">Reference</p><h2 id="glossary-title" className="mt-1 text-2xl font-semibold">Glossary</h2></div><button type="button" onClick={() => setGlossaryOpen(false)} className="flex h-9 w-9 items-center justify-center rounded-md border border-stone-300 dark:border-stone-700" aria-label="Close glossary"><X size={18} /></button></div>
            <dl className="mt-6 divide-y divide-stone-200 dark:divide-stone-800">{Object.entries(glossary).map(([term, definition]) => <div key={term} className="grid gap-1 py-4 sm:grid-cols-[150px_1fr] sm:gap-5"><dt className="font-semibold text-ink dark:text-white">{term}</dt><dd className="text-sm leading-6 text-stone-600 dark:text-stone-300">{definition}</dd></div>)}</dl>
          </div>
        </div>
      )}
    </div>
  )
}
