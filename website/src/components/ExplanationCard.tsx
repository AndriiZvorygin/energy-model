import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

type ExplanationCardProps = {
  title: string
  children: ReactNode
  icon?: LucideIcon
  eyebrow?: string
}

export function ExplanationCard({ title, children, icon: Icon, eyebrow }: ExplanationCardProps) {
  return (
    <article className="border-l-2 border-petroleum bg-white px-6 py-5 dark:bg-[#18201d]">
      <div className="flex items-start gap-3">
        {Icon && <Icon className="mt-0.5 shrink-0 text-petroleum" aria-hidden="true" size={20} />}
        <div>
          {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-petroleum">{eyebrow}</p>}
          <h3 className="text-lg font-semibold text-ink dark:text-white">{title}</h3>
          <div className="mt-2 text-sm leading-6 text-stone-600 dark:text-stone-300">{children}</div>
        </div>
      </div>
    </article>
  )
}
