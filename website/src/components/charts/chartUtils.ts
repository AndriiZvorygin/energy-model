import type { ChartDataset, ChartObservation, ChartSeries, ChartState, Transformation } from './chartTypes'

const value = (row: ChartObservation, key: string) => typeof row[key] === 'number' && Number.isFinite(row[key]) ? row[key] as number : null

export type ReferenceStatistics = Record<string, { mean: number | null; standardDeviation: number | null; n: number }>

export function referenceStatistics(rows: ChartObservation[], series: ChartSeries[], start?: string | null, end?: string | null): ReferenceStatistics {
  const reference = rows.filter((row) => (!start || row.date >= start) && (!end || row.date <= end))
  return Object.fromEntries(series.map((item) => {
    const available = reference.map((row) => value(row, item.key)).filter((entry): entry is number => entry !== null)
    const mean = available.length ? available.reduce((sum, entry) => sum + entry, 0) / available.length : null
    const variance = mean === null ? null : available.reduce((sum, entry) => sum + (entry - mean) ** 2, 0) / available.length
    return [item.key, { mean, standardDeviation: variance === null ? null : Math.sqrt(variance), n: available.length }]
  }))
}

export function transformObservations(rows: ChartObservation[], series: ChartSeries[], transformation: Transformation, referenceRows = rows, fixedStatistics?: ReferenceStatistics): ChartObservation[] {
  if (transformation === 'raw') return rows.map((row) => ({ ...row }))
  const result = rows.map((row) => ({ date: row.date } as ChartObservation))
  const baseline = fixedStatistics ?? referenceStatistics(referenceRows, series)
  for (const item of series) {
    const values = rows.map((row) => value(row, item.key))
    const available = values.filter((item): item is number => item !== null)
    const mean = baseline[item.key]?.mean ?? null
    const std = baseline[item.key]?.standardDeviation ?? null
    const first = available[0] ?? null
    values.forEach((current, index) => {
      let transformed: number | null = null
      if (current !== null && transformation === 'zscore') transformed = std && mean !== null ? (current - mean) / std : null
      if (current !== null && transformation === 'indexed') transformed = first ? 100 * current / first : null
      const previousIndex = transformation === 'yoy' ? index - (item.frequency === 'quarterly' ? 4 : item.frequency === 'annual' ? 1 : 12) : index - 1
      const previous = previousIndex >= 0 ? values[previousIndex] : null
      if (current !== null && previous !== null && previous !== 0 && transformation === 'yoy') transformed = 100 * (current / previous - 1)
      if (current !== null && previous !== null && previous !== 0 && transformation === 'pct_change') transformed = 100 * (current / previous - 1)
      result[index][item.key] = transformed
      result[index][`__raw_${item.key}`] = current
      const sourceDate = rows[index][`__sourceDate_${item.key}`]
      if (typeof sourceDate === 'string') result[index][`__sourceDate_${item.key}`] = sourceDate
    })
  }
  return result
}

export function shiftSeries(rows: ChartObservation[], key: string, lag: number, outputKey = `${key}_shifted`): ChartObservation[] {
  return rows.map((row, index) => ({
    ...row,
    [outputKey]: index >= lag ? value(rows[index - lag], key) : null,
    [`__sourceDate_${outputKey}`]: index >= lag ? rows[index - lag].date : null,
  }))
}

export function rangeRows(rows: ChartObservation[], range: string, from?: string, to?: string): ChartObservation[] {
  if (!rows.length) return []
  if (range === 'custom') return rows.filter((row) => (!from || row.date >= from) && (!to || row.date <= to))
  if (range === 'all') return rows
  const years = Number(range.replace('y', ''))
  if (!Number.isFinite(years)) return rows
  const end = new Date(rows[rows.length - 1].date)
  const start = new Date(end)
  start.setUTCFullYear(start.getUTCFullYear() - years)
  return rows.filter((row) => new Date(row.date) >= start)
}

export function parseChartState(search: string, defaults: ChartState): ChartState {
  const params = new URLSearchParams(search)
  const series = params.get('series')?.split(',').filter(Boolean) ?? defaults.series
  const candidate = params.get('view') as Transformation | null
  const lagParam = params.get('lag')
  const lagValue = lagParam === null ? Number.NaN : Number(lagParam)
  return {
    series,
    transformation: candidate ?? defaults.transformation,
    range: params.get('range') ?? defaults.range,
    from: params.get('from') ?? defaults.from,
    to: params.get('to') ?? defaults.to,
    lag: Number.isFinite(lagValue) ? lagValue : defaults.lag,
  }
}

export function chartStateSearch(state: ChartState): string {
  const params = new URLSearchParams()
  if (state.series.length) params.set('series', state.series.join(','))
  params.set('view', state.transformation)
  params.set('range', state.range)
  if (state.from) params.set('from', state.from)
  if (state.to) params.set('to', state.to)
  if (state.lag !== undefined) params.set('lag', String(state.lag))
  return params.toString()
}

export function rowsToCsv(rows: ChartObservation[], series: ChartSeries[]): string {
  const escape = (input: unknown) => {
    const text = input === null || input === undefined ? '' : String(input)
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
  }
  const header = ['date', ...series.map((item) => `${item.label} (${item.unit})`)]
  return [header, ...rows.map((row) => [row.date, ...series.map((item) => row[item.key] ?? '')])].map((record) => record.map(escape).join(',')).join('\n')
}

export function validateDataset(dataset: ChartDataset): string[] {
  const errors: string[] = []
  if (!dataset.schemaVersion || !dataset.id || !dataset.title || !dataset.frequency) errors.push('Missing required dataset metadata')
  if (!dataset.plainLanguageSummary || !dataset.howToRead || !dataset.calculation?.formula) errors.push('Missing chart explanation metadata')
  if (!dataset.transformation || !('referenceStart' in dataset.transformation) || !('referenceEnd' in dataset.transformation)) errors.push('Missing transformation reference metadata')
  const keys = dataset.series.map((item) => item.key)
  if (new Set(keys).size !== keys.length) errors.push('Duplicate series keys')
  dataset.series.forEach((item) => {
    if (!item.unit) errors.push(`Missing unit for ${item.key}`)
    if (!item.source) errors.push(`Missing source for ${item.key}`)
  })
  const dates = dataset.observations.map((row) => row.date)
  if (dates.some((date, index) => index > 0 && date <= dates[index - 1])) errors.push('Dates must be strictly increasing and unique')
  return errors
}

export function correlation(rows: ChartObservation[], left: string, right: string): { correlation: number | null; n: number } {
  const pairs = rows.map((row) => [value(row, left), value(row, right)] as const).filter((pair): pair is readonly [number, number] => pair[0] !== null && pair[1] !== null)
  if (pairs.length < 3) return { correlation: null, n: pairs.length }
  const meanX = pairs.reduce((sum, pair) => sum + pair[0], 0) / pairs.length
  const meanY = pairs.reduce((sum, pair) => sum + pair[1], 0) / pairs.length
  const numerator = pairs.reduce((sum, pair) => sum + (pair[0] - meanX) * (pair[1] - meanY), 0)
  const denominator = Math.sqrt(pairs.reduce((sum, pair) => sum + (pair[0] - meanX) ** 2, 0) * pairs.reduce((sum, pair) => sum + (pair[1] - meanY) ** 2, 0))
  return { correlation: denominator ? numerator / denominator : null, n: pairs.length }
}
