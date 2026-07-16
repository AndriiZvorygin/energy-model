import { NavLink } from 'react-router-dom'

const choices = [
  ['/canada/current-state', 'Canada'],
  ['/canada/ontario', 'Ontario'],
  ['/current-state/us', 'United States comparison'],
  ['/liquidity', 'Global inputs'],
] as const

export function CanadaGeographyControls() {
  return <nav className="flex flex-wrap border-y border-stone-300 py-3 dark:border-stone-700" aria-label="Evidence geography">{choices.map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => `border-r border-stone-300 px-3 py-2 text-xs font-semibold last:border-r-0 dark:border-stone-700 ${isActive ? 'bg-petroleum text-white' : 'hover:bg-stone-100 dark:hover:bg-stone-800'}`}>{label}</NavLink>)}</nav>
}
