import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ChevronDown,
  Droplets,
  Factory,
  Fuel,
  History,
  Home,
  House,
  Landmark,
  ListFilter,
  Map,
  MapPin,
  Network,
  Route,
  Scale,
  TrendingUp,
  type LucideIcon,
} from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'

type NavigationItem = {
  to: string
  label: string
  icon: LucideIcon
}

type NavigationGroup = {
  id: string
  label: string
  icon: LucideIcon
  items: NavigationItem[]
}

const groups: NavigationGroup[] = [
  {
    id: 'global',
    label: 'Global conditions',
    icon: Network,
    items: [
      { to: '/global', label: 'Global overview', icon: Network },
      { to: '/global/food-security', label: 'Food security', icon: House },
      { to: '/global/nutrition', label: 'Nutrition outcomes', icon: Activity },
      { to: '/global/human-impact', label: 'Human impact', icon: Activity },
      { to: '/global/demography', label: 'Demography', icon: Map },
      { to: '/liquidity', label: 'Global liquidity', icon: TrendingUp },
      { to: '/physical-market', label: 'Physical oil market', icon: Droplets },
      { to: '/oil-prices', label: 'Oil price layers', icon: Fuel },
    ],
  },
  {
    id: 'canada',
    label: 'Canadian conditions',
    icon: Map,
    items: [
      { to: '/canada', label: 'Overview', icon: Map },
      { to: '/canada/current-state', label: 'Current state', icon: Activity },
      { to: '/canada/regimes', label: 'Regimes', icon: BarChart3 },
      { to: '/canada/symptoms', label: 'Symptoms', icon: AlertTriangle },
      { to: '/canada/ontario', label: 'Ontario context', icon: MapPin },
      { to: '/compare/canada-us', label: 'Canada–U.S. comparison', icon: Scale },
    ],
  },
  {
    id: 'affordability',
    label: 'Affordability',
    icon: House,
    items: [
      { to: '/affordability', label: 'Canada affordability', icon: House },
      { to: '/affordability/food', label: 'Canada food', icon: House },
      { to: '/affordability/housing', label: 'Canada housing', icon: House },
      { to: '/owen-sound/affordability', label: 'Owen Sound overview', icon: MapPin },
      { to: '/owen-sound/food', label: 'Owen Sound food', icon: MapPin },
      { to: '/owen-sound/housing', label: 'Owen Sound housing', icon: MapPin },
    ],
  },
  {
    id: 'oil-markets',
    label: 'Oil and markets',
    icon: Fuel,
    items: [
      { to: '/equities', label: 'Equities', icon: Landmark },
    ],
  },
  {
    id: 'system-economy',
    label: 'System and economy',
    icon: Network,
    items: [
      { to: '/overview', label: 'System overview', icon: Network },
      { to: '/system-response', label: 'System response', icon: Route },
      { to: '/energy-burden', label: 'Energy burden', icon: Scale },
      { to: '/economy', label: 'Energy and GDP', icon: Factory },
      { to: '/labour', label: 'Labour', icon: BriefcaseBusiness },
      { to: '/output-quality', label: 'Output quality', icon: Scale },
    ],
  },
  {
    id: 'research',
    label: 'Research and methods',
    icon: BookOpen,
    items: [
      { to: '/current-state/us', label: 'U.S. current state', icon: Activity },
      { to: '/regimes', label: 'U.S. regimes', icon: BarChart3 },
      { to: '/symptoms', label: 'U.S. symptoms', icon: AlertTriangle },
      { to: '/indicators', label: 'Indicator catalogue', icon: ListFilter },
      { to: '/episodes', label: 'Historical episodes', icon: History },
      { to: '/methodology', label: 'Methodology', icon: BookOpen },
      { to: '/roadmap', label: 'Roadmap', icon: Map },
    ],
  },
]

const activeGroup = (pathname: string) =>
  groups.find((group) => group.items.some((item) => item.to === pathname))?.id

export function ResearchNavigation() {
  const location = useLocation()
  const currentGroup = activeGroup(location.pathname)
  const [expanded, setExpanded] = useState<string | null>(currentGroup ?? 'canada')

  useEffect(() => {
    if (currentGroup) setExpanded(currentGroup)
  }, [currentGroup])

  return (
    <nav aria-label="Research sections">
      <NavLink
        to="/"
        end
        className={({ isActive }) =>
          `mb-2 flex items-center gap-3 px-3 py-2 text-sm font-semibold transition ${
            isActive
              ? 'bg-petroleum text-white'
              : 'text-stone-700 hover:bg-stone-200/70 dark:text-stone-300 dark:hover:bg-stone-800'
          }`
        }
      >
        <Home size={17} aria-hidden="true" />
        Home
      </NavLink>

      <div className="space-y-1">
        {groups.map((group) => {
          const open = expanded === group.id
          const containsCurrentPage = currentGroup === group.id
          const GroupIcon = group.icon
          return (
            <section key={group.id}>
              <button
                type="button"
                aria-expanded={open}
                aria-controls={`navigation-${group.id}`}
                onClick={() => setExpanded(open ? null : group.id)}
                className={`flex w-full items-center gap-3 px-3 py-2 text-left text-sm font-semibold transition hover:bg-stone-200/70 dark:hover:bg-stone-800 ${
                  containsCurrentPage ? 'text-petroleum dark:text-emerald-300' : 'text-stone-700 dark:text-stone-300'
                }`}
              >
                <GroupIcon size={17} aria-hidden="true" />
                <span className="min-w-0 flex-1">{group.label}</span>
                <ChevronDown size={16} aria-hidden="true" className={`transition-transform ${open ? 'rotate-180' : ''}`} />
              </button>
              {open && (
                <div id={`navigation-${group.id}`} className="mb-2 ml-5 border-l border-stone-300 pl-2 dark:border-stone-700">
                  {group.items.map(({ to, label, icon: Icon }) => (
                    <NavLink
                      key={to}
                      to={to}
                      end
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-3 py-2 text-sm transition ${
                          isActive
                            ? 'bg-petroleum font-semibold text-white'
                            : 'text-stone-600 hover:bg-stone-200/70 hover:text-ink dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-white'
                        }`
                      }
                    >
                      <Icon size={15} aria-hidden="true" />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </section>
          )
        })}
      </div>
    </nav>
  )
}
