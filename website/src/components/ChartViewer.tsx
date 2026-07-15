import { useState } from 'react'
import { Expand, X } from 'lucide-react'
import { SourceNote } from './SourceNote'

type ChartViewerProps = {
  src: string
  alt: string
  title: string
  description: string
  source: string
}

export function ChartViewer({ src, alt, title, description, source }: ChartViewerProps) {
  const [expanded, setExpanded] = useState(false)
  const resolvedSrc = src.startsWith('/') ? `${import.meta.env.BASE_URL}${src.slice(1)}` : src

  return (
    <figure className="border-y border-stone-200 py-6 dark:border-stone-800">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-ink dark:text-white">{title}</h3>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-stone-600 dark:text-stone-400">{description}</p>
        </div>
        <button
          type="button"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-stone-200 bg-white text-stone-600 transition hover:border-petroleum hover:text-petroleum dark:border-stone-700 dark:bg-stone-900 dark:text-stone-300"
          onClick={() => setExpanded(true)}
          title="Expand chart"
          aria-label={`Expand ${title}`}
        >
          <Expand size={17} />
        </button>
      </div>
      <button type="button" onClick={() => setExpanded(true)} className="block w-full cursor-zoom-in overflow-hidden bg-white dark:bg-stone-100" aria-label={`Open enlarged ${title}`}>
        <img src={resolvedSrc} alt={alt} className="h-auto w-full object-contain" loading="lazy" />
      </button>
      <SourceNote>{source}</SourceNote>

      {expanded && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-3 sm:p-8" role="dialog" aria-modal="true" aria-label={title} onClick={() => setExpanded(false)}>
          <button type="button" onClick={() => setExpanded(false)} className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-md bg-white text-stone-800" aria-label="Close chart">
            <X size={20} />
          </button>
          <img src={resolvedSrc} alt={alt} className="max-h-full max-w-full bg-white object-contain" onClick={(event) => event.stopPropagation()} />
        </div>
      )}
    </figure>
  )
}
