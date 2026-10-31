import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ChevronDown,
  Cpu,
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
      { to: '/global/food-prices', label: 'Food commodity prices', icon: House },
      { to: '/global/housing', label: 'Global housing prices', icon: House },
      { to: '/global/food-security', label: 'Food security', icon: House },
      { to: '/global/nutrition', label: 'Nutrition outcomes', icon: Activity },
      { to: '/global/human-impact', label: 'Human impact', icon: Activity },
      { to: '/global/demography', label: 'Demography', icon: Map },
    ],
  },
  {
    id: 'core-model',
    label: 'Core model',
    icon: Route,
    items: [
      { to: '/overview', label: 'System overview', icon: Network },
      { to: '/liquidity', label: 'Global liquidity', icon: TrendingUp },
      { to: '/physical-market', label: 'Physical oil market', icon: Droplets },
      { to: '/oil-prices', label: 'Oil prices', icon: Fuel },
      { to: '/equities', label: 'Equities', icon: Landmark },
      { to: '/energy-burden', label: 'Energy burden', icon: Scale },
      { to: '/economy', label: 'Energy and GDP', icon: Factory },
      { to: '/labour', label: 'Labour', icon: BriefcaseBusiness },
      { to: '/system-response', label: 'System response', icon: Route },
    ],
  },
  {
    id: 'canada',
    label: 'Canada',
    icon: Map,
    items: [
      { to: '/canada', label: 'Overview', icon: Map },
      { to: '/canada/current-state', label: 'Current state', icon: Activity },
      { to: '/affordability', label: 'Affordability overview', icon: House },
      { to: '/canada/food', label: 'Food affordability', icon: House },
      { to: '/canada/housing', label: 'Housing affordability', icon: House },
      { to: '/canada/energy', label: 'Canadian energy', icon: Droplets },
      { to: '/canada/economy', label: 'Canadian economy', icon: Factory },
      { to: '/canada/labour', label: 'Canadian labour', icon: BriefcaseBusiness },
      { to: '/canada/households', label: 'Canadian households', icon: Home },
      { to: '/canada/regimes', label: 'Regimes', icon: BarChart3 },
      { to: '/canada/symptoms', label: 'Symptoms', icon: AlertTriangle },
      { to: '/canada/ontario', label: 'Ontario context', icon: MapPin },
      { to: '/compare/canada-us', label: 'Canada–U.S. comparison', icon: Scale },
    ],
  },
  {
    id: 'technology',
    label: 'AI and technology flows',
    icon: Cpu,
    items: [
      { to: '/technology-flows', label: 'Technology flows', icon: Cpu },
    ],
  },
  {
    id: 'owen-sound',
    label: 'Owen Sound',
    icon: MapPin,
    items: [
      { to: '/owen-sound/affordability', label: 'Owen Sound overview', icon: MapPin },
      { to: '/owen-sound/food', label: 'Owen Sound food', icon: MapPin },
      { to: '/owen-sound/housing', label: 'Owen Sound housing', icon: MapPin },
    ],
  },
  {
    id: 'comparisons',
    label: 'Comparisons',
    icon: Scale,
    items: [
      { to: '/compare/food', label: 'Canada–U.S. food', icon: House },
      { to: '/compare/housing', label: 'Canada–U.S. housing', icon: House },
      { to: '/compare/canada-us', label: 'Canada–U.S. economy', icon: Scale },
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
      { to: '/output-quality', label: 'Output quality', icon: Scale },
      { to: '/indicators', label: 'Indicator catalogue', icon: ListFilter },
      { to: '/episodes', label: 'Historical episodes', icon: History },
      { to: '/methodology', label: 'Methodology', icon: BookOpen },
      { to: '/roadmap', label: 'Roadmap', icon: Map },
    ],
  },
]

export const navigationAliases = new Set(['/current-state', '/affordability/food', '/affordability/housing'])

export function getVisibleNavigationRoutes() {
  return new Set(groups.flatMap((group) => group.items.map((item) => item.to)))
}

const activeGroup = (pathname: string) => {
  const normalizedPath = pathname.replace(/\/$/, '') || '/'
  return groups.find((group) => group.items.some((item) => item.to === normalizedPath))?.id
}

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
