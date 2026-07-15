import { useEffect, useState } from 'react'
import type { ChartDataset, ChartEvent, ChartRegime } from './chartTypes'
import { validateDataset } from './chartUtils'

const base = import.meta.env.BASE_URL
const cache = new Map<string, unknown>()

async function loadJson<T>(file: string): Promise<T> {
  if (cache.has(file)) return cache.get(file) as T
  const response = await fetch(`${base}generated/${file}`)
  if (!response.ok) throw new Error(`Could not load chart data: ${file} (${response.status})`)
  const data = await response.json() as T
  cache.set(file, data)
  return data
}

export function useChartDataset(file: string) {
  const [dataset, setDataset] = useState<ChartDataset | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let active = true
    loadJson<ChartDataset>(file).then((data) => {
      const errors = validateDataset(data)
      if (errors.length) throw new Error(errors.join('; '))
      if (active) setDataset(data)
    }).catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : String(reason)))
    return () => { active = false }
  }, [file])
  return { dataset, error }
}

export function useChartContext() {
  const [events, setEvents] = useState<ChartEvent[]>([])
  const [regimes, setRegimes] = useState<ChartRegime[]>([])
  const [recessions, setRecessions] = useState<ChartRegime[]>([])
  useEffect(() => {
    void Promise.all([
      loadJson<{ events: ChartEvent[] }>('events.json'),
      loadJson<{ regimes: ChartRegime[]; recessions?: ChartRegime[] }>('regimes.json'),
    ]).then(([eventData, regimeData]) => {
      setEvents(eventData.events)
      setRegimes(regimeData.regimes)
      setRecessions(regimeData.recessions ?? [])
    })
  }, [])
  return { events, regimes, recessions }
}

export function useCrossLayerData(enabled: boolean) {
  const [observations, setObservations] = useState<Record<string, string | number | null>[]>([])
  useEffect(() => {
    if (!enabled) return
    void loadJson<{ observations: Record<string, string | number | null>[] }>('cross-layer.json').then((data) => setObservations(data.observations))
  }, [enabled])
  return observations
}
