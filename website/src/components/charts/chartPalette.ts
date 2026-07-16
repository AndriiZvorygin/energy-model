const palette = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
  'var(--chart-6)',
  'var(--chart-7)',
  'var(--chart-8)',
]

const semanticColors: Record<string, string> = {
  '#0f766e': palette[0],
  '#2563eb': palette[1],
  '#d97706': palette[2],
  '#be123c': palette[3],
  '#7c3aed': palette[4],
  '#475569': palette[5],
  '#64748b': palette[5],
  '#15803d': palette[6],
  '#a16207': palette[7],
}

export const chartColor = (source: string | null | undefined, index = 0) =>
  source ? (semanticColors[source.toLowerCase()] ?? source) : palette[index % palette.length]

export const chartPalette = palette
