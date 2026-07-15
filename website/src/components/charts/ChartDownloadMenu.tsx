import { Download, ExternalLink, Link as LinkIcon } from 'lucide-react'
import type { ChartDataset, ChartObservation, ChartSeries } from './chartTypes'
import { rowsToCsv } from './chartUtils'

function download(name: string, text: string) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' }))
  link.download = name
  link.click()
  URL.revokeObjectURL(link.href)
}

async function copy(text: string) {
  await navigator.clipboard.writeText(text)
}

export function ChartDownloadMenu({ dataset, displayedRows, visibleSeries }: { dataset: ChartDataset; displayedRows: ChartObservation[]; visibleSeries: ChartSeries[] }) {
  const base = import.meta.env.BASE_URL
  const sources = [...new Set(dataset.series.map((item) => item.source))].join('; ')
  const citation = `${dataset.title}. Energy Model research website. Data generated ${dataset.generatedAt}. Sources: ${sources}.`
  return <details className="relative"><summary className="flex h-9 cursor-pointer list-none items-center gap-2 border border-stone-300 px-3 text-xs font-semibold dark:border-stone-700"><Download size={14} />Download and cite</summary><div className="absolute right-0 z-20 mt-1 w-60 border border-stone-200 bg-white p-1 shadow-xl dark:border-stone-700 dark:bg-[#18201d]"><button type="button" className="block w-full px-3 py-2 text-left text-xs hover:bg-stone-100 dark:hover:bg-stone-800" onClick={() => download(`${dataset.id}-displayed.csv`, rowsToCsv(displayedRows, visibleSeries))}>Download displayed CSV</button><button type="button" className="block w-full px-3 py-2 text-left text-xs hover:bg-stone-100 dark:hover:bg-stone-800" onClick={() => download(`${dataset.id}-full.csv`, rowsToCsv(dataset.observations, dataset.series))}>Download full source CSV</button>{dataset.staticFigure && <a className="flex items-center gap-2 px-3 py-2 text-xs hover:bg-stone-100 dark:hover:bg-stone-800" href={`${base}charts/${dataset.staticFigure}`} target="_blank" rel="noreferrer"><ExternalLink size={13} />Open publication PNG</a>}<button type="button" className="block w-full px-3 py-2 text-left text-xs hover:bg-stone-100 dark:hover:bg-stone-800" onClick={() => void copy(citation)}>Copy chart citation</button><button type="button" className="block w-full px-3 py-2 text-left text-xs hover:bg-stone-100 dark:hover:bg-stone-800" onClick={() => void copy(sources)}>Copy source list</button><button type="button" className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-stone-100 dark:hover:bg-stone-800" onClick={() => void copy(window.location.href)}><LinkIcon size={13} />Copy shareable URL</button></div></details>
}
