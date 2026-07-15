import { Database } from 'lucide-react'
import type { ReactNode } from 'react'

export function SourceNote({ children }: { children: ReactNode }) {
  return (
    <figcaption className="mt-3 flex items-start gap-2 text-xs leading-5 text-stone-500 dark:text-stone-500">
      <Database className="mt-0.5 shrink-0" size={13} aria-hidden="true" />
      <span>{children}</span>
    </figcaption>
  )
}
