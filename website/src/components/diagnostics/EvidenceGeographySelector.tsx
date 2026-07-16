import { Link, useLocation } from 'react-router-dom'
import { useGeneratedJson } from '../charts/useChartData'

type PresentationRoute = {
  route: string
  geography: string
  geographyLabel: string
  topic: string
  evidenceKey: string
}

type PresentationManifest = {
  routes: Record<string, PresentationRoute>
}

export function geographyOptions(manifest: PresentationManifest, pathname: string) {
  const normalizedPath = pathname.replace(/\/$/, '') || '/'
  const current = manifest.routes[normalizedPath]
  if (!current) return []

  const byGeography = new Map<string, PresentationRoute>()
  Object.values(manifest.routes)
    .filter((route) => route.topic === current.topic)
    .sort((left, right) => left.route.length - right.route.length)
    .forEach((route) => {
      if (!byGeography.has(route.geography)) byGeography.set(route.geography, route)
    })
  byGeography.set(current.geography, current)

  return [...byGeography.values()].sort((left, right) =>
    left.geographyLabel.localeCompare(right.geographyLabel),
  )
}

export function topicRoute(manifest: PresentationManifest, pathname: string, topic: string, fallback: string) {
  const normalizedPath = pathname.replace(/\/$/, '') || '/'
  const current = manifest.routes[normalizedPath]
  if (!current) return fallback
  return Object.values(manifest.routes).find(
    (route) => route.geography === current.geography && route.topic === topic,
  )?.route ?? fallback
}

export function useEvidenceTopicRoute(topic: string, fallback: string) {
  const location = useLocation()
  const { data } = useGeneratedJson<PresentationManifest>('presentation-manifest.json')
  return data ? topicRoute(data, location.pathname, topic, fallback) : fallback
}

export function EvidenceGeographySelector() {
  const location = useLocation()
  const { data } = useGeneratedJson<PresentationManifest>('presentation-manifest.json')
  const options = data ? geographyOptions(data, location.pathname) : []
  const normalizedPath = location.pathname.replace(/\/$/, '') || '/'

  if (options.length < 2) return null

  return (
    <nav aria-label="Evidence geography" className="mb-6 flex flex-wrap items-center gap-2">
      <span className="mr-1 text-xs font-semibold uppercase text-stone-500 dark:text-stone-400">
        Geography
      </span>
      {options.map((option) => {
        const active = option.route === normalizedPath
        return (
          <Link
            key={option.geography}
            to={option.route}
            aria-current={active ? 'page' : undefined}
            className={
              active
                ? 'border border-petroleum bg-petroleum px-3 py-1.5 text-sm font-semibold text-white'
                : 'border border-stone-300 bg-white px-3 py-1.5 text-sm font-semibold text-stone-700 hover:border-petroleum hover:text-petroleum dark:border-stone-600 dark:bg-[#18201d] dark:text-stone-200'
            }
          >
            {option.geographyLabel}
          </Link>
        )
      })}
    </nav>
  )
}
