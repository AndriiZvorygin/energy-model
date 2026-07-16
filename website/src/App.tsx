import { lazy, Suspense, useEffect, useState } from 'react'
import { Activity, AlertTriangle, BarChart3, BookOpen, BriefcaseBusiness, CircleHelp, Clock3, Droplets, Factory, Fuel, History, Home as HomeIcon, House, Landmark, ListFilter, Map, Menu, Moon, Network, Route as RouteIcon, Scale, Sun, TrendingUp, X } from 'lucide-react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { readThemePreference, resolveTheme, type ThemePreference } from './lib/theme'
const Home = lazy(() => import('./pages/Home').then((module) => ({ default: module.Home })))
const Overview = lazy(() => import('./pages/Overview').then((module) => ({ default: module.Overview })))
const Liquidity = lazy(() => import('./pages/Liquidity').then((module) => ({ default: module.Liquidity })))
const PhysicalMarket = lazy(() => import('./pages/PhysicalMarket').then((module) => ({ default: module.PhysicalMarket })))
const OilPrices = lazy(() => import('./pages/OilPrices').then((module) => ({ default: module.OilPrices })))
const Equities = lazy(() => import('./pages/Equities').then((module) => ({ default: module.Equities })))
const Economy = lazy(() => import('./pages/Economy').then((module) => ({ default: module.Economy })))
const Methodology = lazy(() => import('./pages/Methodology').then((module) => ({ default: module.Methodology })))
const SystemResponse = lazy(() => import('./pages/SystemResponse').then((module) => ({ default: module.SystemResponse })))
const CurrentState = lazy(() => import('./pages/CurrentState').then((module) => ({ default: module.CurrentState })))
const Regimes = lazy(() => import('./pages/Regimes').then((module) => ({ default: module.Regimes })))
const Symptoms = lazy(() => import('./pages/Symptoms').then((module) => ({ default: module.Symptoms })))
const Indicators = lazy(() => import('./pages/Indicators').then((module) => ({ default: module.Indicators })))
const Episodes = lazy(() => import('./pages/Episodes').then((module) => ({ default: module.Episodes })))
const EnergyBurden = lazy(() => import('./pages/EnergyBurden').then((module) => ({ default: module.EnergyBurden })))
const Labour = lazy(() => import('./pages/Labour').then((module) => ({ default: module.Labour })))
const Roadmap = lazy(() => import('./pages/Roadmap').then((module) => ({ default: module.Roadmap })))
const OutputQuality = lazy(() => import('./pages/OutputQuality').then((module) => ({ default: module.OutputQuality })))
const Canada = lazy(() => import('./pages/Canada').then((module) => ({ default: module.Canada })))
const CanadaCurrentState = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaCurrentState })))
const CanadaEnergy = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaEnergy })))
const CanadaEconomy = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaEconomy })))
const CanadaLabour = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaLabour })))
const CanadaHouseholds = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaHouseholds })))
const CanadaOntario = lazy(() => import('./pages/CanadaCurrentState').then((module) => ({ default: module.CanadaOntario })))
const CanadaUsComparison = lazy(() => import('./pages/CanadaUsComparison').then((module) => ({ default: module.CanadaUsComparison })))
const CanadaSymptoms = lazy(() => import('./pages/CanadaSymptoms').then((module) => ({ default: module.CanadaSymptoms })))
const CanadaRegimes = lazy(() => import('./pages/CanadaRegimes').then((module) => ({ default: module.CanadaRegimes })))
const Affordability = lazy(() => import('./pages/Affordability').then((module) => ({ default: module.Affordability })))
const FoodAffordability = lazy(() => import('./pages/FoodAffordability').then((module) => ({ default: module.FoodAffordability })))
const HousingAffordability = lazy(() => import('./pages/HousingAffordability').then((module) => ({ default: module.HousingAffordability })))

const navItems = [
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/canada', label: 'Canadian conditions', icon: Map },
  { to: '/canada/current-state', label: 'Canada current state', icon: Activity },
  { to: '/canada/regimes', label: 'Canada regimes', icon: BarChart3 },
  { to: '/canada/symptoms', label: 'Canada symptoms', icon: AlertTriangle },
  { to: '/affordability', label: 'Food and housing', icon: House },
  { to: '/canada/ontario', label: 'Ontario context', icon: Map },
  { to: '/compare/canada-us', label: 'Canada–U.S. comparison', icon: Scale },
  { to: '/overview', label: 'System overview', icon: Network },
  { to: '/system-response', label: 'System response', icon: RouteIcon },
  { to: '/current-state/us', label: 'U.S. current state', icon: Activity },
  { to: '/regimes', label: 'Regimes', icon: BarChart3 },
  { to: '/symptoms', label: 'Symptoms', icon: AlertTriangle },
  { to: '/indicators', label: 'Indicators', icon: ListFilter },
  { to: '/episodes', label: 'Episodes', icon: History },
  { to: '/energy-burden', label: 'Energy burden', icon: Scale },
  { to: '/labour', label: 'Labour', icon: BriefcaseBusiness },
  { to: '/liquidity', label: 'Liquidity', icon: TrendingUp },
  { to: '/physical-market', label: 'Physical market', icon: Droplets },
  { to: '/oil-prices', label: 'Oil prices', icon: Fuel },
  { to: '/equities', label: 'Equities', icon: Landmark },
  { to: '/economy', label: 'Economy', icon: Factory },
  { to: '/output-quality', label: 'Output quality', icon: Scale },
  { to: '/methodology', label: 'Methodology', icon: BookOpen },
  { to: '/roadmap', label: 'Roadmap', icon: Map },
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
  const [themePreference, setThemePreference] = useState<ThemePreference>(readThemePreference)
  const [resolvedTheme, setResolvedTheme] = useState(() => resolveTheme(readThemePreference()))
  const [menuOpen, setMenuOpen] = useState(false)
  const [glossaryOpen, setGlossaryOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const update = () => setResolvedTheme(resolveTheme(themePreference))
    update()
    localStorage.setItem('themePreference', themePreference)
    localStorage.removeItem('theme')
    const timer = window.setInterval(update, 60_000)
    document.addEventListener('visibilitychange', update)
    return () => { window.clearInterval(timer); document.removeEventListener('visibilitychange', update) }
  }, [themePreference])
  useEffect(() => {
    document.documentElement.classList.toggle('dark', resolvedTheme === 'dark')
    document.documentElement.dataset.theme = resolvedTheme
    document.documentElement.dataset.themePreference = themePreference
  }, [resolvedTheme, themePreference])
  useEffect(() => setMenuOpen(false), [location.pathname])
  useEffect(() => window.scrollTo(0, 0), [location.pathname])

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-stone-200 bg-paper/95 px-4 backdrop-blur lg:hidden dark:border-stone-800 dark:bg-[#111715]/95">
        <NavLink to="/" className="font-semibold text-ink dark:text-white">Canadian energy research</NavLink>
        <button type="button" onClick={() => setMenuOpen(!menuOpen)} className="flex h-9 w-9 items-center justify-center rounded-md border border-stone-300 dark:border-stone-700" aria-label="Toggle navigation">{menuOpen ? <X size={19} /> : <Menu size={19} />}</button>
      </header>

      <aside className={`${menuOpen ? 'block' : 'hidden'} fixed inset-x-0 top-16 z-30 max-h-[calc(100vh-4rem)] overflow-y-auto border-b border-stone-200 bg-paper p-4 lg:sticky lg:top-0 lg:block lg:h-screen lg:max-h-none lg:border-b-0 lg:border-r lg:p-5 dark:border-stone-800 dark:bg-[#111715]`}>
        <NavLink to="/" className="mb-6 hidden lg:block">
          <span className="block text-xs font-semibold uppercase tracking-widest text-petroleum">Research atlas</span>
          <span className="mt-2 block max-w-40 text-xl font-semibold leading-6 text-ink dark:text-white">Canada in the global energy system</span>
        </NavLink>
        <nav className="grid grid-cols-2 gap-1 sm:grid-cols-4 lg:block" aria-label="Research sections">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition lg:mb-0.5 ${isActive ? 'bg-petroleum text-white' : 'text-stone-600 hover:bg-stone-200/70 hover:text-ink dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-white'}`}>
              <Icon size={17} aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-5 border-t border-stone-200 pt-5 dark:border-stone-800">
          <button type="button" onClick={() => setGlossaryOpen(true)} className="flex h-9 w-full items-center justify-center gap-2 rounded-md border border-stone-300 px-3 text-xs font-semibold dark:border-stone-700"><CircleHelp size={15} />Glossary</button>
          <fieldset className="mt-3"><legend className="mb-2 text-xs font-semibold text-stone-500">Theme · Auto is {resolvedTheme}</legend><div className="grid grid-cols-3 border border-stone-300 dark:border-stone-700">{([
            ['auto', Clock3, 'Automatic theme from local time'],
            ['light', Sun, 'Always use light theme'],
            ['dark', Moon, 'Always use dark theme'],
          ] as const).map(([preference, Icon, label]) => <button key={preference} type="button" title={label} aria-label={label} aria-pressed={themePreference === preference} onClick={() => setThemePreference(preference)} className={`flex h-9 items-center justify-center border-r last:border-r-0 dark:border-stone-700 ${themePreference === preference ? 'bg-petroleum text-white' : 'hover:bg-stone-200 dark:hover:bg-stone-800'}`}><Icon size={15} /></button>)}</div></fieldset>
        </div>
      </aside>

      <main className="min-w-0">
        <Suspense fallback={<div className="flex min-h-[60vh] items-center justify-center text-sm text-stone-500">Loading research section…</div>}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/system-response" element={<SystemResponse />} />
            <Route path="/current-state" element={<CanadaCurrentState />} />
            <Route path="/current-state/us" element={<CurrentState />} />
            <Route path="/canada" element={<Canada />} />
            <Route path="/canada/current-state" element={<CanadaCurrentState />} />
            <Route path="/canada/energy" element={<CanadaEnergy />} />
            <Route path="/canada/economy" element={<CanadaEconomy />} />
            <Route path="/canada/labour" element={<CanadaLabour />} />
            <Route path="/canada/households" element={<CanadaHouseholds />} />
            <Route path="/canada/ontario" element={<CanadaOntario />} />
            <Route path="/canada/regimes" element={<CanadaRegimes />} />
            <Route path="/canada/symptoms" element={<CanadaSymptoms />} />
            <Route path="/affordability" element={<Affordability />} />
            <Route path="/affordability/food" element={<FoodAffordability />} />
            <Route path="/affordability/housing" element={<HousingAffordability />} />
            <Route path="/canada/food" element={<FoodAffordability />} />
            <Route path="/canada/housing" element={<HousingAffordability />} />
            <Route path="/compare/food" element={<FoodAffordability />} />
            <Route path="/compare/housing" element={<HousingAffordability />} />
            <Route path="/owen-sound/affordability" element={<Affordability />} />
            <Route path="/owen-sound/food" element={<FoodAffordability />} />
            <Route path="/owen-sound/housing" element={<HousingAffordability />} />
            <Route path="/compare/canada-us" element={<CanadaUsComparison />} />
            <Route path="/regimes" element={<Regimes />} />
            <Route path="/symptoms" element={<Symptoms />} />
            <Route path="/indicators" element={<Indicators />} />
            <Route path="/episodes" element={<Episodes />} />
            <Route path="/energy-burden" element={<EnergyBurden />} />
            <Route path="/labour" element={<Labour />} />
            <Route path="/liquidity" element={<Liquidity />} />
            <Route path="/physical-market" element={<PhysicalMarket />} />
            <Route path="/oil-prices" element={<OilPrices />} />
            <Route path="/equities" element={<Equities />} />
            <Route path="/economy" element={<Economy />} />
            <Route path="/output-quality" element={<OutputQuality />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/roadmap" element={<Roadmap />} />
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
